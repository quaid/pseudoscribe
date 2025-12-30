"""Unit tests for ZeroDB-backed VectorStore

AI-012: Test persistent vector storage with ZeroDB integration.
This test suite verifies that vectors are stored persistently using ZeroDB
instead of in-memory Python dicts.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, call
from typing import Dict, List, Any

from pseudoscribe.infrastructure.vector_store import VectorStore


class TestVectorStoreInitialization:
    """Test VectorStore initialization and configuration"""

    def test_vector_store_initializes_without_errors(self):
        """AI-012: VectorStore should initialize successfully"""
        # Arrange & Act
        store = VectorStore()

        # Assert
        assert store is not None
        assert not store.initialized

    def test_initialize_sets_up_zerodb_connection(self):
        """AI-012: Initialize should configure ZeroDB connection"""
        # Arrange
        store = VectorStore()

        # Act
        result = store.initialize()

        # Assert
        assert result is True
        assert store.initialized is True


class TestVectorPersistence:
    """Test vector storage and retrieval using ZeroDB"""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance for testing"""
        store = VectorStore()
        store.initialize()
        return store

    @pytest.fixture
    def sample_vector_384(self):
        """Create a sample 384-dimensional vector"""
        return np.random.rand(384).astype(np.float32)

    @pytest.fixture
    def sample_vector_1024(self):
        """Create a sample 1024-dimensional vector"""
        return np.random.rand(1024).astype(np.float32)

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_add_vector_calls_zerodb_upsert(self, mock_mcp_client, vector_store, sample_vector_384):
        """AI-012: Adding a vector should call ZeroDB upsert, not store in memory"""
        # Arrange
        vector_id = "test_vector_1"
        document = "Test document content"
        metadata = {"tenant_id": "tenant_1", "type": "style_profile"}

        mock_mcp_client.upsert_vector = Mock(return_value={"success": True, "vector_id": vector_id})

        # Act
        result = vector_store.add_vector(
            id=vector_id,
            vector=sample_vector_384,
            document=document,
            metadata=metadata
        )

        # Assert
        assert result is True
        mock_mcp_client.upsert_vector.assert_called_once()

        # Verify the call arguments
        call_args = mock_mcp_client.upsert_vector.call_args
        assert call_args[1]['vector_id'] == vector_id
        assert call_args[1]['document'] == document
        assert call_args[1]['metadata'] == metadata
        np.testing.assert_array_almost_equal(
            call_args[1]['vector_embedding'],
            sample_vector_384.tolist()
        )

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_add_vector_supports_1024_dimensions(self, mock_mcp_client, vector_store, sample_vector_1024):
        """AI-012: Should support 1024-dimensional vectors (BAAI/bge-large)"""
        # Arrange
        vector_id = "test_vector_large"
        document = "Test document"

        mock_mcp_client.upsert_vector = Mock(return_value={"success": True, "vector_id": vector_id})

        # Act
        result = vector_store.add_vector(
            id=vector_id,
            vector=sample_vector_1024,
            document=document
        )

        # Assert
        assert result is True
        call_args = mock_mcp_client.upsert_vector.call_args
        assert len(call_args[1]['vector_embedding']) == 1024

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_get_vector_retrieves_from_zerodb(self, mock_mcp_client, vector_store):
        """AI-012: Getting a vector should retrieve from ZeroDB, not memory"""
        # Arrange
        vector_id = "test_vector_1"
        expected_vector = np.random.rand(384).tolist()

        mock_mcp_client.get_vector = Mock(return_value={
            "vector_id": vector_id,
            "vector_embedding": expected_vector,
            "document": "Test doc",
            "metadata": {}
        })

        # Act
        result = vector_store.get_vector(vector_id)

        # Assert
        assert result is not None
        np.testing.assert_array_almost_equal(result, np.array(expected_vector))
        mock_mcp_client.get_vector.assert_called_once_with(
            vector_id=vector_id,
            include_embedding=True,
            namespace="default"
        )

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_get_nonexistent_vector_returns_none(self, mock_mcp_client, vector_store):
        """AI-012: Getting a non-existent vector should return None"""
        # Arrange
        mock_mcp_client.get_vector = Mock(return_value=None)

        # Act
        result = vector_store.get_vector("nonexistent_id")

        # Assert
        assert result is None


class TestSemanticSearch:
    """Test similarity search using ZeroDB"""

    @pytest.fixture
    def vector_store(self):
        store = VectorStore()
        store.initialize()
        return store

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_find_similar_uses_zerodb_search(self, mock_mcp_client, vector_store):
        """AI-012: Similarity search should use ZeroDB search, not in-memory comparison"""
        # Arrange
        query_vector = np.random.rand(384)

        mock_mcp_client.search_vectors = Mock(return_value=[
            {"vector_id": "vec1", "score": 0.95, "document": "Doc 1"},
            {"vector_id": "vec2", "score": 0.87, "document": "Doc 2"},
            {"vector_id": "vec3", "score": 0.75, "document": "Doc 3"}
        ])

        # Act
        results = vector_store.find_similar(query_vector, top_k=3, threshold=0.7)

        # Assert
        assert len(results) == 3
        assert results[0]["id"] == "vec1"
        assert results[0]["score"] == 0.95

        mock_mcp_client.search_vectors.assert_called_once()
        call_args = mock_mcp_client.search_vectors.call_args
        np.testing.assert_array_almost_equal(
            call_args[1]['query_vector'],
            query_vector.tolist()
        )
        assert call_args[1]['limit'] == 3
        assert call_args[1]['threshold'] == 0.7

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_find_similar_respects_threshold(self, mock_mcp_client, vector_store):
        """AI-012: Similarity search should filter by threshold"""
        # Arrange
        query_vector = np.random.rand(384)
        threshold = 0.8

        mock_mcp_client.search_vectors = Mock(return_value=[
            {"vector_id": "vec1", "score": 0.95, "document": "Doc 1"},
            {"vector_id": "vec2", "score": 0.87, "document": "Doc 2"}
        ])

        # Act
        results = vector_store.find_similar(query_vector, top_k=5, threshold=threshold)

        # Assert
        assert all(r["score"] >= threshold for r in results)

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_find_similar_empty_results(self, mock_mcp_client, vector_store):
        """AI-012: Similarity search should handle empty results gracefully"""
        # Arrange
        query_vector = np.random.rand(384)
        mock_mcp_client.search_vectors = Mock(return_value=[])

        # Act
        results = vector_store.find_similar(query_vector, top_k=5)

        # Assert
        assert results == []


class TestNamespaceIsolation:
    """Test multi-tenant namespace isolation"""

    @pytest.fixture
    def vector_store(self):
        store = VectorStore()
        store.initialize()
        return store

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_add_vector_uses_namespace(self, mock_mcp_client, vector_store):
        """AI-012: Vectors should be stored in tenant-specific namespaces"""
        # Arrange
        tenant_id = "tenant_123"
        vector_id = "style_profile_1"
        vector = np.random.rand(384)
        document = "Test content"

        mock_mcp_client.upsert_vector = Mock(return_value={"success": True})

        # Act
        result = vector_store.add_vector(
            id=vector_id,
            vector=vector,
            document=document,
            namespace=f"tenant_{tenant_id}"
        )

        # Assert
        assert result is True
        call_args = mock_mcp_client.upsert_vector.call_args
        assert call_args[1]['namespace'] == f"tenant_{tenant_id}"

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_search_respects_namespace(self, mock_mcp_client, vector_store):
        """AI-012: Similarity search should only search within namespace"""
        # Arrange
        query_vector = np.random.rand(384)
        namespace = "tenant_456"

        mock_mcp_client.search_vectors = Mock(return_value=[])

        # Act
        results = vector_store.find_similar(
            query_vector,
            top_k=5,
            namespace=namespace
        )

        # Assert
        call_args = mock_mcp_client.search_vectors.call_args
        assert call_args[1]['namespace'] == namespace

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_default_namespace_is_used_when_not_specified(self, mock_mcp_client, vector_store):
        """AI-012: Should use default namespace when not specified"""
        # Arrange
        vector = np.random.rand(384)
        mock_mcp_client.upsert_vector = Mock(return_value={"success": True})

        # Act
        vector_store.add_vector(id="test_id", vector=vector, document="Test")

        # Assert
        call_args = mock_mcp_client.upsert_vector.call_args
        assert call_args[1]['namespace'] == "default"


class TestDeleteOperations:
    """Test vector deletion operations"""

    @pytest.fixture
    def vector_store(self):
        store = VectorStore()
        store.initialize()
        return store

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_delete_vector_calls_zerodb(self, mock_mcp_client, vector_store):
        """AI-012: Deleting a vector should call ZeroDB delete"""
        # Arrange
        vector_id = "vector_to_delete"
        namespace = "tenant_789"

        mock_mcp_client.delete_vector = Mock(return_value={"success": True})

        # Act
        result = vector_store.delete_vector(vector_id, namespace=namespace)

        # Assert
        assert result is True
        mock_mcp_client.delete_vector.assert_called_once_with(
            vector_id=vector_id,
            namespace=namespace
        )

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_delete_nonexistent_vector_returns_false(self, mock_mcp_client, vector_store):
        """AI-012: Deleting non-existent vector should return False"""
        # Arrange
        mock_mcp_client.delete_vector = Mock(return_value=None)

        # Act
        result = vector_store.delete_vector("nonexistent_id")

        # Assert
        assert result is False


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def vector_store(self):
        store = VectorStore()
        store.initialize()
        return store

    def test_add_vector_fails_when_not_initialized(self):
        """AI-012: Operations should fail gracefully when store not initialized"""
        # Arrange
        store = VectorStore()  # Not initialized
        vector = np.random.rand(384)

        # Act
        result = store.add_vector(id="test", vector=vector, document="Test")

        # Assert
        assert result is False

    def test_add_vector_rejects_invalid_vector_type(self, vector_store):
        """AI-012: Should reject non-numpy arrays"""
        # Arrange
        invalid_vector = [0.1, 0.2, 0.3]  # Python list, not numpy array

        # Act
        result = vector_store.add_vector(
            id="test",
            vector=invalid_vector,
            document="Test"
        )

        # Assert
        assert result is False

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_zerodb_error_handling(self, mock_mcp_client, vector_store):
        """AI-012: Should handle ZeroDB errors gracefully"""
        # Arrange
        vector = np.random.rand(384)
        mock_mcp_client.upsert_vector = Mock(side_effect=Exception("ZeroDB connection error"))

        # Act
        result = vector_store.add_vector(id="test", vector=vector, document="Test")

        # Assert
        assert result is False

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_find_similar_handles_invalid_threshold(self, mock_mcp_client, vector_store):
        """AI-012: Should clamp threshold to valid range [0.0, 1.0]"""
        # Arrange
        query_vector = np.random.rand(384)
        mock_mcp_client.search_vectors = Mock(return_value=[])

        # Act - threshold > 1.0
        results = vector_store.find_similar(query_vector, threshold=1.5)

        # Assert
        call_args = mock_mcp_client.search_vectors.call_args
        assert call_args[1]['threshold'] == 1.0  # Should be clamped

        # Act - threshold < 0.0
        vector_store.find_similar(query_vector, threshold=-0.5)

        # Assert
        call_args = mock_mcp_client.search_vectors.call_args
        assert call_args[1]['threshold'] == 0.0  # Should be clamped


class TestListVectors:
    """Test listing vectors in a namespace"""

    @pytest.fixture
    def vector_store(self):
        store = VectorStore()
        store.initialize()
        return store

    @patch('pseudoscribe.infrastructure.vector_store.mcp_client')
    def test_list_vectors_calls_zerodb(self, mock_mcp_client, vector_store):
        """AI-012: Listing vectors should call ZeroDB list_vectors"""
        # Arrange
        namespace = "tenant_999"
        mock_mcp_client.list_vectors = Mock(return_value=[
            {"vector_id": "vec1", "document": "Doc 1"},
            {"vector_id": "vec2", "document": "Doc 2"}
        ])

        # Act
        results = vector_store.list_vectors(namespace=namespace, limit=10)

        # Assert
        assert len(results) == 2
        mock_mcp_client.list_vectors.assert_called_once_with(
            namespace=namespace,
            limit=10,
            offset=0
        )
