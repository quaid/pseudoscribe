"""Tests for embedding cache and multi-model support.

Issue: AI-010b - Embedding Cache & Multi-Model Support

These tests verify:
- LRU cache for embeddings
- Cache hit/miss scenarios
- Cache eviction policy
- Cache metrics
- Multi-model support
- Performance SLAs (<100ms for cached embeddings)
"""

import pytest
import numpy as np
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List


# Test fixtures
@pytest.fixture
def mock_mcp_embeddings():
    """Create a mock MCP embeddings function."""
    async def mock_generate(texts: List[str], model: str = "BAAI/bge-small-en-v1.5") -> Dict[str, Any]:
        # Simulate network delay for uncached requests
        await asyncio.sleep(0.1)  # 100ms delay

        # Return embeddings based on model dimension
        dimensions = {
            "BAAI/bge-small-en-v1.5": 384,
            "BAAI/bge-base-en-v1.5": 768,
            "BAAI/bge-large-en-v1.5": 1024,
        }
        dim = dimensions.get(model, 384)

        # Generate deterministic embeddings based on text hash
        embeddings = []
        for text in texts:
            np.random.seed(hash(text) % 2**32)
            embeddings.append(np.random.randn(dim).tolist())

        return {"embeddings": embeddings}

    return mock_generate


@pytest.fixture
def cached_vector_generator(mock_mcp_embeddings):
    """Create a CachedVectorGenerator with mocked MCP function."""
    from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

    generator = CachedVectorGenerator(
        model_name="BAAI/bge-small-en-v1.5",
        cache_size=100,
        mcp_func=mock_mcp_embeddings
    )
    return generator


import asyncio


class TestEmbeddingCache:
    """Tests for embedding cache functionality."""

    @pytest.mark.asyncio
    async def test_cache_miss_calls_mcp(self, cached_vector_generator, mock_mcp_embeddings):
        """Test that cache miss calls the MCP function."""
        await cached_vector_generator.initialize()

        # First call should be a cache miss
        embedding = await cached_vector_generator.generate("Hello world")

        assert embedding is not None
        assert len(embedding) == 384  # Default model dimension

        # Check metrics
        stats = cached_vector_generator.get_cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_embedding(self, cached_vector_generator):
        """Test that repeated requests return cached embeddings."""
        await cached_vector_generator.initialize()

        text = "Test text for caching"

        # First call - cache miss
        embedding1 = await cached_vector_generator.generate(text)

        # Second call - should be cache hit
        embedding2 = await cached_vector_generator.generate(text)

        # Embeddings should be identical
        np.testing.assert_array_equal(embedding1, embedding2)

        # Check metrics
        stats = cached_vector_generator.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_cached_response_under_100ms(self, cached_vector_generator):
        """Test that cached embeddings are returned in <100ms."""
        await cached_vector_generator.initialize()

        text = "Performance test text"

        # First call to populate cache
        await cached_vector_generator.generate(text)

        # Measure cached response time
        start = time.perf_counter()
        await cached_vector_generator.generate(text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should be under 100ms for cached response
        assert elapsed_ms < 100, f"Cached response took {elapsed_ms:.2f}ms, expected <100ms"

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cached_vector_generator):
        """Test LRU eviction when cache is full."""
        # Create generator with small cache
        from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

        small_cache_generator = CachedVectorGenerator(
            model_name="BAAI/bge-small-en-v1.5",
            cache_size=3,
            mcp_func=cached_vector_generator._mcp_func
        )
        await small_cache_generator.initialize()

        # Fill cache with 3 items
        await small_cache_generator.generate("text1")
        await small_cache_generator.generate("text2")
        await small_cache_generator.generate("text3")

        stats = small_cache_generator.get_cache_stats()
        assert stats["size"] == 3

        # Add 4th item - should evict "text1" (LRU)
        await small_cache_generator.generate("text4")

        stats = small_cache_generator.get_cache_stats()
        assert stats["size"] == 3  # Still at max size

        # "text1" should no longer be in cache (cache miss)
        initial_misses = stats["misses"]
        await small_cache_generator.generate("text1")
        stats = small_cache_generator.get_cache_stats()
        assert stats["misses"] == initial_misses + 1

    @pytest.mark.asyncio
    async def test_lru_access_order_update(self, cached_vector_generator):
        """Test that accessing cached item updates LRU order."""
        from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

        small_cache_generator = CachedVectorGenerator(
            model_name="BAAI/bge-small-en-v1.5",
            cache_size=3,
            mcp_func=cached_vector_generator._mcp_func
        )
        await small_cache_generator.initialize()

        # Fill cache: text1, text2, text3
        await small_cache_generator.generate("text1")
        await small_cache_generator.generate("text2")
        await small_cache_generator.generate("text3")

        # Access text1 again - moves it to end of LRU order
        await small_cache_generator.generate("text1")

        # Add text4 - should evict text2 (now LRU)
        await small_cache_generator.generate("text4")

        # text1 should still be cached (cache hit)
        stats_before = small_cache_generator.get_cache_stats()
        await small_cache_generator.generate("text1")
        stats_after = small_cache_generator.get_cache_stats()

        assert stats_after["hits"] == stats_before["hits"] + 1

    @pytest.mark.asyncio
    async def test_cache_stats_accuracy(self, cached_vector_generator):
        """Test cache statistics are accurate."""
        await cached_vector_generator.initialize()

        # Initial stats
        stats = cached_vector_generator.get_cache_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # Generate some traffic
        await cached_vector_generator.generate("text1")  # miss
        await cached_vector_generator.generate("text2")  # miss
        await cached_vector_generator.generate("text1")  # hit
        await cached_vector_generator.generate("text1")  # hit
        await cached_vector_generator.generate("text3")  # miss

        stats = cached_vector_generator.get_cache_stats()
        assert stats["size"] == 3
        assert stats["hits"] == 2
        assert stats["misses"] == 3
        assert stats["hit_rate"] == 0.4  # 2 / 5 = 0.4

    @pytest.mark.asyncio
    async def test_cache_clear(self, cached_vector_generator):
        """Test cache can be cleared."""
        await cached_vector_generator.initialize()

        # Populate cache
        await cached_vector_generator.generate("text1")
        await cached_vector_generator.generate("text2")

        stats = cached_vector_generator.get_cache_stats()
        assert stats["size"] == 2

        # Clear cache
        cached_vector_generator.clear_cache()

        stats = cached_vector_generator.get_cache_stats()
        assert stats["size"] == 0
        # Metrics should be preserved
        assert stats["misses"] == 2


class TestMultiModelSupport:
    """Tests for multi-model embedding support."""

    @pytest.mark.asyncio
    async def test_default_model(self, cached_vector_generator):
        """Test default model produces correct dimensions."""
        await cached_vector_generator.initialize()

        embedding = await cached_vector_generator.generate("test text")

        assert len(embedding) == 384  # BAAI/bge-small-en-v1.5

    @pytest.mark.asyncio
    async def test_base_model_768_dimensions(self, mock_mcp_embeddings):
        """Test base model produces 768 dimensions."""
        from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

        generator = CachedVectorGenerator(
            model_name="BAAI/bge-base-en-v1.5",
            mcp_func=mock_mcp_embeddings
        )
        await generator.initialize()

        embedding = await generator.generate("test text")

        assert len(embedding) == 768

    @pytest.mark.asyncio
    async def test_large_model_1024_dimensions(self, mock_mcp_embeddings):
        """Test large model produces 1024 dimensions."""
        from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

        generator = CachedVectorGenerator(
            model_name="BAAI/bge-large-en-v1.5",
            mcp_func=mock_mcp_embeddings
        )
        await generator.initialize()

        embedding = await generator.generate("test text")

        assert len(embedding) == 1024

    @pytest.mark.asyncio
    async def test_model_switching(self, mock_mcp_embeddings):
        """Test switching between models at runtime."""
        from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

        generator = CachedVectorGenerator(
            model_name="BAAI/bge-small-en-v1.5",
            mcp_func=mock_mcp_embeddings
        )
        await generator.initialize()

        # Generate with default model
        embedding_small = await generator.generate("test text")
        assert len(embedding_small) == 384

        # Switch model
        generator.set_model("BAAI/bge-large-en-v1.5")
        embedding_large = await generator.generate("test text")
        assert len(embedding_large) == 1024

    @pytest.mark.asyncio
    async def test_cache_is_model_specific(self, mock_mcp_embeddings):
        """Test cache keys include model to avoid conflicts."""
        from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator

        generator = CachedVectorGenerator(
            model_name="BAAI/bge-small-en-v1.5",
            mcp_func=mock_mcp_embeddings
        )
        await generator.initialize()

        text = "same text different models"

        # Generate with small model
        embedding_small = await generator.generate(text)

        # Switch to large model
        generator.set_model("BAAI/bge-large-en-v1.5")
        embedding_large = await generator.generate(text)

        # Embeddings should be different (different dimensions)
        assert len(embedding_small) != len(embedding_large)

        # Both should be cache misses (model-specific cache keys)
        stats = generator.get_cache_stats()
        assert stats["misses"] == 2

    @pytest.mark.asyncio
    async def test_get_supported_models(self, cached_vector_generator):
        """Test listing supported models."""
        models = cached_vector_generator.get_supported_models()

        assert "BAAI/bge-small-en-v1.5" in models
        assert "BAAI/bge-base-en-v1.5" in models
        assert "BAAI/bge-large-en-v1.5" in models

        # Check dimensions are included
        assert models["BAAI/bge-small-en-v1.5"]["dimensions"] == 384
        assert models["BAAI/bge-base-en-v1.5"]["dimensions"] == 768
        assert models["BAAI/bge-large-en-v1.5"]["dimensions"] == 1024


class TestCacheMetrics:
    """Tests for cache metrics and monitoring."""

    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self, cached_vector_generator):
        """Test hit rate is calculated correctly."""
        await cached_vector_generator.initialize()

        # 2 misses, 3 hits = 60% hit rate
        await cached_vector_generator.generate("text1")  # miss
        await cached_vector_generator.generate("text2")  # miss
        await cached_vector_generator.generate("text1")  # hit
        await cached_vector_generator.generate("text1")  # hit
        await cached_vector_generator.generate("text2")  # hit

        stats = cached_vector_generator.get_cache_stats()
        assert stats["hit_rate"] == 0.6

    @pytest.mark.asyncio
    async def test_metrics_reset(self, cached_vector_generator):
        """Test metrics can be reset."""
        await cached_vector_generator.initialize()

        await cached_vector_generator.generate("text1")
        await cached_vector_generator.generate("text1")

        stats = cached_vector_generator.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Reset metrics
        cached_vector_generator.reset_metrics()

        stats = cached_vector_generator.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        # Cache should still have the data
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_cache_memory_estimate(self, cached_vector_generator):
        """Test cache provides memory usage estimate."""
        await cached_vector_generator.initialize()

        # Add some embeddings
        for i in range(10):
            await cached_vector_generator.generate(f"text{i}")

        stats = cached_vector_generator.get_cache_stats()

        assert "memory_bytes" in stats
        # 10 embeddings * 384 dims * 4 bytes (float32) = ~15KB
        assert stats["memory_bytes"] > 0
