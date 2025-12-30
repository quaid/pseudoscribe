"""API tests for research material integration endpoints

Tests the FastAPI endpoints for uploading, searching, and managing
research documents following TDD principles.
"""

import pytest
import tempfile
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from pseudoscribe.api.app import app
from pseudoscribe.api.dependencies import get_research_processor
from pseudoscribe.infrastructure.research_processor import ResearchProcessor


@pytest.fixture
def mock_research_processor():
    """Create a mock ResearchProcessor for testing"""
    processor = MagicMock(spec=ResearchProcessor)

    # Mock process_pdf_document
    processor.process_pdf_document = AsyncMock(return_value={
        "document_id": "doc-123",
        "document_name": "test.pdf",
        "chunk_count": 5,
        "vector_ids": ["vec-1", "vec-2", "vec-3", "vec-4", "vec-5"],
        "tenant_id": "tenant-1",
        "project_id": "project-1"
    })

    # Mock search_research
    processor.search_research = AsyncMock(return_value=[
        {
            "text": "Sample research content about machine learning.",
            "document_id": "doc-123",
            "document_name": "ml_paper.pdf",
            "chunk_index": 0,
            "similarity_score": 0.95,
            "metadata": {}
        },
        {
            "text": "Additional research on neural networks.",
            "document_id": "doc-456",
            "document_name": "nn_paper.pdf",
            "chunk_index": 2,
            "similarity_score": 0.87,
            "metadata": {}
        }
    ])

    # Mock get_project_documents
    processor.get_project_documents = AsyncMock(return_value=[
        {
            "document_id": "doc-123",
            "document_name": "paper1.pdf",
            "created_at": "2024-01-01T00:00:00",
            "metadata": {}
        },
        {
            "document_id": "doc-456",
            "document_name": "paper2.pdf",
            "created_at": "2024-01-02T00:00:00",
            "metadata": {}
        }
    ])

    # Mock delete_document
    processor.delete_document = AsyncMock(return_value=5)

    return processor


@pytest.fixture
def client_with_research_mock(mock_research_processor):
    """Create test client with mocked research processor"""
    app.dependency_overrides[get_research_processor] = lambda: mock_research_processor

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client_with_research_mock(mock_research_processor):
    """Create async test client with mocked research processor"""
    app.dependency_overrides[get_research_processor] = lambda: mock_research_processor

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestResearchUploadEndpoint:
    """Test suite for POST /api/v1/research/upload endpoint"""

    @pytest.mark.asyncio
    async def test_upload_pdf_successfully(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test successful PDF upload and processing"""
        # Arrange
        pdf_content = self._create_mock_pdf_content()
        files = {"file": ("test.pdf", pdf_content, "application/pdf")}
        params = {
            "tenant_id": "tenant-1",
            "project_id": "project-1"
        }

        # Act
        response = await async_client_with_research_mock.post(
            "/api/v1/research/upload",
            files=files,
            params=params
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "doc-123"
        assert data["document_name"] == "test.pdf"
        assert data["chunk_count"] == 5
        assert data["tenant_id"] == "tenant-1"
        assert data["project_id"] == "project-1"
        assert "Successfully processed" in data["message"]

        # Verify processor was called
        mock_research_processor.process_pdf_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_non_pdf_file_returns_400(
        self,
        async_client_with_research_mock
    ):
        """Test that uploading non-PDF file returns 400 error"""
        # Arrange
        files = {"file": ("test.txt", b"text content", "text/plain")}
        params = {
            "tenant_id": "tenant-1",
            "project_id": "project-1"
        }

        # Act
        response = await async_client_with_research_mock.post(
            "/api/v1/research/upload",
            files=files,
            params=params
        )

        # Assert
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_with_missing_tenant_id_returns_422(
        self,
        async_client_with_research_mock
    ):
        """Test that missing tenant_id returns validation error"""
        # Arrange
        pdf_content = self._create_mock_pdf_content()
        files = {"file": ("test.pdf", pdf_content, "application/pdf")}
        params = {"project_id": "project-1"}  # Missing tenant_id

        # Act
        response = await async_client_with_research_mock.post(
            "/api/v1/research/upload",
            files=files,
            params=params
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def _create_mock_pdf_content(self) -> bytes:
        """Create mock PDF binary content for testing"""
        # Minimal valid PDF header
        return b"%PDF-1.4\n%mock content\n%%EOF"


class TestResearchSearchEndpoint:
    """Test suite for POST /api/v1/research/search endpoint"""

    @pytest.mark.asyncio
    async def test_search_research_successfully(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test successful research search"""
        # Arrange
        search_request = {
            "query": "machine learning algorithms",
            "limit": 10,
            "threshold": 0.7
        }
        params = {"tenant_id": "tenant-1"}

        # Act
        response = await async_client_with_research_mock.post(
            "/api/v1/research/search",
            json=search_request,
            params=params
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "machine learning algorithms"
        assert data["count"] == 2
        assert len(data["results"]) == 2

        # Check first result
        result = data["results"][0]
        assert result["text"] == "Sample research content about machine learning."
        assert result["document_id"] == "doc-123"
        assert result["similarity_score"] == 0.95

        # Verify processor was called
        mock_research_processor.search_research.assert_called_once_with(
            query="machine learning algorithms",
            tenant_id="tenant-1",
            project_id=None,
            limit=10,
            threshold=0.7
        )

    @pytest.mark.asyncio
    async def test_search_with_project_filter(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test search filtered by project_id"""
        # Arrange
        search_request = {
            "query": "neural networks",
            "project_id": "project-123",
            "limit": 5,
            "threshold": 0.8
        }
        params = {"tenant_id": "tenant-1"}

        # Act
        response = await async_client_with_research_mock.post(
            "/api/v1/research/search",
            json=search_request,
            params=params
        )

        # Assert
        assert response.status_code == 200

        # Verify processor was called with project filter
        mock_research_processor.search_research.assert_called_once_with(
            query="neural networks",
            tenant_id="tenant-1",
            project_id="project-123",
            limit=5,
            threshold=0.8
        )

    @pytest.mark.asyncio
    async def test_search_with_empty_query_returns_422(
        self,
        async_client_with_research_mock
    ):
        """Test that empty query returns validation error"""
        # Arrange
        search_request = {
            "query": "",  # Empty query
            "limit": 10
        }
        params = {"tenant_id": "tenant-1"}

        # Act
        response = await async_client_with_research_mock.post(
            "/api/v1/research/search",
            json=search_request,
            params=params
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestListProjectDocumentsEndpoint:
    """Test suite for GET /api/v1/research/projects/{project_id}/documents endpoint"""

    @pytest.mark.asyncio
    async def test_list_project_documents_successfully(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test successful listing of project documents"""
        # Arrange
        project_id = "project-123"
        params = {"tenant_id": "tenant-1"}

        # Act
        response = await async_client_with_research_mock.get(
            f"/api/v1/research/projects/{project_id}/documents",
            params=params
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["project_id"] == project_id
        assert len(data["documents"]) == 2
        assert data["documents"][0]["document_id"] == "doc-123"
        assert data["documents"][1]["document_id"] == "doc-456"

        # Verify processor was called
        mock_research_processor.get_project_documents.assert_called_once_with(
            tenant_id="tenant-1",
            project_id=project_id
        )

    @pytest.mark.asyncio
    async def test_list_documents_with_missing_tenant_returns_422(
        self,
        async_client_with_research_mock
    ):
        """Test that missing tenant_id returns validation error"""
        # Arrange
        project_id = "project-123"

        # Act
        response = await async_client_with_research_mock.get(
            f"/api/v1/research/projects/{project_id}/documents"
            # No tenant_id in params
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestDeleteDocumentEndpoint:
    """Test suite for DELETE /api/v1/research/documents/{document_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_document_successfully(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test successful document deletion"""
        # Arrange
        document_id = "doc-123"
        params = {"tenant_id": "tenant-1"}

        # Act
        response = await async_client_with_research_mock.delete(
            f"/api/v1/research/documents/{document_id}",
            params=params
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert data["chunks_deleted"] == 5
        assert "Successfully deleted" in data["message"]

        # Verify processor was called
        mock_research_processor.delete_document.assert_called_once_with(
            tenant_id="tenant-1",
            document_id=document_id
        )

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document_returns_404(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test that deleting non-existent document returns 404"""
        # Arrange
        mock_research_processor.delete_document.return_value = 0  # No chunks deleted
        document_id = "nonexistent-doc"
        params = {"tenant_id": "tenant-1"}

        # Act
        response = await async_client_with_research_mock.delete(
            f"/api/v1/research/documents/{document_id}",
            params=params
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestResearchAPIIntegration:
    """Integration tests for research API workflow"""

    @pytest.mark.asyncio
    async def test_full_workflow_upload_search_delete(
        self,
        async_client_with_research_mock,
        mock_research_processor
    ):
        """Test complete workflow: upload -> search -> delete"""
        tenant_id = "tenant-1"
        project_id = "project-1"

        # Step 1: Upload document
        pdf_content = b"%PDF-1.4\n%content\n%%EOF"
        files = {"file": ("research.pdf", pdf_content, "application/pdf")}
        upload_response = await async_client_with_research_mock.post(
            "/api/v1/research/upload",
            files=files,
            params={"tenant_id": tenant_id, "project_id": project_id}
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["document_id"]

        # Step 2: Search for content
        search_request = {
            "query": "machine learning",
            "project_id": project_id,
            "limit": 10
        }
        search_response = await async_client_with_research_mock.post(
            "/api/v1/research/search",
            json=search_request,
            params={"tenant_id": tenant_id}
        )
        assert search_response.status_code == 200
        assert search_response.json()["count"] > 0

        # Step 3: List project documents
        list_response = await async_client_with_research_mock.get(
            f"/api/v1/research/projects/{project_id}/documents",
            params={"tenant_id": tenant_id}
        )
        assert list_response.status_code == 200
        assert list_response.json()["count"] > 0

        # Step 4: Delete document
        delete_response = await async_client_with_research_mock.delete(
            f"/api/v1/research/documents/{document_id}",
            params={"tenant_id": tenant_id}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["chunks_deleted"] > 0
