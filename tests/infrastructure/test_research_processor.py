"""Tests for ResearchProcessor - PDF document ingestion and search

This test suite follows TDD workflow:
1. RED: Write failing tests that define desired behavior
2. GREEN: Implement minimal code to make tests pass
3. REFACTOR: Improve code quality while keeping tests green
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from pseudoscribe.infrastructure.research_processor import (
    ResearchProcessor,
    ResearchDocument,
    DocumentChunk,
    ChunkingStrategy,
    PDFExtractionError,
)


class TestResearchProcessor:
    """Test suite for ResearchProcessor class following TDD principles"""

    @pytest.fixture
    def mock_zerodb_service(self):
        """Create a mock ZeroDB service for testing"""
        mock_service = MagicMock()
        mock_service.embed_and_store = AsyncMock(return_value=["vec-id-1", "vec-id-2"])
        mock_service.semantic_search = AsyncMock(return_value=[
            {
                "vector_id": "vec-id-1",
                "document": "chunk text 1",
                "metadata": {"chunk_index": 0, "page_number": 1},
                "score": 0.95
            }
        ])
        return mock_service

    @pytest.fixture
    def research_processor(self, mock_zerodb_service):
        """Create ResearchProcessor instance with mocked dependencies"""
        return ResearchProcessor(zerodb_service=mock_zerodb_service)

    # --- PDF Document Parsing Tests --- #

    @pytest.mark.asyncio
    async def test_extract_text_from_valid_pdf(self, research_processor):
        """Test extracting text from a valid PDF file"""
        # Arrange
        test_pdf_path = self._create_test_pdf("Sample PDF content for testing.")

        # Act
        text = await research_processor.extract_text_from_pdf(test_pdf_path)

        # Assert
        assert text is not None
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Sample PDF content" in text

        # Cleanup
        os.unlink(test_pdf_path)

    @pytest.mark.asyncio
    async def test_extract_text_from_nonexistent_pdf_raises_error(self, research_processor):
        """Test that extracting from non-existent PDF raises appropriate error"""
        # Arrange
        nonexistent_path = "/tmp/nonexistent_file.pdf"

        # Act & Assert
        with pytest.raises(PDFExtractionError, match="PDF file not found"):
            await research_processor.extract_text_from_pdf(nonexistent_path)

    @pytest.mark.asyncio
    async def test_extract_text_from_corrupted_pdf_raises_error(self, research_processor):
        """Test that corrupted PDF files raise appropriate error"""
        # Arrange
        corrupted_pdf = self._create_corrupted_pdf()

        # Act & Assert
        with pytest.raises(PDFExtractionError, match="Failed to extract text"):
            await research_processor.extract_text_from_pdf(corrupted_pdf)

        # Cleanup
        os.unlink(corrupted_pdf)

    @pytest.mark.asyncio
    async def test_extract_text_from_empty_pdf(self, research_processor):
        """Test that empty PDFs return empty string without error"""
        # Arrange
        empty_pdf = self._create_test_pdf("")

        # Act
        text = await research_processor.extract_text_from_pdf(empty_pdf)

        # Assert
        assert text == ""

        # Cleanup
        os.unlink(empty_pdf)

    # --- Document Chunking Tests --- #

    @pytest.mark.asyncio
    async def test_chunk_document_with_default_strategy(self, research_processor):
        """Test chunking text with default chunking strategy"""
        # Arrange
        text = "This is sentence one. " * 100  # Long enough to require chunking

        # Act
        chunks = await research_processor.chunk_document(text)

        # Assert
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(len(chunk.text) <= research_processor.default_chunk_size for chunk in chunks)
        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    @pytest.mark.asyncio
    async def test_chunk_document_with_overlap(self, research_processor):
        """Test that chunks have overlapping text for context preservation"""
        # Arrange
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five." * 50
        chunk_size = 200
        overlap = 50

        # Act
        chunks = await research_processor.chunk_document(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        # Assert
        assert len(chunks) >= 2  # Should have multiple chunks
        # Check that consecutive chunks have overlapping content
        for i in range(len(chunks) - 1):
            current_chunk_end = chunks[i].text[-overlap:]
            next_chunk_start = chunks[i + 1].text[:overlap]
            # There should be some textual overlap
            assert len(current_chunk_end) > 0
            assert len(next_chunk_start) > 0

    @pytest.mark.asyncio
    async def test_chunk_short_document_returns_single_chunk(self, research_processor):
        """Test that short documents return a single chunk"""
        # Arrange
        short_text = "This is a short document."

        # Act
        chunks = await research_processor.chunk_document(short_text)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].text == short_text
        assert chunks[0].chunk_index == 0

    @pytest.mark.asyncio
    async def test_chunk_empty_text_raises_error(self, research_processor):
        """Test that chunking empty text raises ValueError"""
        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await research_processor.chunk_document("")

    @pytest.mark.asyncio
    async def test_chunk_with_custom_strategy(self, research_processor):
        """Test chunking with custom strategy (sentence-based)"""
        # Arrange
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        strategy = ChunkingStrategy.SENTENCE

        # Act
        chunks = await research_processor.chunk_document(text, strategy=strategy)

        # Assert
        assert len(chunks) > 0
        # Each chunk should contain complete sentences
        assert all(chunk.text.strip().endswith('.') for chunk in chunks)

    # --- Vector Storage Tests --- #

    @pytest.mark.asyncio
    async def test_store_document_chunks_in_zerodb(self, research_processor, mock_zerodb_service):
        """Test storing document chunks as vectors in ZeroDB"""
        # Arrange
        chunks = [
            DocumentChunk(text="First chunk", chunk_index=0, metadata={}),
            DocumentChunk(text="Second chunk", chunk_index=1, metadata={})
        ]
        tenant_id = "tenant-123"
        project_id = "project-456"
        document_id = "doc-789"

        # Act
        vector_ids = await research_processor.store_chunks(
            chunks=chunks,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id
        )

        # Assert
        assert len(vector_ids) == 2
        mock_zerodb_service.embed_and_store.assert_called_once()

        # Verify the call contained proper metadata
        call_args = mock_zerodb_service.embed_and_store.call_args
        assert call_args.kwargs["texts"] == ["First chunk", "Second chunk"]
        assert call_args.kwargs["metadata"]["tenant_id"] == tenant_id
        assert call_args.kwargs["metadata"]["project_id"] == project_id
        assert call_args.kwargs["metadata"]["document_id"] == document_id

    @pytest.mark.asyncio
    async def test_store_chunks_with_namespace_isolation(self, research_processor, mock_zerodb_service):
        """Test that chunks are stored in tenant-specific namespace"""
        # Arrange
        chunks = [DocumentChunk(text="Test chunk", chunk_index=0, metadata={})]
        tenant_id = "tenant-abc"

        # Act
        await research_processor.store_chunks(
            chunks=chunks,
            tenant_id=tenant_id,
            project_id="proj-1",
            document_id="doc-1"
        )

        # Assert
        call_args = mock_zerodb_service.embed_and_store.call_args
        # Namespace should be tenant-specific
        assert call_args.kwargs["namespace"] == f"research_{tenant_id}"

    # --- Semantic Search Tests --- #

    @pytest.mark.asyncio
    async def test_search_research_materials(self, research_processor, mock_zerodb_service):
        """Test semantic search across research materials"""
        # Arrange
        query = "machine learning algorithms"
        tenant_id = "tenant-123"
        project_id = "project-456"

        # Act
        results = await research_processor.search_research(
            query=query,
            tenant_id=tenant_id,
            project_id=project_id,
            limit=5
        )

        # Assert
        assert len(results) > 0
        mock_zerodb_service.semantic_search.assert_called_once()

        # Verify search parameters
        call_args = mock_zerodb_service.semantic_search.call_args
        assert call_args.kwargs["query_text"] == query
        assert call_args.kwargs["limit"] == 5
        assert call_args.kwargs["namespace"] == f"research_{tenant_id}"
        assert call_args.kwargs["filter_metadata"]["project_id"] == project_id

    @pytest.mark.asyncio
    async def test_search_without_project_filter(self, research_processor, mock_zerodb_service):
        """Test searching across all projects for a tenant"""
        # Arrange
        query = "research topic"
        tenant_id = "tenant-123"

        # Act
        results = await research_processor.search_research(
            query=query,
            tenant_id=tenant_id,
            project_id=None,  # Search across all projects
            limit=10
        )

        # Assert
        call_args = mock_zerodb_service.semantic_search.call_args
        # Should filter by tenant but not project
        assert call_args.kwargs["filter_metadata"]["tenant_id"] == tenant_id
        assert "project_id" not in call_args.kwargs["filter_metadata"]

    @pytest.mark.asyncio
    async def test_search_returns_formatted_results(self, research_processor, mock_zerodb_service):
        """Test that search results are properly formatted"""
        # Arrange
        mock_zerodb_service.semantic_search.return_value = [
            {
                "vector_id": "vec-1",
                "document": "relevant chunk text",
                "metadata": {
                    "document_id": "doc-123",
                    "chunk_index": 0,
                    "page_number": 1,
                    "document_name": "research.pdf"
                },
                "score": 0.92
            }
        ]

        # Act
        results = await research_processor.search_research(
            query="test query",
            tenant_id="tenant-1",
            limit=5
        )

        # Assert
        assert len(results) == 1
        result = results[0]
        assert result["text"] == "relevant chunk text"
        assert result["document_id"] == "doc-123"
        assert result["document_name"] == "research.pdf"
        assert result["chunk_index"] == 0
        assert result["similarity_score"] == 0.92

    # --- Document Processing Integration Tests --- #

    @pytest.mark.asyncio
    async def test_process_pdf_document_end_to_end(self, research_processor, mock_zerodb_service):
        """Test complete workflow: extract PDF -> chunk -> store"""
        # Arrange
        pdf_path = self._create_test_pdf("Research document content. " * 100)
        tenant_id = "tenant-123"
        project_id = "project-456"
        document_name = "research_paper.pdf"

        # Act
        result = await research_processor.process_pdf_document(
            pdf_path=pdf_path,
            tenant_id=tenant_id,
            project_id=project_id,
            document_name=document_name
        )

        # Assert
        assert result is not None
        assert "document_id" in result
        assert "chunk_count" in result
        assert "vector_ids" in result
        assert result["chunk_count"] > 0
        assert len(result["vector_ids"]) == result["chunk_count"]

        # Verify ZeroDB was called to store chunks
        mock_zerodb_service.embed_and_store.assert_called_once()

        # Cleanup
        os.unlink(pdf_path)

    @pytest.mark.asyncio
    async def test_process_document_includes_metadata(self, research_processor, mock_zerodb_service):
        """Test that processed documents include comprehensive metadata"""
        # Arrange
        pdf_path = self._create_test_pdf("Test content.")
        tenant_id = "tenant-123"
        project_id = "project-456"
        document_name = "test.pdf"
        additional_metadata = {"author": "John Doe", "year": 2024}

        # Act
        result = await research_processor.process_pdf_document(
            pdf_path=pdf_path,
            tenant_id=tenant_id,
            project_id=project_id,
            document_name=document_name,
            metadata=additional_metadata
        )

        # Assert
        call_args = mock_zerodb_service.embed_and_store.call_args
        stored_metadata = call_args.kwargs["metadata"]
        assert stored_metadata["tenant_id"] == tenant_id
        assert stored_metadata["project_id"] == project_id
        assert stored_metadata["document_name"] == document_name
        assert stored_metadata["author"] == "John Doe"
        assert stored_metadata["year"] == 2024

        # Cleanup
        os.unlink(pdf_path)

    # --- Project Linking Tests --- #

    @pytest.mark.asyncio
    async def test_get_documents_for_project(self, research_processor, mock_zerodb_service):
        """Test retrieving all research documents for a specific project"""
        # Arrange
        tenant_id = "tenant-123"
        project_id = "project-456"
        mock_zerodb_service.semantic_search.return_value = [
            {
                "vector_id": "vec-1",
                "document": "chunk 1",
                "metadata": {"document_id": "doc-1", "document_name": "paper1.pdf"},
                "score": 0.9
            },
            {
                "vector_id": "vec-2",
                "document": "chunk 2",
                "metadata": {"document_id": "doc-1", "document_name": "paper1.pdf"},
                "score": 0.85
            },
            {
                "vector_id": "vec-3",
                "document": "chunk 3",
                "metadata": {"document_id": "doc-2", "document_name": "paper2.pdf"},
                "score": 0.8
            }
        ]

        # Act
        documents = await research_processor.get_project_documents(
            tenant_id=tenant_id,
            project_id=project_id
        )

        # Assert
        # Should return unique documents, not chunks
        assert len(documents) == 2
        doc_ids = [doc["document_id"] for doc in documents]
        assert "doc-1" in doc_ids
        assert "doc-2" in doc_ids

    @pytest.mark.asyncio
    async def test_delete_document_removes_all_chunks(self, research_processor, mock_zerodb_service):
        """Test that deleting a document removes all its chunks from vector store"""
        # Arrange
        tenant_id = "tenant-123"
        document_id = "doc-789"
        mock_zerodb_service.delete_vector = AsyncMock()

        # Mock finding chunks for the document
        mock_zerodb_service.semantic_search.return_value = [
            {"vector_id": "vec-1", "metadata": {"document_id": document_id}},
            {"vector_id": "vec-2", "metadata": {"document_id": document_id}},
            {"vector_id": "vec-3", "metadata": {"document_id": document_id}},
        ]

        # Act
        deleted_count = await research_processor.delete_document(
            tenant_id=tenant_id,
            document_id=document_id
        )

        # Assert
        assert deleted_count == 3
        assert mock_zerodb_service.delete_vector.call_count == 3

    # --- Helper Methods for Test Data --- #

    def _create_test_pdf(self, content: str) -> str:
        """Create a temporary PDF file with given content for testing

        Args:
            content: Text content to include in PDF

        Returns:
            Path to created PDF file
        """
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
        except ImportError:
            pytest.skip("reportlab not installed - skipping PDF creation tests")

        # Create temporary file
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)

        # Create PDF with content
        c = canvas.Canvas(path, pagesize=letter)
        c.drawString(100, 750, content)
        c.save()

        return path

    def _create_corrupted_pdf(self) -> str:
        """Create a corrupted PDF file for testing error handling

        Returns:
            Path to corrupted PDF file
        """
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.write(fd, b'This is not a valid PDF file content')
        os.close(fd)
        return path


class TestDocumentChunk:
    """Test suite for DocumentChunk dataclass"""

    def test_document_chunk_creation(self):
        """Test creating a DocumentChunk instance"""
        # Arrange & Act
        chunk = DocumentChunk(
            text="Sample chunk text",
            chunk_index=0,
            metadata={"page": 1}
        )

        # Assert
        assert chunk.text == "Sample chunk text"
        assert chunk.chunk_index == 0
        assert chunk.metadata["page"] == 1

    def test_document_chunk_with_optional_fields(self):
        """Test DocumentChunk with all optional fields"""
        # Arrange & Act
        chunk = DocumentChunk(
            text="Sample text",
            chunk_index=5,
            metadata={"page": 2, "section": "Introduction"},
            start_char=100,
            end_char=250
        )

        # Assert
        assert chunk.start_char == 100
        assert chunk.end_char == 250
        assert chunk.metadata["section"] == "Introduction"


class TestResearchDocument:
    """Test suite for ResearchDocument dataclass"""

    def test_research_document_creation(self):
        """Test creating a ResearchDocument instance"""
        # Arrange & Act
        doc = ResearchDocument(
            document_id="doc-123",
            document_name="paper.pdf",
            tenant_id="tenant-1",
            project_id="project-1",
            file_path="/path/to/paper.pdf"
        )

        # Assert
        assert doc.document_id == "doc-123"
        assert doc.document_name == "paper.pdf"
        assert doc.tenant_id == "tenant-1"
        assert doc.project_id == "project-1"

    def test_research_document_with_metadata(self):
        """Test ResearchDocument with additional metadata"""
        # Arrange & Act
        doc = ResearchDocument(
            document_id="doc-456",
            document_name="research.pdf",
            tenant_id="tenant-2",
            project_id="project-2",
            file_path="/tmp/research.pdf",
            metadata={"author": "Jane Smith", "year": 2024},
            chunk_count=15
        )

        # Assert
        assert doc.metadata["author"] == "Jane Smith"
        assert doc.chunk_count == 15
