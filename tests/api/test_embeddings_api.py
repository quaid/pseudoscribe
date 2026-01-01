"""Tests for embeddings API endpoints.

Issue: AI-010b - Embedding Cache & Multi-Model Support
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from pseudoscribe.api.app import app
from pseudoscribe.infrastructure.cached_vector_generator import CachedVectorGenerator


@pytest.fixture
def client():
    """Create test client with tenant header."""
    client = TestClient(app)
    # Add default tenant header for all requests
    client.headers = {"X-Tenant-ID": "test-tenant-123"}
    return client


@pytest.fixture
def mock_generator():
    """Create a mock CachedVectorGenerator."""
    generator = CachedVectorGenerator(
        model_name="BAAI/bge-small-en-v1.5",
        cache_size=100
    )
    return generator


class TestCacheStatsEndpoint:
    """Tests for /embeddings/cache/stats endpoint."""

    def test_get_cache_stats(self, client, mock_generator):
        """Test getting cache statistics."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.get("/embeddings/cache/stats")

            assert response.status_code == 200
            data = response.json()
            assert "size" in data
            assert "max_size" in data
            assert "hits" in data
            assert "misses" in data
            assert "hit_rate" in data
            assert "memory_bytes" in data


class TestCacheClearEndpoint:
    """Tests for /embeddings/cache/clear endpoint."""

    def test_clear_cache(self, client, mock_generator):
        """Test clearing the cache."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.post("/embeddings/cache/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cache_cleared"


class TestResetMetricsEndpoint:
    """Tests for /embeddings/cache/reset-metrics endpoint."""

    def test_reset_metrics(self, client, mock_generator):
        """Test resetting cache metrics."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.post("/embeddings/cache/reset-metrics")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "metrics_reset"


class TestModelsEndpoint:
    """Tests for /embeddings/models endpoints."""

    def test_get_supported_models(self, client, mock_generator):
        """Test getting supported models."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.get("/embeddings/models")

            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert "BAAI/bge-small-en-v1.5" in data["models"]
            assert "BAAI/bge-base-en-v1.5" in data["models"]
            assert "BAAI/bge-large-en-v1.5" in data["models"]

    def test_get_current_model(self, client, mock_generator):
        """Test getting current model."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.get("/embeddings/models/current")

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "BAAI/bge-small-en-v1.5"
            assert data["dimensions"] == 384

    def test_switch_model_valid(self, client, mock_generator):
        """Test switching to a valid model."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.post(
                "/embeddings/models/switch",
                json={"model": "BAAI/bge-large-en-v1.5"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "model_switched"
            assert data["model"] == "BAAI/bge-large-en-v1.5"
            assert data["dimensions"] == 1024

    def test_switch_model_invalid(self, client, mock_generator):
        """Test switching to an invalid model."""
        with patch(
            'pseudoscribe.api.embeddings.get_cached_generator',
            return_value=mock_generator
        ):
            response = client.post(
                "/embeddings/models/switch",
                json={"model": "invalid-model"}
            )

            assert response.status_code == 400
            assert "Unsupported model" in response.json()["detail"]
