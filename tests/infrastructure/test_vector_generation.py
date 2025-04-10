import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock
from pseudoscribe.infrastructure.model_manager import ModelManager

class TestVectorGeneration:
    @pytest.fixture
    def model_manager(self):
        return ModelManager()
        
    @pytest.mark.asyncio
    async def test_embedding_dimensions(self, model_manager):
        """AI-004: Verify vector output dimensions match specs"""
        # Arrange
        test_input = "Sample text for vectorization"
        
        # Act
        vectors = await model_manager.generate_vectors(test_input)
        
        # Assert
        assert isinstance(vectors, np.ndarray), "Expected numpy array output"
        assert vectors.shape == (768,), "Expected 768-dimensional vector"
        assert not np.isnan(vectors).any(), "Vector should not contain NaN values"
