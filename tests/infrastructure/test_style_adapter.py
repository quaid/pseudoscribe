import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from pseudoscribe.infrastructure.style_checker import StyleChecker

class TestStyleAdapter:
    """Test suite for the StyleAdapter class."""
    
    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
        # Make the async methods return AsyncMock objects
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler
    
    @pytest.fixture
    def style_checker(self):
        """Create a StyleChecker mock for testing."""
        checker = MagicMock()
        checker.check_style_against_profile = AsyncMock()
        checker.check_style_against_target_characteristics = AsyncMock()
        return checker
    
    @pytest.fixture
    def model_manager(self):
        """Create a ModelManager mock for testing."""
        manager = MagicMock()
        manager.generate_text = AsyncMock()
        return manager
    
    @pytest.fixture
    def style_adapter(self, style_profiler, style_checker, model_manager):
        """Create a StyleAdapter instance for testing."""
        # We'll import this after we create the implementation file
        from pseudoscribe.infrastructure.style_adapter import StyleAdapter
        return StyleAdapter(
            style_profiler=style_profiler,
            style_checker=style_checker,
            model_manager=model_manager
        )
    
    @pytest.mark.asyncio
    async def test_adapt_text_to_profile(self, style_adapter, style_profiler, style_checker, model_manager):
        """Test that adapt_text_to_profile adapts text to match a profile."""
        # Arrange
        text = "This is a sample text for style adaptation."
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
        
        # Mock the style check
        mock_check_result = {
            "overall_match": 0.6,
            "deviations": {
                "complexity": 0.1,
                "formality": 0.2,
                "tone": -0.1,
                "readability": 0.1
            },
            "suggestions": [
                "Use more formal language and avoid contractions to increase formality."
            ]
        }
        style_checker.check_style_against_profile.return_value = mock_check_result
        
        # Mock the text generation
        adapted_text = "This is an adapted sample text with more formal language for style adaptation."
        model_manager.generate_text.return_value = adapted_text
        
        # Act
        result = await style_adapter.adapt_text_to_profile(text, profile_id)
        
        # Assert
        assert result is not None
        assert "original_text" in result
        assert "adapted_text" in result
        assert "style_match" in result
        assert "profile_id" in result
        
        assert result["original_text"] == text
        assert result["adapted_text"] == adapted_text
        assert result["profile_id"] == profile_id
        assert isinstance(result["style_match"], float)
        
        # Verify the profiler methods were called
        style_profiler.retrieve_profile.assert_called_once_with(profile_id)
        # Check that check_style_against_profile was called with the original text first
        assert style_checker.check_style_against_profile.call_count == 2
        assert style_checker.check_style_against_profile.call_args_list[0] == ((text, profile_id),)
        model_manager.generate_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_adapt_text_to_characteristics(self, style_adapter, style_checker, model_manager):
        """Test that adapt_text_to_characteristics adapts text to match target characteristics."""
        # Arrange
        text = "This is a sample text for style adaptation."
        target_characteristics = {
            "complexity": 0.7,
            "formality": 0.8,
            "tone": 0.5,
            "readability": 0.6
        }
        
        # Mock the style check
        mock_check_result = {
            "overall_match": 0.6,
            "deviations": {
                "complexity": 0.1,
                "formality": 0.2,
                "tone": -0.1,
                "readability": 0.1
            },
            "suggestions": [
                "Use more formal language and avoid contractions to increase formality."
            ]
        }
        style_checker.check_style_against_target_characteristics.return_value = mock_check_result
        
        # Mock the text generation
        adapted_text = "This is an adapted sample text with more formal language for style adaptation."
        model_manager.generate_text.return_value = adapted_text
        
        # Act
        result = await style_adapter.adapt_text_to_characteristics(text, target_characteristics)
        
        # Assert
        assert result is not None
        assert "original_text" in result
        assert "adapted_text" in result
        assert "style_match" in result
        assert "target_characteristics" in result
        
        assert result["original_text"] == text
        assert result["adapted_text"] == adapted_text
        assert result["target_characteristics"] == target_characteristics
        assert isinstance(result["style_match"], float)
        
        # Verify the profiler method was called
        # Check that check_style_against_target_characteristics was called with the original text first
        assert style_checker.check_style_against_target_characteristics.call_count == 2
        assert style_checker.check_style_against_target_characteristics.call_args_list[0] == ((text, target_characteristics),)
        model_manager.generate_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_adapt_text_with_nonexistent_profile(self, style_adapter, style_profiler):
        """Test that adapt_text_to_profile handles nonexistent profiles."""
        # Arrange
        text = "This is a sample text for style adaptation."
        profile_id = "nonexistent_profile"
        
        # Mock the profile retrieval to return None (profile not found)
        style_profiler.retrieve_profile.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Profile with ID {profile_id} not found"):
            await style_adapter.adapt_text_to_profile(text, profile_id)
    
    @pytest.mark.asyncio
    async def test_adapt_text_with_empty_text(self, style_adapter):
        """Test that adapt_text_to_profile handles empty text."""
        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await style_adapter.adapt_text_to_profile("", "test_profile")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await style_adapter.adapt_text_to_characteristics("", {"complexity": 0.5})
    
    @pytest.mark.asyncio
    async def test_adapt_text_with_empty_characteristics(self, style_adapter):
        """Test that adapt_text_to_characteristics handles empty characteristics."""
        # Act & Assert
        with pytest.raises(ValueError, match="Target characteristics cannot be empty"):
            await style_adapter.adapt_text_to_characteristics("Some text", {})
    
    @pytest.mark.asyncio
    async def test_generate_adaptation_prompt(self, style_adapter):
        """Test that _generate_adaptation_prompt creates appropriate prompts."""
        # Arrange
        text = "This is a sample text."
        suggestions = [
            "Use more formal language and avoid contractions.",
            "Use more complex sentence structures."
        ]
        
        # Act
        prompt = style_adapter._generate_adaptation_prompt(text, suggestions)
        
        # Assert
        assert isinstance(prompt, str)
        assert text in prompt
        for suggestion in suggestions:
            assert suggestion in prompt
