"""Knowledge Graph API endpoints

Provides REST API for interacting with the ZeroDB-backed knowledge graph,
including vault synchronization, semantic search, and reference suggestions.

Author: PseudoScribe Team
Date: 2025-12-30
"""

import logging
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Header
from pydantic import BaseModel, Field

from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph
from pseudoscribe.infrastructure.vault_sync import VaultSync

logger = logging.getLogger(__name__)


# Dependency to get tenant ID from header
def get_current_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> str:
    """Get tenant ID from header"""
    return x_tenant_id or "default"

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


# Request/Response Models

class SyncVaultRequest(BaseModel):
    """Request model for vault synchronization"""

    vault_path: str = Field(
        ...,
        description="Absolute path to the Obsidian vault directory"
    )
    namespace: Optional[str] = Field(
        None,
        description="Custom namespace for organizing vectors"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vault_path": "/home/user/Documents/my-vault",
                "namespace": "personal-notes"
            }
        }


class SyncVaultResponse(BaseModel):
    """Response model for vault synchronization"""

    status: str = Field(..., description="Sync status")
    added: List[str] = Field(..., description="List of added documents")
    modified: List[str] = Field(..., description="List of modified documents")
    deleted: List[str] = Field(..., description="List of deleted documents")
    total_documents: int = Field(..., description="Total documents in graph")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "added": ["notes/new-idea.md"],
                "modified": ["notes/updated-doc.md"],
                "deleted": [],
                "total_documents": 42
            }
        }


class RelatedDocument(BaseModel):
    """Model for related document results"""

    doc_path: str = Field(..., description="Document path")
    title: str = Field(..., description="Document title")
    score: float = Field(..., description="Similarity score (0.0-1.0)")
    links: List[str] = Field(..., description="Outgoing links from document")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_path": "notes/machine-learning.md",
                "title": "Machine Learning Basics",
                "score": 0.92,
                "links": ["Neural Networks", "Data Science"]
            }
        }


class FindRelatedResponse(BaseModel):
    """Response model for finding related documents"""

    query: str = Field(..., description="Search query")
    results: List[RelatedDocument] = Field(..., description="Related documents")
    count: int = Field(..., description="Number of results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "deep learning techniques",
                "results": [],
                "count": 0
            }
        }


class SuggestReferencesRequest(BaseModel):
    """Request model for reference suggestions"""

    content: str = Field(
        ...,
        description="Document content to find references for"
    )
    current_doc_path: Optional[str] = Field(
        None,
        description="Path of current document (to exclude from results)"
    )
    limit: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of suggestions"
    )
    threshold: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# My Note\n\nWriting about neural networks and deep learning.",
                "current_doc_path": "notes/my-note.md",
                "limit": 5,
                "threshold": 0.75
            }
        }


class SuggestReferencesResponse(BaseModel):
    """Response model for reference suggestions"""

    suggestions: List[RelatedDocument] = Field(
        ...,
        description="Suggested references"
    )
    count: int = Field(..., description="Number of suggestions")

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [],
                "count": 0
            }
        }


# API Endpoints

@router.post("/sync", response_model=SyncVaultResponse)
async def sync_vault(
    request: SyncVaultRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Sync Obsidian vault to knowledge graph

    Scans the specified vault for markdown files, extracts links and
    relationships, generates embeddings, and stores everything in ZeroDB.

    - **vault_path**: Path to the Obsidian vault directory
    - **namespace**: Optional namespace for organization (defaults to kg-{tenant_id})

    Returns the sync status and lists of added/modified/deleted documents.
    """
    logger.info(
        f"Syncing vault for tenant={tenant_id}, path={request.vault_path}"
    )

    try:
        # Validate vault path
        vault_path = Path(request.vault_path)
        if not vault_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Vault path does not exist: {request.vault_path}"
            )

        if not vault_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Vault path is not a directory: {request.vault_path}"
            )

        # Initialize vault sync and knowledge graph
        vault = VaultSync(vault_path=str(vault_path))
        kg = KnowledgeGraph(
            tenant_id=tenant_id,
            namespace=request.namespace
        )

        # Sync changes
        changes = await kg.sync_vault_changes(vault)

        # Calculate total documents
        total_docs = len(changes["added"]) + len(changes["modified"])

        logger.info(
            f"Vault sync complete for tenant={tenant_id}: "
            f"{total_docs} total documents"
        )

        return SyncVaultResponse(
            status="success",
            added=changes["added"],
            modified=changes["modified"],
            deleted=changes["deleted"],
            total_documents=total_docs
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing vault: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync vault: {str(e)}"
        )


@router.get("/related", response_model=FindRelatedResponse)
async def find_related_documents(
    query: str = Query(
        ...,
        description="Search query text",
        min_length=1
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of results"
    ),
    threshold: float = Query(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    ),
    namespace: Optional[str] = Query(
        None,
        description="Custom namespace to search in"
    ),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Find semantically related documents

    Searches the knowledge graph for documents semantically similar
    to the provided query text.

    - **query**: Text to search for
    - **limit**: Maximum number of results (1-50)
    - **threshold**: Minimum similarity score (0.0-1.0)
    - **namespace**: Optional namespace filter

    Returns a list of related documents with similarity scores.
    """
    logger.info(
        f"Finding related documents for tenant={tenant_id}, "
        f"query='{query[:50]}...'"
    )

    try:
        # Initialize knowledge graph
        kg = KnowledgeGraph(tenant_id=tenant_id, namespace=namespace)

        # Search for related documents
        results = await kg.find_related(
            query_text=query,
            limit=limit,
            threshold=threshold
        )

        # Format response
        related_docs = [
            RelatedDocument(
                doc_path=r["doc_path"],
                title=r["title"],
                score=r["score"],
                links=r["links"]
            )
            for r in results
        ]

        logger.info(f"Found {len(related_docs)} related documents")

        return FindRelatedResponse(
            query=query,
            results=related_docs,
            count=len(related_docs)
        )

    except Exception as e:
        logger.error(f"Error finding related documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find related documents: {str(e)}"
        )


@router.post("/suggest", response_model=SuggestReferencesResponse)
async def suggest_cross_references(
    request: SuggestReferencesRequest = Body(...),
    namespace: Optional[str] = Query(
        None,
        description="Custom namespace to search in"
    ),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Suggest cross-references for content

    Analyzes the provided content and suggests relevant documents
    from the knowledge graph that could be referenced.

    - **content**: Document content to analyze
    - **current_doc_path**: Current document path (excluded from results)
    - **limit**: Maximum number of suggestions (1-20)
    - **threshold**: Minimum similarity threshold (0.0-1.0)
    - **namespace**: Optional namespace filter

    Returns a list of suggested documents with relevance scores.
    """
    logger.info(
        f"Suggesting references for tenant={tenant_id}, "
        f"content_len={len(request.content)}"
    )

    try:
        # Initialize knowledge graph
        kg = KnowledgeGraph(tenant_id=tenant_id, namespace=namespace)

        # Get suggestions
        suggestions = await kg.suggest_references(
            content=request.content,
            current_doc_path=request.current_doc_path,
            limit=request.limit,
            threshold=request.threshold
        )

        # Format response
        suggested_docs = [
            RelatedDocument(
                doc_path=s["doc_path"],
                title=s["title"],
                score=s["score"],
                links=s["links"]
            )
            for s in suggestions
        ]

        logger.info(f"Generated {len(suggested_docs)} reference suggestions")

        return SuggestReferencesResponse(
            suggestions=suggested_docs,
            count=len(suggested_docs)
        )

    except Exception as e:
        logger.error(f"Error suggesting references: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest references: {str(e)}"
        )


@router.get("/health")
async def knowledge_graph_health(
    tenant_id: str = Depends(get_current_tenant_id)
):
    """Health check for knowledge graph functionality

    Returns the status of the knowledge graph service.
    """
    return {
        "status": "ok",
        "service": "knowledge_graph",
        "tenant_id": tenant_id
    }
