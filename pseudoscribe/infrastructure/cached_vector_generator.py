"""Cached vector embedding generator with LRU cache and multi-model support.

This module provides the CachedVectorGenerator class that extends VectorGenerator
with caching capabilities for improved performance and multi-model support.

Issue: AI-010b - Embedding Cache & Multi-Model Support
"""

import numpy as np
from typing import List, Dict, Any, Optional, Callable
from collections import OrderedDict
import logging
import time

logger = logging.getLogger(__name__)


# Supported embedding models with their dimensions
SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
    "BAAI/bge-small-en-v1.5": {"dimensions": 384, "type": "text"},
    "BAAI/bge-base-en-v1.5": {"dimensions": 768, "type": "text"},
    "BAAI/bge-large-en-v1.5": {"dimensions": 1024, "type": "text"},
}


class CacheMetrics:
    """Tracks cache performance metrics."""

    def __init__(self):
        self.hits: int = 0
        self.misses: int = 0

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self.misses += 1

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            float: Hit rate between 0.0 and 1.0
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def reset(self) -> None:
        """Reset all metrics."""
        self.hits = 0
        self.misses = 0


class CachedVectorGenerator:
    """Vector embedding generator with LRU caching and multi-model support.

    This class provides efficient embedding generation by caching frequently
    used embeddings and supporting multiple embedding models with different
    dimensions.

    Attributes:
        model_name: Current embedding model name
        dimension: Expected embedding dimension for current model
        cache_size: Maximum number of embeddings to cache
        initialized: Whether the generator has been initialized
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        cache_size: int = 1000,
        mcp_func: Optional[Callable] = None
    ):
        """Initialize the cached vector generator.

        Args:
            model_name: Name of the embedding model to use.
                       Options: BAAI/bge-small-en-v1.5 (384-dim, default),
                               BAAI/bge-base-en-v1.5 (768-dim),
                               BAAI/bge-large-en-v1.5 (1024-dim)
            cache_size: Maximum number of embeddings to cache (default: 1000)
            mcp_func: Optional MCP function for dependency injection (for testing)
        """
        self.model_name = model_name
        self.dimension = self._get_model_dimension(model_name)
        self.cache_size = cache_size
        self.initialized = False
        self._mcp_func = mcp_func

        # LRU cache using OrderedDict
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._metrics = CacheMetrics()

        logger.info(
            f"CachedVectorGenerator initialized with model={model_name}, "
            f"cache_size={cache_size}"
        )

    def _get_model_dimension(self, model_name: str) -> int:
        """Get the embedding dimension for a given model.

        Args:
            model_name: Name of the embedding model

        Returns:
            int: Embedding dimension
        """
        if model_name in SUPPORTED_MODELS:
            return SUPPORTED_MODELS[model_name]["dimensions"]
        return 384  # Default dimension

    def _make_cache_key(self, text: str, model: str) -> str:
        """Create a cache key from text and model.

        Args:
            text: Input text
            model: Model name

        Returns:
            str: Cache key
        """
        return f"{model}:{hash(text)}"

    async def initialize(self) -> bool:
        """Initialize the vector generator.

        Returns:
            bool: True if initialization succeeded, False otherwise.
        """
        try:
            logger.info(f"Initializing cached vector generator with model: {self.model_name}")
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vector generator: {str(e)}")
            return False

    async def generate(self, text: str) -> np.ndarray:
        """Generate vector embeddings with caching.

        Args:
            text: Input text to vectorize

        Returns:
            np.ndarray: Embedding vector

        Raises:
            RuntimeError: If the generator is not initialized
            ValueError: If the input text is empty
        """
        if not self.initialized:
            raise RuntimeError("Vector generator not initialized")

        if not text or not text.strip():
            raise ValueError("Cannot generate embeddings for empty text")

        # Create cache key (model-specific)
        cache_key = self._make_cache_key(text, self.model_name)

        # Check cache
        if cache_key in self._cache:
            self._metrics.record_hit()
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            logger.debug(f"Cache hit for key: {cache_key[:50]}...")
            return self._cache[cache_key]

        # Cache miss - generate embedding
        self._metrics.record_miss()
        logger.debug(f"Cache miss for key: {cache_key[:50]}...")

        embedding = await self._generate_embedding(text)

        # Add to cache with LRU eviction
        self._add_to_cache(cache_key, embedding)

        return embedding

    def _add_to_cache(self, key: str, value: np.ndarray) -> None:
        """Add embedding to cache with LRU eviction.

        Args:
            key: Cache key
            value: Embedding to cache
        """
        # Evict LRU if at capacity
        if len(self._cache) >= self.cache_size:
            # Pop first item (least recently used)
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(f"Evicted LRU cache entry: {evicted_key[:50]}...")

        self._cache[key] = value

    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using MCP function.

        Args:
            text: Input text

        Returns:
            np.ndarray: Embedding vector

        Raises:
            RuntimeError: If embedding generation fails
        """
        try:
            logger.info(f"Generating embedding for text: {text[:50]}...")

            if self._mcp_func is None:
                raise RuntimeError(
                    "No MCP function available. "
                    "Ensure the ZeroDB MCP server is running or inject the function."
                )

            # Call MCP function
            response = await self._mcp_func(
                texts=[text],
                model=self.model_name
            )

            # Extract embedding
            if "embeddings" not in response or len(response["embeddings"]) == 0:
                raise RuntimeError("MCP returned empty embeddings")

            embedding = response["embeddings"][0]
            embedding_array = np.array(embedding, dtype=np.float32)

            # Validate dimension
            if embedding_array.shape[0] != self.dimension:
                raise RuntimeError(
                    f"Expected {self.dimension}-dimensional embedding, "
                    f"got {embedding_array.shape[0]}"
                )

            logger.info(f"Generated {self.dimension}-dimensional embedding")
            return embedding_array

        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def set_model(self, model_name: str) -> None:
        """Switch to a different embedding model.

        Args:
            model_name: Name of the model to switch to

        Note:
            Cache entries are model-specific, so switching models
            doesn't invalidate the cache but new embeddings will
            use the new model.
        """
        if model_name not in SUPPORTED_MODELS:
            logger.warning(f"Unknown model: {model_name}, using default dimensions")

        self.model_name = model_name
        self.dimension = self._get_model_dimension(model_name)
        logger.info(f"Switched to model: {model_name} (dim={self.dimension})")

    def get_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """Get supported embedding models.

        Returns:
            Dict mapping model names to their properties
        """
        return SUPPORTED_MODELS.copy()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict containing cache stats including size, hits, misses, hit_rate
        """
        cache_size = len(self._cache)

        # Estimate memory usage (embeddings are float32)
        if cache_size > 0:
            # Get dimension from first cached item
            sample = next(iter(self._cache.values()))
            memory_bytes = cache_size * sample.nbytes
        else:
            memory_bytes = 0

        return {
            "size": cache_size,
            "max_size": self.cache_size,
            "hits": self._metrics.hits,
            "misses": self._metrics.misses,
            "hit_rate": self._metrics.hit_rate,
            "memory_bytes": memory_bytes,
        }

    def clear_cache(self) -> None:
        """Clear all cached embeddings.

        Note: Metrics are preserved.
        """
        self._cache.clear()
        logger.info("Cache cleared")

    def reset_metrics(self) -> None:
        """Reset cache metrics.

        Note: Cache contents are preserved.
        """
        self._metrics.reset()
        logger.info("Cache metrics reset")
