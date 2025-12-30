"""Research material integration API endpoints

Provides endpoints for uploading research documents (PDFs),
searching research materials, and managing document-project associations.
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel, Field

from pseudoscribe.api.dependencies import get_research_processor
from pseudoscribe.infrastructure.research_processor import ResearchProcessor

logger = logging.getLogger(__name__)

# --- Router --- #
router = APIRouter(prefix="/api/v1/research", tags=["research"])


# --- Pydantic Models --- #
class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str = Field(..., description="Unique document identifier")
    document_name: str = Field(..., description="Name of uploaded document")
    chunk_count: int = Field(..., description="Number of chunks created")
    tenant_id: str = Field(..., description="Tenant identifier")
    project_id: str = Field(..., description="Project identifier")
    message: str = Field(..., description="Success message")


class SearchRequest(BaseModel):
    """Request model for research search"""
    query: str = Field(..., min_length=1, description="Search query text")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")


class SearchResult(BaseModel):
    """Individual search result"""
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Document identifier")
    document_name: str = Field(..., description="Document name")
    chunk_index: int = Field(..., description="Chunk index in document")
    similarity_score: float = Field(..., description="Similarity score (0.0-1.0)")


class SearchResponse(BaseModel):
    """Response model for search results"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results returned")


class DocumentListResponse(BaseModel):
    """Response model for document listing"""
    documents: List[dict] = Field(..., description="List of documents")
    count: int = Field(..., description="Number of documents")
    project_id: str = Field(..., description="Project identifier")


class DeleteResponse(BaseModel):
    """Response model for document deletion"""
    document_id: str = Field(..., description="Deleted document ID")
    chunks_deleted: int = Field(..., description="Number of chunks deleted")
    message: str = Field(..., description="Success message")


# --- API Endpoints --- #
@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload research document"
)
async def upload_research_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    tenant_id: str = Query(..., description="Tenant identifier"),
    project_id: str = Query(..., description="Project identifier"),
    processor: ResearchProcessor = Depends(get_research_processor)
):
    """Upload a PDF research document for processing and indexing

    The document will be:
    1. Validated as a PDF file
    2. Text extracted from all pages
    3. Chunked into semantically meaningful segments
    4. Stored as vector embeddings for semantic search
    5. Associated with the specified project

    Args:
        file: PDF file upload (multipart/form-data)
        tenant_id: Tenant ID for multi-tenant isolation
        project_id: Project ID to associate document with
        processor: ResearchProcessor dependency injection

    Returns:
        DocumentUploadResponse with document_id and processing stats

    Raises:
        HTTPException 400: If file is not a PDF or processing fails
        HTTPException 500: If internal processing error occurs
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Create temporary file to store upload
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Write uploaded file to temporary location
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Process the PDF document
        result = await processor.process_pdf_document(
            pdf_path=tmp_file_path,
            tenant_id=tenant_id,
            project_id=project_id,
            document_name=file.filename,
            metadata={
                "file_size": len(content),
                "content_type": file.content_type
            }
        )

        # Clean up temporary file
        Path(tmp_file_path).unlink()

        logger.info(
            f"Successfully uploaded document {file.filename} "
            f"for tenant {tenant_id}, project {project_id}"
        )

        return DocumentUploadResponse(
            document_id=result["document_id"],
            document_name=result["document_name"],
            chunk_count=result["chunk_count"],
            tenant_id=result["tenant_id"],
            project_id=result["project_id"],
            message=f"Successfully processed {result['chunk_count']} chunks"
        )

    except Exception as e:
        # Clean up temporary file on error
        if 'tmp_file_path' in locals():
            try:
                Path(tmp_file_path).unlink()
            except Exception:
                pass

        logger.error(f"Failed to upload research document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search research materials"
)
async def search_research(
    request: SearchRequest,
    tenant_id: str = Query(..., description="Tenant identifier"),
    processor: ResearchProcessor = Depends(get_research_processor)
):
    """Search research materials using semantic similarity

    Performs semantic search across all research documents,
    optionally filtered by project. Returns relevant chunks
    ranked by similarity to the query.

    Args:
        request: SearchRequest with query and filters
        tenant_id: Tenant ID for isolation
        processor: ResearchProcessor dependency injection

    Returns:
        SearchResponse with ranked results

    Raises:
        HTTPException 500: If search fails
    """
    try:
        results = await processor.search_research(
            query=request.query,
            tenant_id=tenant_id,
            project_id=request.project_id,
            limit=request.limit,
            threshold=request.threshold
        )

        # Convert results to Pydantic models
        search_results = [
            SearchResult(
                text=r["text"],
                document_id=r["document_id"],
                document_name=r["document_name"],
                chunk_index=r["chunk_index"],
                similarity_score=r["similarity_score"]
            )
            for r in results
        ]

        logger.info(
            f"Search for '{request.query}' returned {len(search_results)} results"
        )

        return SearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results)
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/documents",
    response_model=DocumentListResponse,
    summary="List documents for project"
)
async def list_project_documents(
    project_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    processor: ResearchProcessor = Depends(get_research_processor)
):
    """List all research documents associated with a project

    Args:
        project_id: Project identifier
        tenant_id: Tenant identifier
        processor: ResearchProcessor dependency injection

    Returns:
        DocumentListResponse with list of documents

    Raises:
        HTTPException 500: If listing fails
    """
    try:
        documents = await processor.get_project_documents(
            tenant_id=tenant_id,
            project_id=project_id
        )

        logger.info(
            f"Retrieved {len(documents)} documents for project {project_id}"
        )

        return DocumentListResponse(
            documents=documents,
            count=len(documents),
            project_id=project_id
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete research document"
)
async def delete_research_document(
    document_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    processor: ResearchProcessor = Depends(get_research_processor)
):
    """Delete a research document and all its chunks

    Permanently removes the document and all associated
    vector embeddings from the system.

    Args:
        document_id: Document identifier to delete
        tenant_id: Tenant identifier
        processor: ResearchProcessor dependency injection

    Returns:
        DeleteResponse with deletion stats

    Raises:
        HTTPException 404: If document not found
        HTTPException 500: If deletion fails
    """
    try:
        chunks_deleted = await processor.delete_document(
            tenant_id=tenant_id,
            document_id=document_id
        )

        if chunks_deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        logger.info(
            f"Deleted document {document_id} ({chunks_deleted} chunks)"
        )

        return DeleteResponse(
            document_id=document_id,
            chunks_deleted=chunks_deleted,
            message=f"Successfully deleted document and {chunks_deleted} chunks"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
