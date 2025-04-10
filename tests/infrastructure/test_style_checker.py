import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from pseudoscribe.infrastructure.style_checker import StyleChecker

class TestStyleChecker:
    """Test suite for the StyleChecker class."""
    
    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
        # Make the async methods return AsyncMock objects
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler
    
    @pytest.fixture
    def style_checker(self, style_profiler):
        """Create a StyleChecker instance for testing."""
        return StyleChecker(style_profiler=style_profiler)
    
    @pytest.mark.asyncio
    async def test_check_style_against_profile(self, style_checker, style_profiler):
        """Test that check_style_against_profile returns style check results."""
        # Arrange
        text = "This is a sample text for style checking."
        profile_id = "test_profile"
        
        # Mock the profile retrieval
        mock_profile = {
            "id": profile_id,
            "characteristics": {
                "complexity": 0.7,
                "formality": 0.8,
                "tone": 0.5,
                "readability": 0.6
            }
        }
        style_profiler.retrieve_profile.return_value = mock_profile
        
        # Mock the text analysis
        mock_characteristics = {
            "complexity": 0.6,
            "formality": 0.7,
            "tone": 0.4,
            "readability": 0.5
        }
        style_profiler.analyze_text.return_value = mock_characteristics
        
        # Act
        result = await style_checker.check_style_against_profile(text, profile_id)
        
        # Assert
        assert result is not None
        assert "overall_match" in result
        assert "deviations" in result
        assert "suggestions" in result
        assert isinstance(result["overall_match"], float)
        assert 0 <= result["overall_match"] <= 1
        assert isinstance(result["deviations"], dict)
        assert isinstance(result["suggestions"], list)
        
        # Verify the profiler methods were called
        style_profiler.retrieve_profile.assert_called_once_with(profile_id)
        style_profiler.analyze_text.assert_called_once_with(text)
    
    @pytest.mark.asyncio
    async def test_check_style_with_nonexistent_profile(self, style_checker, style_profiler):
        """Test that check_style_against_profile handles nonexistent profiles."""
        # Arrange
        text = "This is a sample text for style checking."
        profile_id = "nonexistent_profile"
        
        # Mock the profile retrieval to return None (profile not found)
        style_profiler.retrieve_profile.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Profile with ID {profile_id} not found"):
            await style_checker.check_style_against_profile(text, profile_id)
    
    @pytest.mark.asyncio
    async def test_check_style_with_empty_text(self, style_checker):
        """Test that check_style_against_profile handles empty text."""
        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await style_checker.check_style_against_profile("", "test_profile")
    
    @pytest.mark.asyncio
    async def test_generate_style_suggestions(self, style_checker):
        """Test that generate_style_suggestions returns appropriate suggestions."""
        # Arrange
        deviations = {
            "complexity": 0.2,  # Target is higher (more complex)
            "formality": -0.1,  # Target is lower (less formal)
            "tone": 0.05,       # Small deviation
            "readability": -0.3  # Target is lower (less readable)
        }
        
        # Act
        suggestions = style_checker._generate_style_suggestions(deviations)
        
        # Assert
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check that we have suggestions for significant deviations
        has_complexity_suggestion = any("complex" in suggestion.lower() for suggestion in suggestions)
        has_readability_suggestion = any("readab" in suggestion.lower() for suggestion in suggestions)
        
        assert has_complexity_suggestion
        assert has_readability_suggestion
    
    @pytest.mark.asyncio
    async def test_calculate_style_match(self, style_checker):
        """Test that calculate_style_match returns an accurate match score."""
        # Arrange
        target_characteristics = {
            "complexity": 0.7,
            "formality": 0.8,
            "tone": 0.5,
            "readability": 0.6
        }
        
        actual_characteristics = {
            "complexity": 0.6,
            "formality": 0.7,
            "tone": 0.4,
            "readability": 0.5
        }
        
        # Act
        match_score, deviations = style_checker._calculate_style_match(
            target_characteristics, actual_characteristics
        )
        
        # Assert
        assert isinstance(match_score, float)
        assert 0 <= match_score <= 1
        assert isinstance(deviations, dict)
        assert set(deviations.keys()) == set(target_characteristics.keys())
        
        # Check that deviations are calculated correctly
        for key in target_characteristics:
            expected_deviation = target_characteristics[key] - actual_characteristics[key]
            assert abs(deviations[key] - expected_deviation) < 0.001
    
    @pytest.mark.asyncio
    async def test_check_style_against_target_characteristics(self, style_checker, style_profiler):
        """Test that check_style_against_target_characteristics returns style check results."""
        # Arrange
        text = "This is a sample text for style checking."
        target_characteristics = {
            "complexity": 0.7,
            "formality": 0.8,
            "tone": 0.5,
            "readability": 0.6
        }
        
        # Mock the text analysis
        mock_characteristics = {
            "complexity": 0.6,
            "formality": 0.7,
            "tone": 0.4,
            "readability": 0.5
        }
        style_profiler.analyze_text.return_value = mock_characteristics
        
        # Act
        result = await style_checker.check_style_against_target_characteristics(
            text, target_characteristics
        )
        
        # Assert
        assert result is not None
        assert "overall_match" in result
        assert "deviations" in result
        assert "suggestions" in result
        
        # Verify the profiler method was called
        style_profiler.analyze_text.assert_called_once_with(text)
