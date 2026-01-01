"""Embeddings API endpoints for PseudoScribe.

This module provides API endpoints for:
- Embedding generation
- Cache statistics and management
- Multi-model support

Issue: AI-010b - Embedding Cache & Multi-Model Support
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from pseudoscribe.infrastructure.cached_vector_generator import (
    CachedVectorGenerator,
    SUPPORTED_MODELS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


# Singleton instance of the cached generator
_cached_generator: Optional[CachedVectorGenerator] = None


def get_cached_generator() -> CachedVectorGenerator:
    """Get the singleton CachedVectorGenerator instance."""
    global _cached_generator
    if _cached_generator is None:
        _cached_generator = CachedVectorGenerator()
    return _cached_generator


# Request/Response Models

class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    text: str = Field(..., description="Text to generate embeddings for")
    model: Optional[str] = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Embedding model to use"
    )


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    embedding: List[float] = Field(..., description="Generated embedding vector")
    model: str = Field(..., description="Model used for generation")
    dimensions: int = Field(..., description="Embedding dimensions")
    cached: bool = Field(..., description="Whether result was from cache")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    size: int = Field(..., description="Current number of cached embeddings")
    max_size: int = Field(..., description="Maximum cache size")
    hits: int = Field(..., description="Total cache hits")
    misses: int = Field(..., description="Total cache misses")
    hit_rate: float = Field(..., description="Cache hit rate (0.0-1.0)")
    memory_bytes: int = Field(..., description="Estimated memory usage in bytes")


class SupportedModelsResponse(BaseModel):
    """Response model for supported models."""

    models: Dict[str, Dict[str, Any]] = Field(
        ..., description="Supported models with their properties"
    )


class ModelSwitchRequest(BaseModel):
    """Request model for switching embedding models."""

    model: str = Field(..., description="Model to switch to")


# Endpoints

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    generator: CachedVectorGenerator = Depends(get_cached_generator)
) -> CacheStatsResponse:
    """Get embedding cache statistics.

    Returns current cache size, hit/miss rates, and memory usage.
    """
    stats = generator.get_cache_stats()
    return CacheStatsResponse(**stats)


@router.post("/cache/clear")
async def clear_cache(
    generator: CachedVectorGenerator = Depends(get_cached_generator)
) -> Dict[str, str]:
    """Clear the embedding cache.

    Note: Cache metrics are preserved.
    """
    generator.clear_cache()
    return {"status": "cache_cleared"}


@router.post("/cache/reset-metrics")
async def reset_cache_metrics(
    generator: CachedVectorGenerator = Depends(get_cached_generator)
) -> Dict[str, str]:
    """Reset cache metrics.

    Note: Cache contents are preserved.
    """
    generator.reset_metrics()
    return {"status": "metrics_reset"}


@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models(
    generator: CachedVectorGenerator = Depends(get_cached_generator)
) -> SupportedModelsResponse:
    """Get list of supported embedding models."""
    models = generator.get_supported_models()
    return SupportedModelsResponse(models=models)


@router.post("/models/switch")
async def switch_model(
    request: ModelSwitchRequest,
    generator: CachedVectorGenerator = Depends(get_cached_generator)
) -> Dict[str, Any]:
    """Switch the active embedding model.

    Note: Existing cache entries are preserved but new embeddings
    will use the new model.
    """
    if request.model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model: {request.model}. "
            f"Supported models: {list(SUPPORTED_MODELS.keys())}"
        )

    generator.set_model(request.model)
    return {
        "status": "model_switched",
        "model": request.model,
        "dimensions": SUPPORTED_MODELS[request.model]["dimensions"]
    }


@router.get("/models/current")
async def get_current_model(
    generator: CachedVectorGenerator = Depends(get_cached_generator)
) -> Dict[str, Any]:
    """Get the currently active embedding model."""
    return {
        "model": generator.model_name,
        "dimensions": generator.dimension
    }
