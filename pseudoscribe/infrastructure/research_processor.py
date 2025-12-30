"""Research Material Processing for PseudoScribe

This module handles PDF document ingestion, text extraction, chunking,
and semantic search for research materials integrated with writing projects.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

from pseudoscribe.infrastructure.zerodb_service import ZeroDBService

logger = logging.getLogger(__name__)


# Custom Exceptions
class PDFExtractionError(Exception):
    """Exception raised when PDF text extraction fails"""
    pass


class ChunkingStrategy(Enum):
    """Strategies for chunking documents"""
    FIXED_SIZE = "fixed_size"  # Fixed character count with overlap
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata

    Attributes:
        text: The text content of the chunk
        chunk_index: Sequential index of this chunk in the document
        metadata: Additional metadata (page numbers, sections, etc.)
        start_char: Starting character position in original document
        end_char: Ending character position in original document
    """
    text: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_char: Optional[int] = None
    end_char: Optional[int] = None


@dataclass
class ResearchDocument:
    """Represents a research document in the system

    Attributes:
        document_id: Unique identifier for the document
        document_name: Name of the document file
        tenant_id: Tenant who owns this document
        project_id: Project this document is linked to
        file_path: Path to the original file
        metadata: Additional document metadata
        chunk_count: Number of chunks this document was split into
        created_at: Document creation timestamp
    """
    document_id: str
    document_name: str
    tenant_id: str
    project_id: str
    file_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


class ResearchProcessor:
    """Processes research materials for semantic search and integration

    This class handles:
    - PDF text extraction using pdfplumber
    - Document chunking with configurable strategies
    - Vector storage in ZeroDB with multi-tenant isolation
    - Semantic search across research materials
    - Project-document associations
    """

    def __init__(
        self,
        zerodb_service: Optional[ZeroDBService] = None,
        default_chunk_size: int = 1000,
        default_overlap: int = 200,
        embedding_model: str = "BAAI/bge-small-en-v1.5"
    ):
        """Initialize ResearchProcessor

        Args:
            zerodb_service: ZeroDB service instance (creates singleton if None)
            default_chunk_size: Default chunk size in characters
            default_overlap: Default overlap between chunks in characters
            embedding_model: Model to use for generating embeddings
        """
        self.zerodb_service = zerodb_service or ZeroDBService.get_instance()
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap
        self.embedding_model = embedding_model

    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content

        Raises:
            PDFExtractionError: If file doesn't exist or extraction fails
        """
        # Check if file exists
        path = Path(pdf_path)
        if not path.exists():
            raise PDFExtractionError(f"PDF file not found: {pdf_path}")

        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed")
            raise PDFExtractionError(
                "pdfplumber library is required for PDF processing. "
                "Install with: pip install pdfplumber"
            )

        try:
            text_content = []

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

            return "\n".join(text_content)

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise PDFExtractionError(f"Failed to extract text from PDF: {e}")

    async def chunk_document(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    ) -> List[DocumentChunk]:
        """Split document text into chunks for processing

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            strategy: Chunking strategy to use

        Returns:
            List of DocumentChunk objects

        Raises:
            ValueError: If text is empty
        """
        if not text or text.strip() == "":
            raise ValueError("Text cannot be empty")

        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap

        if strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, chunk_size, overlap)
        elif strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(text, chunk_size)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, chunk_size)
        else:
            raise ValueError(f"Unsupported chunking strategy: {strategy}")

    def _chunk_fixed_size(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[DocumentChunk]:
        """Chunk text using fixed size with overlap

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between consecutive chunks

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]

            chunk = DocumentChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                metadata={},
                start_char=start,
                end_char=end
            )
            chunks.append(chunk)

            chunk_index += 1
            # Move start position, accounting for overlap
            start = end - overlap if end < len(text) else end

        return chunks

    def _chunk_by_sentence(
        self,
        text: str,
        max_chunk_size: int
    ) -> List[DocumentChunk]:
        """Chunk text by sentences, respecting max chunk size

        Args:
            text: Text to chunk
            max_chunk_size: Maximum size of each chunk

        Returns:
            List of DocumentChunk objects
        """
        # Simple sentence splitting (can be enhanced with NLTK)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunk = DocumentChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    metadata={},
                    start_char=start_char,
                    end_char=start_char + len(chunk_text)
                )
                chunks.append(chunk)

                # Start new chunk
                chunk_index += 1
                start_char += len(chunk_text) + 1
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size

        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk = DocumentChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                metadata={},
                start_char=start_char,
                end_char=start_char + len(chunk_text)
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_paragraph(
        self,
        text: str,
        max_chunk_size: int
    ) -> List[DocumentChunk]:
        """Chunk text by paragraphs, respecting max chunk size

        Args:
            text: Text to chunk
            max_chunk_size: Maximum size of each chunk

        Returns:
            List of DocumentChunk objects
        """
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)

            if current_size + paragraph_size > max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunk = DocumentChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    metadata={},
                    start_char=start_char,
                    end_char=start_char + len(chunk_text)
                )
                chunks.append(chunk)

                # Start new chunk
                chunk_index += 1
                start_char += len(chunk_text) + 2
                current_chunk = []
                current_size = 0

            current_chunk.append(paragraph)
            current_size += paragraph_size

        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunk = DocumentChunk(
                text=chunk_text,
                chunk_index=chunk_index,
                metadata={},
                start_char=start_char,
                end_char=start_char + len(chunk_text)
            )
            chunks.append(chunk)

        return chunks

    async def store_chunks(
        self,
        chunks: List[DocumentChunk],
        tenant_id: str,
        project_id: str,
        document_id: str,
        document_name: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Store document chunks as vectors in ZeroDB

        Args:
            chunks: List of document chunks to store
            tenant_id: Tenant identifier for multi-tenant isolation
            project_id: Project identifier
            document_id: Unique document identifier
            document_name: Name of the source document
            additional_metadata: Additional metadata to attach to vectors

        Returns:
            List of vector IDs for stored chunks
        """
        if not chunks:
            return []

        # Prepare texts and metadata
        texts = [chunk.text for chunk in chunks]

        # Build comprehensive metadata
        metadata = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "document_id": document_id,
            "document_name": document_name or "unknown",
            "created_at": datetime.utcnow().isoformat(),
        }

        # Add additional metadata if provided
        if additional_metadata:
            metadata.update(additional_metadata)

        # Add chunk-specific metadata as separate fields would require
        # storing each chunk separately, but embed_and_store batches them
        # We'll enhance metadata with chunk indices
        metadata["total_chunks"] = len(chunks)

        # Use tenant-specific namespace for isolation
        namespace = f"research_{tenant_id}"

        try:
            # Store chunks in ZeroDB
            vector_ids = await self.zerodb_service.embed_and_store(
                texts=texts,
                namespace=namespace,
                metadata=metadata,
                model=self.embedding_model
            )

            logger.info(
                f"Stored {len(chunks)} chunks for document {document_id} "
                f"in project {project_id}"
            )

            return vector_ids

        except Exception as e:
            logger.error(f"Failed to store chunks in ZeroDB: {e}")
            raise

    async def search_research(
        self,
        query: str,
        tenant_id: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search research materials using semantic similarity

        Args:
            query: Search query text
            tenant_id: Tenant identifier for isolation
            project_id: Optional project ID to filter results
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of search results with text, metadata, and scores
        """
        # Build metadata filter
        filter_metadata = {"tenant_id": tenant_id}
        if project_id:
            filter_metadata["project_id"] = project_id

        # Use tenant-specific namespace
        namespace = f"research_{tenant_id}"

        try:
            # Perform semantic search
            results = await self.zerodb_service.semantic_search(
                query_text=query,
                limit=limit,
                namespace=namespace,
                threshold=threshold,
                model=self.embedding_model,
                filter_metadata=filter_metadata
            )

            # Format results for API response
            formatted_results = []
            for result in results:
                formatted_result = {
                    "text": result.get("document", ""),
                    "document_id": result.get("metadata", {}).get("document_id", ""),
                    "document_name": result.get("metadata", {}).get("document_name", ""),
                    "chunk_index": result.get("metadata", {}).get("chunk_index", 0),
                    "similarity_score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                }
                formatted_results.append(formatted_result)

            logger.info(
                f"Found {len(formatted_results)} research results for query: {query[:50]}"
            )

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search research materials: {e}")
            raise

    async def process_pdf_document(
        self,
        pdf_path: str,
        tenant_id: str,
        project_id: str,
        document_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process a PDF document end-to-end: extract, chunk, and store

        Args:
            pdf_path: Path to PDF file
            tenant_id: Tenant identifier
            project_id: Project identifier
            document_name: Name of the document
            metadata: Additional metadata to attach
            chunk_size: Override default chunk size
            overlap: Override default overlap

        Returns:
            Dictionary with processing results including document_id,
            chunk_count, and vector_ids
        """
        # Generate unique document ID
        document_id = str(uuid.uuid4())

        # Extract text from PDF
        text = await self.extract_text_from_pdf(pdf_path)

        # Chunk the document
        chunks = await self.chunk_document(
            text=text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        # Store chunks in ZeroDB
        vector_ids = await self.store_chunks(
            chunks=chunks,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id,
            document_name=document_name,
            additional_metadata=metadata
        )

        result = {
            "document_id": document_id,
            "document_name": document_name,
            "chunk_count": len(chunks),
            "vector_ids": vector_ids,
            "tenant_id": tenant_id,
            "project_id": project_id
        }

        logger.info(
            f"Successfully processed PDF document {document_name} "
            f"({len(chunks)} chunks, {len(vector_ids)} vectors)"
        )

        return result

    async def get_project_documents(
        self,
        tenant_id: str,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Get all unique research documents for a project

        Args:
            tenant_id: Tenant identifier
            project_id: Project identifier

        Returns:
            List of unique documents with metadata
        """
        # Search with empty query to get all documents
        # (this is a workaround; in production, consider a dedicated method)
        namespace = f"research_{tenant_id}"
        filter_metadata = {
            "tenant_id": tenant_id,
            "project_id": project_id
        }

        try:
            # Get all chunks for the project
            results = await self.zerodb_service.semantic_search(
                query_text="",  # Empty query to match all
                limit=1000,  # High limit to get all chunks
                namespace=namespace,
                threshold=0.0,  # Accept all results
                filter_metadata=filter_metadata
            )

            # Extract unique documents
            documents_dict = {}
            for result in results:
                metadata = result.get("metadata", {})
                doc_id = metadata.get("document_id")

                if doc_id and doc_id not in documents_dict:
                    documents_dict[doc_id] = {
                        "document_id": doc_id,
                        "document_name": metadata.get("document_name", ""),
                        "created_at": metadata.get("created_at", ""),
                        "metadata": metadata
                    }

            return list(documents_dict.values())

        except Exception as e:
            logger.error(f"Failed to get project documents: {e}")
            raise

    async def delete_document(
        self,
        tenant_id: str,
        document_id: str
    ) -> int:
        """Delete a research document and all its chunks

        Args:
            tenant_id: Tenant identifier
            document_id: Document identifier

        Returns:
            Number of chunks deleted
        """
        namespace = f"research_{tenant_id}"
        filter_metadata = {
            "tenant_id": tenant_id,
            "document_id": document_id
        }

        try:
            # Find all chunks for this document
            results = await self.zerodb_service.semantic_search(
                query_text="",
                limit=10000,  # High limit to get all chunks
                namespace=namespace,
                threshold=0.0,
                filter_metadata=filter_metadata
            )

            # Delete each chunk
            deleted_count = 0
            for result in results:
                vector_id = result.get("vector_id")
                if vector_id:
                    await self.zerodb_service.delete_vector(
                        vector_id=vector_id,
                        namespace=namespace
                    )
                    deleted_count += 1

            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
