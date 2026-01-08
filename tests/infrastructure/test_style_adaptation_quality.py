"""Tests for style adaptation quality validation and enhancement.

Issue: AI-009 - Style Adaptation

These tests verify:
- Style transformation preserves meaning
- Quality checks ensure natural flow
- Iterative refinement improves output
- Performance meets SLAs
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any
import time

from pseudoscribe.infrastructure.style_adapter import StyleAdapter


class TestStyleTransformation:
    """Tests for style transformation with meaning preservation."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
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
        manager.generate_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def style_adapter(self, style_profiler, style_checker, model_manager):
        """Create a StyleAdapter instance for testing."""
        return StyleAdapter(
            style_profiler=style_profiler,
            style_checker=style_checker,
            model_manager=model_manager
        )

    @pytest.mark.asyncio
    async def test_adapt_with_semantic_preservation_check(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that adaptation validates semantic similarity."""
        # Arrange
        original_text = "The quick brown fox jumps over the lazy dog."
        adapted_text = "A swift auburn fox leaps over the idle canine."

        style_profiler.retrieve_profile.return_value = {
            "id": "formal-style",
            "characteristics": {"complexity": 0.7, "formality": 0.8, "tone": 0.5, "readability": 0.6}
        }

        style_checker.check_style_against_profile.return_value = {
            "overall_match": 0.5,
            "deviations": {"formality": 0.3},
            "suggestions": ["Use more formal language"]
        }

        model_manager.generate_text.return_value = adapted_text
        # Mock embeddings for semantic similarity
        model_manager.generate_vectors.side_effect = [
            np.array([0.8, 0.2, 0.1]),  # Original text embedding
            np.array([0.75, 0.25, 0.15])  # Adapted text embedding - similar
        ]

        # Act
        result = await style_adapter.adapt_with_quality_check(
            text=original_text,
            profile_id="formal-style"
        )

        # Assert
        assert result is not None
        assert "adapted_text" in result
        assert "semantic_similarity" in result
        assert result["semantic_similarity"] >= 0.7  # Meaning preserved

    @pytest.mark.asyncio
    async def test_adapt_rejects_low_semantic_similarity(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that adaptation rejects output with low semantic similarity."""
        # Arrange
        original_text = "The quick brown fox jumps over the lazy dog."
        bad_adaptation = "It was a dark and stormy night."  # Completely different meaning

        style_profiler.retrieve_profile.return_value = {
            "id": "formal-style",
            "characteristics": {"complexity": 0.7, "formality": 0.8, "tone": 0.5, "readability": 0.6}
        }

        style_checker.check_style_against_profile.return_value = {
            "overall_match": 0.5,
            "deviations": {"formality": 0.3},
            "suggestions": ["Use more formal language"]
        }

        model_manager.generate_text.return_value = bad_adaptation
        # Mock embeddings showing low similarity
        model_manager.generate_vectors.side_effect = [
            np.array([0.9, 0.1, 0.0]),  # Original
            np.array([0.1, 0.2, 0.9])   # Completely different
        ]

        # Act
        result = await style_adapter.adapt_with_quality_check(
            text=original_text,
            profile_id="formal-style"
        )

        # Assert
        assert result["quality_passed"] is False
        assert result["quality_issues"]["semantic_similarity"] < 0.5


class TestQualityValidation:
    """Tests for quality validation of adapted content."""

    @pytest.fixture
    def style_profiler(self):
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self):
        checker = MagicMock()
        checker.check_style_against_profile = AsyncMock()
        checker.check_style_against_target_characteristics = AsyncMock()
        return checker

    @pytest.fixture
    def model_manager(self):
        manager = MagicMock()
        manager.generate_text = AsyncMock()
        manager.generate_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def style_adapter(self, style_profiler, style_checker, model_manager):
        return StyleAdapter(
            style_profiler=style_profiler,
            style_checker=style_checker,
            model_manager=model_manager
        )

    @pytest.mark.asyncio
    async def test_validate_quality_checks_style_match(
        self, style_adapter, style_checker, model_manager
    ):
        """Test that quality validation checks style match threshold."""
        # Arrange
        adapted_text = "The adapted text content."
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        style_checker.check_style_against_target_characteristics.return_value = {
            "overall_match": 0.85,  # Good match
            "deviations": {"complexity": 0.1},
            "suggestions": []
        }

        # Act
        quality_result = await style_adapter.validate_quality(
            original_text="Original text",
            adapted_text=adapted_text,
            target_characteristics=target_characteristics
        )

        # Assert
        assert quality_result is not None
        assert "style_match" in quality_result
        assert quality_result["style_match"] >= 0.7  # Meets quality threshold

    @pytest.mark.asyncio
    async def test_validate_quality_checks_naturalness(
        self, style_adapter, style_checker, model_manager
    ):
        """Test that quality validation assesses naturalness/flow."""
        # Arrange
        adapted_text = "This flows naturally. The sentences connect well."
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.7}

        style_checker.check_style_against_target_characteristics.return_value = {
            "overall_match": 0.8,
            "deviations": {},
            "suggestions": []
        }

        # Mock readability analysis for naturalness
        model_manager.generate_vectors.side_effect = [
            np.array([0.5, 0.5, 0.5]),  # Original
            np.array([0.5, 0.5, 0.5])   # Adapted - similar
        ]

        # Act
        quality_result = await style_adapter.validate_quality(
            original_text="Original flows well. Sentences are clear.",
            adapted_text=adapted_text,
            target_characteristics=target_characteristics
        )

        # Assert
        assert "naturalness_score" in quality_result
        assert quality_result["naturalness_score"] >= 0.0
        assert quality_result["naturalness_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_validate_quality_returns_comprehensive_report(
        self, style_adapter, style_checker, model_manager
    ):
        """Test that quality validation returns all required metrics."""
        # Arrange
        original_text = "Original text here."
        adapted_text = "Adapted text here."
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        style_checker.check_style_against_target_characteristics.return_value = {
            "overall_match": 0.8,
            "deviations": {},
            "suggestions": []
        }

        model_manager.generate_vectors.side_effect = [
            np.array([0.5, 0.5, 0.5]),
            np.array([0.5, 0.5, 0.5])
        ]

        # Act
        quality_result = await style_adapter.validate_quality(
            original_text=original_text,
            adapted_text=adapted_text,
            target_characteristics=target_characteristics
        )

        # Assert - comprehensive quality report
        assert "style_match" in quality_result
        assert "semantic_similarity" in quality_result
        assert "naturalness_score" in quality_result
        assert "overall_quality" in quality_result
        assert "passed" in quality_result


class TestIterativeRefinement:
    """Tests for iterative refinement of adaptations."""

    @pytest.fixture
    def style_profiler(self):
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self):
        checker = MagicMock()
        checker.check_style_against_profile = AsyncMock()
        checker.check_style_against_target_characteristics = AsyncMock()
        return checker

    @pytest.fixture
    def model_manager(self):
        manager = MagicMock()
        manager.generate_text = AsyncMock()
        manager.generate_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def style_adapter(self, style_profiler, style_checker, model_manager):
        return StyleAdapter(
            style_profiler=style_profiler,
            style_checker=style_checker,
            model_manager=model_manager
        )

    @pytest.mark.asyncio
    async def test_iterative_adapt_improves_quality(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that iterative adaptation improves quality over passes."""
        # Arrange
        original_text = "Simple text needing adaptation."

        style_profiler.retrieve_profile.return_value = {
            "id": "target-style",
            "characteristics": {"complexity": 0.7, "formality": 0.8, "tone": 0.5, "readability": 0.6}
        }

        # Mock improving quality scores with each iteration (need more for iterative + final check)
        style_checker.check_style_against_profile.side_effect = [
            {"overall_match": 0.5, "deviations": {"formality": 0.3}, "suggestions": ["More formal"]},
            {"overall_match": 0.7, "deviations": {"formality": 0.1}, "suggestions": ["Slightly more formal"]},
            {"overall_match": 0.9, "deviations": {}, "suggestions": []},
            {"overall_match": 0.9, "deviations": {}, "suggestions": []},  # Final check
        ]

        model_manager.generate_text.side_effect = [
            "Better adapted text.",
            "Even better adapted text.",
            "Perfectly adapted text."
        ]

        model_manager.generate_vectors.return_value = np.array([0.5, 0.5, 0.5])

        # Act
        result = await style_adapter.iterative_adapt(
            text=original_text,
            profile_id="target-style",
            max_iterations=3,
            quality_threshold=0.85
        )

        # Assert
        assert result is not None
        assert result["iterations_used"] <= 3
        assert result["final_quality"] >= 0.85

    @pytest.mark.asyncio
    async def test_iterative_adapt_stops_at_quality_threshold(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that iteration stops when quality threshold is met."""
        # Arrange
        original_text = "Text to adapt."

        style_profiler.retrieve_profile.return_value = {
            "id": "target-style",
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}
        }

        # Quality threshold met on second iteration (need final check too)
        style_checker.check_style_against_profile.side_effect = [
            {"overall_match": 0.6, "deviations": {"formality": 0.2}, "suggestions": ["Adjust"]},
            {"overall_match": 0.92, "deviations": {}, "suggestions": []},  # Meets threshold
            {"overall_match": 0.92, "deviations": {}, "suggestions": []},  # Final check
        ]

        model_manager.generate_text.side_effect = [
            "First adaptation.",
            "Great adaptation."
        ]

        model_manager.generate_vectors.return_value = np.array([0.5, 0.5, 0.5])

        # Act
        result = await style_adapter.iterative_adapt(
            text=original_text,
            profile_id="target-style",
            max_iterations=5,
            quality_threshold=0.9
        )

        # Assert - should stop after 2 iterations since threshold met
        assert result["iterations_used"] == 2
        assert result["early_stopped"] is True

    @pytest.mark.asyncio
    async def test_iterative_adapt_returns_best_result_on_max_iterations(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that max iterations returns best result so far."""
        # Arrange
        original_text = "Text to adapt."

        style_profiler.retrieve_profile.return_value = {
            "id": "target-style",
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}
        }

        # Never reaches threshold but improves (need final check too)
        style_checker.check_style_against_profile.side_effect = [
            {"overall_match": 0.5, "deviations": {"formality": 0.3}, "suggestions": ["Adjust"]},
            {"overall_match": 0.6, "deviations": {"formality": 0.2}, "suggestions": ["More"]},
            {"overall_match": 0.7, "deviations": {"formality": 0.1}, "suggestions": ["Final"]},
            {"overall_match": 0.7, "deviations": {"formality": 0.1}, "suggestions": []},  # Final check
        ]

        model_manager.generate_text.side_effect = [
            "First attempt.",
            "Second attempt.",
            "Third attempt."
        ]

        model_manager.generate_vectors.return_value = np.array([0.5, 0.5, 0.5])

        # Act
        result = await style_adapter.iterative_adapt(
            text=original_text,
            profile_id="target-style",
            max_iterations=3,
            quality_threshold=0.95  # Won't be reached
        )

        # Assert
        assert result["iterations_used"] == 3
        assert result["early_stopped"] is False
        # Best result is the last one with highest quality
        assert result["final_quality"] >= 0.7


class TestAdaptationPerformance:
    """Tests for adaptation performance SLAs."""

    @pytest.fixture
    def style_profiler(self):
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self):
        checker = MagicMock()
        checker.check_style_against_profile = AsyncMock()
        checker.check_style_against_target_characteristics = AsyncMock()
        return checker

    @pytest.fixture
    def model_manager(self):
        manager = MagicMock()
        manager.generate_text = AsyncMock()
        manager.generate_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def style_adapter(self, style_profiler, style_checker, model_manager):
        return StyleAdapter(
            style_profiler=style_profiler,
            style_checker=style_checker,
            model_manager=model_manager
        )

    @pytest.mark.asyncio
    async def test_single_adaptation_under_2_seconds(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that single adaptation completes under 2 seconds."""
        # Arrange
        text = "Sample text for adaptation performance testing. " * 20

        style_profiler.retrieve_profile.return_value = {
            "id": "test-style",
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}
        }

        style_checker.check_style_against_profile.return_value = {
            "overall_match": 0.5,
            "deviations": {"formality": 0.2},
            "suggestions": ["Adjust formality"]
        }

        model_manager.generate_text.return_value = "Adapted text result."
        model_manager.generate_vectors.return_value = np.array([0.5, 0.5, 0.5])

        # Act
        start_time = time.time()
        result = await style_adapter.adapt_text_to_profile(text, "test-style")
        elapsed_time = time.time() - start_time

        # Assert
        assert result is not None
        assert elapsed_time < 2.0, f"Adaptation took {elapsed_time:.2f}s, exceeds 2s SLA"

    @pytest.mark.asyncio
    async def test_adaptation_includes_timing_metadata(
        self, style_adapter, style_profiler, style_checker, model_manager
    ):
        """Test that adaptation result includes timing information."""
        # Arrange
        text = "Text for timing test."

        style_profiler.retrieve_profile.return_value = {
            "id": "test-style",
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}
        }

        style_checker.check_style_against_profile.return_value = {
            "overall_match": 0.5,
            "deviations": {"formality": 0.2},
            "suggestions": ["Adjust"]
        }

        model_manager.generate_text.return_value = "Adapted result."
        model_manager.generate_vectors.return_value = np.array([0.5, 0.5, 0.5])

        # Act
        result = await style_adapter.adapt_with_quality_check(
            text=text,
            profile_id="test-style"
        )

        # Assert
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], (int, float))
        assert result["processing_time_ms"] >= 0


class TestFeedbackLearning:
    """Tests for feedback-based learning system."""

    @pytest.fixture
    def style_profiler(self):
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self):
        checker = MagicMock()
        checker.check_style_against_profile = AsyncMock()
        checker.check_style_against_target_characteristics = AsyncMock()
        return checker

    @pytest.fixture
    def model_manager(self):
        manager = MagicMock()
        manager.generate_text = AsyncMock()
        manager.generate_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def style_adapter(self, style_profiler, style_checker, model_manager):
        return StyleAdapter(
            style_profiler=style_profiler,
            style_checker=style_checker,
            model_manager=model_manager
        )

    @pytest.mark.asyncio
    async def test_record_adaptation_feedback(self, style_adapter):
        """Test that feedback can be recorded for an adaptation."""
        # Arrange
        adaptation_id = "adapt-123"
        feedback = {
            "quality_rating": 4,
            "meaning_preserved": True,
            "style_accurate": True,
            "user_comment": "Good adaptation"
        }

        # Act
        result = await style_adapter.record_feedback(
            adaptation_id=adaptation_id,
            feedback=feedback
        )

        # Assert
        assert result is not None
        assert result["recorded"] is True
        assert result["adaptation_id"] == adaptation_id

    @pytest.mark.asyncio
    async def test_get_adaptation_statistics(self, style_adapter):
        """Test that adaptation statistics can be retrieved."""
        # Arrange
        profile_id = "formal-style"

        # Act
        stats = await style_adapter.get_adaptation_stats(profile_id=profile_id)

        # Assert
        assert stats is not None
        assert "total_adaptations" in stats
        assert "average_quality" in stats
        assert "success_rate" in stats

    @pytest.mark.asyncio
    async def test_feedback_affects_future_adaptations(self, style_adapter):
        """Test that recorded feedback influences adaptation behavior."""
        # Arrange
        profile_id = "test-style"

        # Record positive feedback for a particular prompt style
        await style_adapter.record_feedback(
            adaptation_id="adapt-1",
            feedback={"quality_rating": 5, "prompt_effective": True}
        )

        # Act
        adaptation_context = await style_adapter.get_adaptation_context(profile_id)

        # Assert
        assert adaptation_context is not None
        assert "learned_preferences" in adaptation_context
