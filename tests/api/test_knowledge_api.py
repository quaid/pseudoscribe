"""
Tests for Knowledge Graph API endpoints

Tests the REST API for vault synchronization, semantic search,
and cross-reference suggestions.
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from pseudoscribe.api.app import app


@pytest.fixture
def temp_vault():
    """Create temporary vault for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_kg_service():
    """Mock KnowledgeGraph service"""
    with patch('pseudoscribe.api.knowledge.KnowledgeGraph') as mock:
        mock_instance = MagicMock()
        mock_instance.sync_vault_changes = AsyncMock(return_value={
            "added": ["notes/new.md"],
            "modified": ["notes/updated.md"],
            "deleted": []
        })
        mock_instance.find_related = AsyncMock(return_value=[
            {
                "vector_id": "vec_1",
                "score": 0.92,
                "doc_path": "notes/ml.md",
                "title": "Machine Learning",
                "links": ["AI", "Data Science"]
            }
        ])
        mock_instance.suggest_references = AsyncMock(return_value=[
            {
                "vector_id": "vec_2",
                "score": 0.85,
                "doc_path": "notes/nn.md",
                "title": "Neural Networks",
                "links": ["Deep Learning"]
            }
        ])
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_vault_sync():
    """Mock VaultSync"""
    with patch('pseudoscribe.api.knowledge.VaultSync') as mock:
        yield mock


class TestSyncVaultEndpoint:
    """Test POST /api/v1/knowledge/sync"""

    @pytest.mark.asyncio
    async def test_sync_vault_success(self, temp_vault, mock_kg_service, mock_vault_sync):
        """
        Scenario: Successfully sync vault
        Given a valid vault path
        When posting to /sync
        Then vault is synced and results are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/sync",
                json={"vault_path": temp_vault},
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "added" in data
            assert "modified" in data
            assert "deleted" in data

    @pytest.mark.asyncio
    async def test_sync_vault_invalid_path(self):
        """
        Scenario: Handle invalid vault path
        Given a non-existent vault path
        When posting to /sync
        Then 400 error is returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/sync",
                json={"vault_path": "/nonexistent/path"},
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 400
            assert "does not exist" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_sync_vault_with_namespace(self, temp_vault, mock_kg_service, mock_vault_sync):
        """
        Scenario: Sync vault with custom namespace
        Given a custom namespace
        When posting to /sync
        Then namespace is used for organization
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/sync",
                json={
                    "vault_path": temp_vault,
                    "namespace": "custom-vault"
                },
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200


class TestFindRelatedEndpoint:
    """Test GET /api/v1/knowledge/related"""

    @pytest.mark.asyncio
    async def test_find_related_success(self, mock_kg_service):
        """
        Scenario: Find related documents
        Given a search query
        When getting /related
        Then related documents are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.get(
                "/api/v1/knowledge/related",
                params={"query": "machine learning"},
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "machine learning"
            assert len(data["results"]) > 0
            assert data["count"] == len(data["results"])

    @pytest.mark.asyncio
    async def test_find_related_with_limit(self, mock_kg_service):
        """
        Scenario: Limit number of results
        Given a limit parameter
        When getting /related
        Then limited results are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.get(
                "/api/v1/knowledge/related",
                params={"query": "test", "limit": 5},
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) <= 5

    @pytest.mark.asyncio
    async def test_find_related_with_threshold(self, mock_kg_service):
        """
        Scenario: Filter by similarity threshold
        Given a threshold parameter
        When getting /related
        Then only results above threshold are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.get(
                "/api/v1/knowledge/related",
                params={"query": "test", "threshold": 0.8},
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            for result in data["results"]:
                assert result["score"] >= 0.8

    @pytest.mark.asyncio
    async def test_find_related_missing_query(self):
        """
        Scenario: Handle missing query parameter
        Given no query parameter
        When getting /related
        Then 422 validation error is returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.get(
                "/api/v1/knowledge/related",
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 422


class TestSuggestReferencesEndpoint:
    """Test POST /api/v1/knowledge/suggest"""

    @pytest.mark.asyncio
    async def test_suggest_references_success(self, mock_kg_service):
        """
        Scenario: Get reference suggestions
        Given document content
        When posting to /suggest
        Then relevant references are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/suggest",
                json={
                    "content": "Writing about neural networks and deep learning."
                },
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data
            assert data["count"] == len(data["suggestions"])

    @pytest.mark.asyncio
    async def test_suggest_references_exclude_current(self, mock_kg_service):
        """
        Scenario: Exclude current document from suggestions
        Given current document path
        When posting to /suggest
        Then current document is excluded
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/suggest",
                json={
                    "content": "Test content",
                    "current_doc_path": "notes/current.md"
                },
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            for suggestion in data["suggestions"]:
                assert suggestion["doc_path"] != "notes/current.md"

    @pytest.mark.asyncio
    async def test_suggest_references_with_limit(self, mock_kg_service):
        """
        Scenario: Limit number of suggestions
        Given a limit parameter
        When posting to /suggest
        Then limited suggestions are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/suggest",
                json={
                    "content": "Test content",
                    "limit": 3
                },
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) <= 3

    @pytest.mark.asyncio
    async def test_suggest_references_with_threshold(self, mock_kg_service):
        """
        Scenario: Filter suggestions by threshold
        Given a threshold parameter
        When posting to /suggest
        Then only high-quality suggestions are returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.post(
                "/api/v1/knowledge/suggest",
                json={
                    "content": "Test content",
                    "threshold": 0.9
                },
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200


class TestHealthEndpoint:
    """Test GET /api/v1/knowledge/health"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """
        Scenario: Check knowledge graph health
        When getting /health
        Then status is returned
        """
        # Given
        async with AsyncClient(app=app, base_url="http://test") as client:
            # When
            response = await client.get(
                "/api/v1/knowledge/health",
                headers={"X-Tenant-ID": "test-tenant"}
            )

            # Then
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "knowledge_graph"
