import pytest
import numpy as np
from typing import Dict, List, Any
from pseudoscribe.infrastructure.model_manager import ModelManager
from pseudoscribe.infrastructure.vector_store import VectorStore

class TestContextRanking:
    @pytest.fixture
    def model_manager(self):
        return ModelManager()
        
    @pytest.fixture
    def sample_contexts(self):
        """Generate sample contexts with vectors and metadata for testing ranking"""
        # Create sample contexts with vectors and metadata
        contexts = {
            "doc1": {
                "vector": np.array([0.1, 0.2, 0.3, 0.4] * 192),  # 768-dim vector
                "metadata": {
                    "recency": 0.9,  # very recent
                    "relevance": 0.7,  # moderately relevant
                    "importance": 0.5  # average importance
                }
            },
            "doc2": {
                "vector": np.array([0.11, 0.21, 0.31, 0.41] * 192),  # similar to doc1
                "metadata": {
                    "recency": 0.3,  # older
                    "relevance": 0.9,  # highly relevant
                    "importance": 0.8  # important
                }
            },
            "doc3": {
                "vector": np.array([0.5, 0.6, 0.7, 0.8] * 192),  # different from doc1
                "metadata": {
                    "recency": 0.8,  # recent
                    "relevance": 0.3,  # less relevant
                    "importance": 0.9  # very important
                }
            },
            "doc4": {
                "vector": np.array([0.9, 0.8, 0.7, 0.6] * 192),  # very different from doc1
                "metadata": {
                    "recency": 0.5,  # medium recency
                    "relevance": 0.2,  # not very relevant
                    "importance": 0.1  # not important
                }
            }
        }
        return contexts
    
    @pytest.mark.asyncio
    async def test_rank_contexts_by_similarity(self, model_manager, sample_contexts):
        """AI-006: Verify contexts are ranked by similarity"""
        # Arrange
        query_vector = sample_contexts["doc1"]["vector"]
        
        # Act
        results = await model_manager.rank_contexts(
            query_vector=query_vector,
            contexts=sample_contexts,
            ranking_method="similarity"
        )
        
        # Assert
        assert len(results) == 4, "Should return all contexts"
        assert results[0]["id"] == "doc1", "Most similar should be first"
        assert all("score" in item for item in results), "Each result should have a score"
        assert all("id" in item for item in results), "Each result should have an id"
        
    @pytest.mark.asyncio
    async def test_rank_contexts_with_weighted_factors(self, model_manager, sample_contexts):
        """AI-006: Verify contexts are ranked with weighted factors"""
        # Arrange
        query_vector = sample_contexts["doc1"]["vector"]
        weights = {
            "similarity": 0.5,
            "recency": 0.3,
            "relevance": 0.1,
            "importance": 0.1
        }
        
        # Act
        results = await model_manager.rank_contexts(
            query_vector=query_vector,
            contexts=sample_contexts,
            ranking_method="weighted",
            weights=weights
        )
        
        # Assert
        assert len(results) == 4, "Should return all contexts"
        assert all("score" in item for item in results), "Each result should have a score"
        assert all("id" in item for item in results), "Each result should have an id"
        # Doc1 should still be first due to high similarity and recency
        assert results[0]["id"] == "doc1", "Doc1 should be first with these weights"
        
    @pytest.mark.asyncio
    async def test_rank_contexts_with_custom_ranking(self, model_manager, sample_contexts):
        """AI-006: Verify contexts can be ranked with custom ranking function"""
        # Arrange
        query_vector = sample_contexts["doc1"]["vector"]
        
        # Custom ranking that prioritizes importance over similarity
        custom_ranking = {
            "name": "importance_first",
            "factors": {
                "importance": 0.7,
                "similarity": 0.3
            }
        }
        
        # Act
        results = await model_manager.rank_contexts(
            query_vector=query_vector,
            contexts=sample_contexts,
            ranking_method="custom",
            custom_ranking=custom_ranking
        )
        
        # Assert
        assert len(results) == 4, "Should return all contexts"
        # Doc3 has highest importance
        assert results[0]["id"] == "doc3", "Doc3 should be first with importance-focused ranking"
        
    @pytest.mark.asyncio
    async def test_rank_contexts_with_threshold(self, model_manager, sample_contexts):
        """AI-006: Verify contexts can be filtered with threshold"""
        # Arrange
        query_vector = sample_contexts["doc1"]["vector"]
        
        # Act
        results = await model_manager.rank_contexts(
            query_vector=query_vector,
            contexts=sample_contexts,
            ranking_method="similarity",
            threshold=0.9  # High threshold
        )
        
        # Assert
        assert len(results) < 4, "Should return fewer than all contexts"
        assert all(item["score"] >= 0.9 for item in results), "All scores should be above threshold"
