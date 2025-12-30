"""Style Profile Management API Endpoints.

This module provides CRUD operations for persistent style profiles,
enabling users to save, retrieve, update, and search style profiles.

Author: PseudoScribe Team
Date: 2025-12-30
Issue: CMS-007
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import logging

from pseudoscribe.api.dependencies import get_style_profiler
from pseudoscribe.infrastructure.style_profiler import StyleProfiler

logger = logging.getLogger(__name__)

# Router for style profile endpoints
router = APIRouter(prefix="/style-profiles", tags=["style-profiles"])


# Pydantic Models
class StyleCharacteristics(BaseModel):
    """Style characteristics for a profile."""
    complexity: float = Field(..., ge=0.0, le=1.0, description="Complexity score (0-1)")
    formality: float = Field(..., ge=0.0, le=1.0, description="Formality score (0-1)")
    tone: float = Field(..., ge=0.0, le=1.0, description="Tone score (0-1)")
    readability: float = Field(..., ge=0.0, le=1.0, description="Readability score (0-1)")


class CreateStyleProfileRequest(BaseModel):
    """Request model for creating a style profile."""
    name: str = Field(..., min_length=1, max_length=200, description="Profile name")
    description: Optional[str] = Field(None, max_length=1000, description="Profile description")
    text_sample: str = Field(..., min_length=10, description="Sample text for style analysis")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class UpdateStyleProfileRequest(BaseModel):
    """Request model for updating a style profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated profile name")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    text_sample: Optional[str] = Field(None, min_length=10, description="Updated text sample")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class StyleProfileResponse(BaseModel):
    """Response model for a style profile."""
    id: str = Field(..., description="Profile ID")
    name: str = Field(..., description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")
    text_sample: Optional[str] = Field(None, description="Sample text")
    characteristics: StyleCharacteristics = Field(..., description="Style characteristics")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


class SimilarStyleResult(BaseModel):
    """Result model for similar style search."""
    id: str = Field(..., description="Profile ID")
    name: Optional[str] = Field(None, description="Profile name")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    document: Optional[str] = Field(None, description="Document text")


# API Endpoints

@router.post("/", response_model=StyleProfileResponse, status_code=201)
async def create_style_profile(
    request: CreateStyleProfileRequest,
    profiler: StyleProfiler = Depends(get_style_profiler)
):
    """
    Create a new style profile from sample text.

    This endpoint analyzes the provided text sample and creates a persistent
    style profile with extracted characteristics and vector embedding.

    Args:
        request: Profile creation request with name, description, and text sample
        profiler: Style profiler dependency

    Returns:
        Created style profile with ID and characteristics

    Raises:
        HTTPException: If profile creation fails
    """
    try:
        # Generate vector embedding for the text
        vector = await profiler.model_manager.generate_vectors(request.text_sample)

        # Create full style profile
        profile = profiler._create_style_profile(request.text_sample, vector)

        # Add user-provided fields
        profile["name"] = request.name
        profile["description"] = request.description or ""
        profile["metadata"] = request.metadata or {}

        # Store profile (uses persistence if available)
        profile_id = await profiler.store_profile(profile)

        # Retrieve to get full profile
        stored_profile = await profiler.retrieve_profile(profile_id)

        if not stored_profile:
            raise HTTPException(status_code=500, detail="Failed to retrieve created profile")

        return StyleProfileResponse(
            id=stored_profile["id"],
            name=stored_profile.get("name", ""),
            description=stored_profile.get("description"),
            text_sample=stored_profile.get("text_sample"),
            characteristics=stored_profile["characteristics"],
            metadata=stored_profile.get("metadata", {}),
            created_at=stored_profile.get("created_at", ""),
            updated_at=stored_profile.get("updated_at", "")
        )

    except Exception as e:
        logger.error(f"Failed to create style profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create style profile: {str(e)}")


@router.get("/{profile_id}", response_model=StyleProfileResponse)
async def get_style_profile(
    profile_id: str,
    profiler: StyleProfiler = Depends(get_style_profiler)
):
    """
    Retrieve a style profile by ID.

    Args:
        profile_id: The profile identifier
        profiler: Style profiler dependency

    Returns:
        Style profile with characteristics and metadata

    Raises:
        HTTPException: If profile not found
    """
    try:
        profile = await profiler.retrieve_profile(profile_id)

        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        return StyleProfileResponse(
            id=profile["id"],
            name=profile.get("name", ""),
            description=profile.get("description"),
            text_sample=profile.get("text_sample"),
            characteristics=profile["characteristics"],
            metadata=profile.get("metadata", {}),
            created_at=profile.get("created_at", ""),
            updated_at=profile.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profile: {str(e)}")


@router.post("/search/text", response_model=List[SimilarStyleResult])
async def search_similar_styles_by_text(
    query_text: str = Query(..., min_length=1, description="Text query for semantic search"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    profiler: StyleProfiler = Depends(get_style_profiler)
):
    """
    Search for similar style profiles using text query.

    This endpoint performs semantic search to find style profiles similar
    to the provided text query.

    Args:
        query_text: Text query for semantic search
        limit: Maximum number of results to return
        threshold: Minimum similarity threshold (0.0-1.0)
        profiler: Style profiler dependency

    Returns:
        List of similar style profiles with similarity scores

    Raises:
        HTTPException: If search fails or persistence not available
    """
    try:
        # Check if persistence is available
        if not profiler.style_persistence:
            raise HTTPException(
                status_code=503,
                detail="Style profile persistence not available"
            )

        results = await profiler.search_styles_by_text(
            query_text=query_text,
            limit=limit,
            threshold=threshold
        )

        return [
            SimilarStyleResult(
                id=result.get("id", ""),
                name=result.get("name"),
                score=result.get("score", 0.0),
                document=result.get("document")
            )
            for result in results
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search similar styles: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/vector", response_model=List[SimilarStyleResult])
async def search_similar_styles_by_vector(
    query_vector: List[float] = Query(..., description="Query vector for similarity search"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    profiler: StyleProfiler = Depends(get_style_profiler)
):
    """
    Search for similar style profiles using a vector embedding.

    This endpoint performs vector similarity search to find style profiles
    similar to the provided query vector.

    Args:
        query_vector: Query vector for similarity search
        limit: Maximum number of results to return
        threshold: Minimum similarity threshold (0.0-1.0)
        profiler: Style profiler dependency

    Returns:
        List of similar style profiles with similarity scores

    Raises:
        HTTPException: If search fails or persistence not available
    """
    try:
        # Check if persistence is available
        if not profiler.style_persistence:
            raise HTTPException(
                status_code=503,
                detail="Style profile persistence not available"
            )

        results = await profiler.find_similar_styles(
            query_vector=query_vector,
            limit=limit,
            threshold=threshold
        )

        return [
            SimilarStyleResult(
                id=result.get("id", ""),
                name=result.get("name"),
                score=result.get("score", 0.0),
                document=result.get("document")
            )
            for result in results
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search similar styles: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.delete("/{profile_id}", status_code=204)
async def delete_style_profile(
    profile_id: str,
    profiler: StyleProfiler = Depends(get_style_profiler)
):
    """
    Delete a style profile by ID.

    Args:
        profile_id: The profile identifier
        profiler: Style profiler dependency

    Raises:
        HTTPException: If deletion fails or persistence not available
    """
    try:
        # Check if persistence is available
        if not profiler.style_persistence:
            raise HTTPException(
                status_code=503,
                detail="Style profile persistence not available"
            )

        success = await profiler.style_persistence.delete_profile(profile_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")
