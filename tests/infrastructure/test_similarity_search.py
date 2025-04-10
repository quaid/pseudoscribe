import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from pseudoscribe.infrastructure.model_manager import ModelManager
from pseudoscribe.infrastructure.vector_generator import VectorGenerator

class TestSimilaritySearch:
    @pytest.fixture
    def model_manager(self):
        return ModelManager()
        
    @pytest.fixture
    def sample_vectors(self):
        """Generate sample vectors for testing similarity search"""
        # Create 5 sample vectors with known similarities
        return {
            "doc1": np.array([0.1, 0.2, 0.3, 0.4] * 192),  # 768-dim vector
            "doc2": np.array([0.1, 0.2, 0.3, 0.5] * 192),  # similar to doc1
            "doc3": np.array([0.5, 0.6, 0.7, 0.8] * 192),  # different from doc1
            "doc4": np.array([0.11, 0.21, 0.31, 0.41] * 192),  # very similar to doc1
            "doc5": np.array([0.9, 0.8, 0.7, 0.6] * 192),  # very different from doc1
        }
    
    @pytest.mark.asyncio
    async def test_find_similar_vectors(self, model_manager, sample_vectors):
        """AI-005: Verify similarity search returns correct results"""
        # Arrange
        query_vector = sample_vectors["doc1"]
        
        # Act
        results = await model_manager.find_similar_vectors(query_vector, top_k=3)
        
        # Assert
        assert len(results) == 3, "Should return exactly top_k results"
        assert isinstance(results, list), "Results should be a list"
        assert all(isinstance(item, dict) for item in results), "Each result should be a dict"
        assert all("score" in item for item in results), "Each result should have a score"
        assert all("id" in item for item in results), "Each result should have an id"
        
    @pytest.mark.asyncio
    async def test_similarity_threshold(self, model_manager, sample_vectors):
        """AI-005: Verify similarity threshold filters results correctly"""
        # Arrange
        query_vector = sample_vectors["doc1"]
        
        # Act
        results = await model_manager.find_similar_vectors(
            query_vector, 
            top_k=5,
            threshold=0.8
        )
        
        # Assert
        assert all(item["score"] >= 0.8 for item in results), "All results should meet threshold"
        
    @pytest.mark.asyncio
    async def test_empty_vector_store(self, model_manager):
        """AI-005: Verify empty vector store returns empty results"""
        # Arrange
        query_vector = np.random.rand(768)
        
        # Act
        results = await model_manager.find_similar_vectors(query_vector, top_k=3)
        
        # Assert
        assert len(results) == 0, "Empty vector store should return empty results"
