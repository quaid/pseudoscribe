import pytest
import numpy as np
from unittest.mock import MagicMock, patch
import asyncio
from pseudoscribe.infrastructure.style_profiler import StyleProfiler

class TestStyleProfiler:
    """Test suite for the StyleProfiler class."""
    
    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler instance for testing."""
        model_manager = MagicMock()
        return StyleProfiler(model_manager=model_manager)
    
    @pytest.mark.asyncio
    async def test_analyze_text_returns_style_profile(self, style_profiler):
        """Test that analyze_text returns a style profile with expected attributes."""
        # Arrange
        text = "This is a sample text for style analysis. It should have certain characteristics."
        mock_vector = np.array([0.1, 0.2, 0.3])
        style_profiler.model_manager.generate_vector.return_value = mock_vector
        
        # Act
        profile = await style_profiler.analyze_text(text)
        
        # Assert
        assert profile is not None
        assert "complexity" in profile
        assert "formality" in profile
        assert "tone" in profile
        assert "readability" in profile
        assert isinstance(profile["complexity"], float)
        assert isinstance(profile["formality"], float)
        assert isinstance(profile["tone"], float)
        assert isinstance(profile["readability"], float)
        assert 0 <= profile["complexity"] <= 1
        assert 0 <= profile["formality"] <= 1
        assert 0 <= profile["tone"] <= 1
        assert 0 <= profile["readability"] <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_text_with_empty_text(self, style_profiler):
        """Test that analyze_text handles empty text appropriately."""
        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await style_profiler.analyze_text("")
    
    @pytest.mark.asyncio
    async def test_create_style_profile(self, style_profiler):
        """Test that create_style_profile creates a profile with the expected structure."""
        # Arrange
        text = "This is a sample text for style analysis."
        mock_vector = np.array([0.1, 0.2, 0.3])
        
        # Act
        profile = style_profiler._create_style_profile(text, mock_vector)
        
        # Assert
        assert "id" in profile
        assert "text_sample" in profile
        assert "vector" in profile
        assert "characteristics" in profile
        assert "complexity" in profile["characteristics"]
        assert "formality" in profile["characteristics"]
        assert "tone" in profile["characteristics"]
        assert "readability" in profile["characteristics"]
        assert "created_at" in profile
        assert "updated_at" in profile
    
    @pytest.mark.asyncio
    async def test_compare_profiles(self, style_profiler):
        """Test that compare_profiles returns similarity scores between profiles."""
        # Arrange
        profile1 = {
            "id": "profile1",
            "characteristics": {
                "complexity": 0.7,
                "formality": 0.8,
                "tone": 0.5,
                "readability": 0.6
            },
            "vector": np.array([0.1, 0.2, 0.3])
        }
        
        profile2 = {
            "id": "profile2",
            "characteristics": {
                "complexity": 0.6,
                "formality": 0.7,
                "tone": 0.4,
                "readability": 0.5
            },
            "vector": np.array([0.15, 0.25, 0.35])
        }
        
        # Act
        similarity = await style_profiler.compare_profiles(profile1, profile2)
        
        # Assert
        assert "overall" in similarity
        assert "vector_similarity" in similarity
        assert "characteristics_similarity" in similarity
        assert 0 <= similarity["overall"] <= 1
        assert 0 <= similarity["vector_similarity"] <= 1
        assert 0 <= similarity["characteristics_similarity"] <= 1
    
    @pytest.mark.asyncio
    async def test_store_profile(self, style_profiler):
        """Test that store_profile stores a profile and returns its ID."""
        # Arrange
        profile = {
            "id": "test_profile",
            "text_sample": "Sample text",
            "vector": np.array([0.1, 0.2, 0.3]),
            "characteristics": {
                "complexity": 0.7,
                "formality": 0.8,
                "tone": 0.5,
                "readability": 0.6
            },
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        # Mock the storage method
        style_profiler._save_profile = MagicMock(return_value="test_profile")
        
        # Act
        profile_id = await style_profiler.store_profile(profile)
        
        # Assert
        assert profile_id == "test_profile"
        style_profiler._save_profile.assert_called_once_with(profile)
    
    @pytest.mark.asyncio
    async def test_retrieve_profile(self, style_profiler):
        """Test that retrieve_profile retrieves a profile by ID."""
        # Arrange
        profile_id = "test_profile"
        mock_profile = {
            "id": profile_id,
            "text_sample": "Sample text",
            "vector": np.array([0.1, 0.2, 0.3]),
            "characteristics": {
                "complexity": 0.7,
                "formality": 0.8,
                "tone": 0.5,
                "readability": 0.6
            },
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        # Mock the retrieval method
        style_profiler._load_profile = MagicMock(return_value=mock_profile)
        
        # Act
        profile = await style_profiler.retrieve_profile(profile_id)
        
        # Assert
        assert profile == mock_profile
        style_profiler._load_profile.assert_called_once_with(profile_id)
