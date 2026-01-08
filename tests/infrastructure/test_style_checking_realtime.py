"""Tests for real-time style checking and batch analysis.

Issue: AI-008 - Style Checking

These tests verify:
- Real-time deviation detection with inline highlighting
- Position tracking for style deviations
- Batch checking with severity ranking
- Performance SLA (<1s per check)
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List
import time

from pseudoscribe.infrastructure.style_checker import StyleChecker


class TestRealTimeDeviationDetection:
    """Tests for real-time style deviation detection with inline highlighting."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        profiler.analyze_segment = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self, style_profiler):
        """Create a StyleChecker instance for testing."""
        return StyleChecker(style_profiler=style_profiler)

    @pytest.mark.asyncio
    async def test_check_realtime_returns_inline_deviations(self, style_checker, style_profiler):
        """Test that real-time check returns deviations with character positions."""
        # Arrange
        text = "This is a very complex sentence that deviates from the simple style."
        target_characteristics = {
            "complexity": 0.3,  # Target simple style
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.8
        }

        # Mock analysis to return high complexity for this segment
        style_profiler.analyze_text.return_value = {
            "complexity": 0.8,  # High complexity - deviates from target
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.4
        }

        # Act
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics
        )

        # Assert
        assert result is not None
        assert "inline_deviations" in result
        assert isinstance(result["inline_deviations"], list)
        # Should have at least one deviation
        assert len(result["inline_deviations"]) > 0

    @pytest.mark.asyncio
    async def test_inline_deviation_contains_position_info(self, style_checker, style_profiler):
        """Test that inline deviations contain start/end positions."""
        # Arrange
        text = "This is overly complex."
        target_characteristics = {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8}

        style_profiler.analyze_text.return_value = {
            "complexity": 0.9,
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.3
        }

        # Act
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics
        )

        # Assert
        if result["inline_deviations"]:
            deviation = result["inline_deviations"][0]
            assert "start" in deviation
            assert "end" in deviation
            assert "type" in deviation
            assert "severity" in deviation
            assert "message" in deviation
            assert isinstance(deviation["start"], int)
            assert isinstance(deviation["end"], int)
            assert deviation["start"] >= 0
            assert deviation["end"] <= len(text)
            assert deviation["end"] > deviation["start"]

    @pytest.mark.asyncio
    async def test_inline_deviation_includes_suggestion(self, style_checker, style_profiler):
        """Test that inline deviations include actionable suggestions."""
        # Arrange
        text = "The aforementioned paradigm necessitates consideration."  # Too formal
        target_characteristics = {"complexity": 0.3, "formality": 0.3, "tone": 0.5, "readability": 0.8}

        style_profiler.analyze_text.return_value = {
            "complexity": 0.8,
            "formality": 0.9,  # High formality deviation
            "tone": 0.5,
            "readability": 0.2
        }

        # Act
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics
        )

        # Assert
        if result["inline_deviations"]:
            deviation = result["inline_deviations"][0]
            assert "suggestion" in deviation
            assert isinstance(deviation["suggestion"], str)
            assert len(deviation["suggestion"]) > 0

    @pytest.mark.asyncio
    async def test_realtime_check_sentence_level_granularity(self, style_checker, style_profiler):
        """Test that real-time check analyzes at sentence level for better granularity."""
        # Arrange
        text = "Simple sentence. A very complex, convoluted, and overly elaborate sentence follows."
        target_characteristics = {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8}

        # Mock to simulate different complexity for different sentences
        style_profiler.analyze_segment = AsyncMock(side_effect=[
            {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8},  # Simple sentence
            {"complexity": 0.9, "formality": 0.5, "tone": 0.5, "readability": 0.2},  # Complex sentence
        ])

        # Act
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics,
            granularity="sentence"
        )

        # Assert
        assert result is not None
        # Should identify the second sentence as a deviation
        deviations = result.get("inline_deviations", [])
        # At least one deviation should be detected for the complex sentence
        if deviations:
            # Check that the deviation is in the second half of the text
            # The first sentence "Simple sentence." is 17 chars, so second starts after that
            first_sentence_end = len("Simple sentence.")
            has_deviation_in_complex = any(
                d["start"] >= first_sentence_end for d in deviations
            )
            assert has_deviation_in_complex

    @pytest.mark.asyncio
    async def test_realtime_check_empty_text(self, style_checker, style_profiler):
        """Test that real-time check handles empty text gracefully."""
        # Arrange
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await style_checker.check_realtime(
                text="",
                target_characteristics=target_characteristics
            )

    @pytest.mark.asyncio
    async def test_realtime_check_no_deviations_for_matching_text(self, style_checker, style_profiler):
        """Test that matching text returns no deviations."""
        # Arrange
        text = "This is a simple sentence."
        target_characteristics = {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8}

        # Mock to return matching characteristics
        style_profiler.analyze_text.return_value = {
            "complexity": 0.35,  # Within tolerance
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.78
        }

        # Act
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics
        )

        # Assert - should have no or minimal deviations
        assert result is not None
        assert "inline_deviations" in result
        # All deviations should have low severity if any
        for deviation in result["inline_deviations"]:
            assert deviation.get("severity", "low") in ["low", "info"]


class TestBatchStyleChecking:
    """Tests for batch style checking with severity ranking."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        profiler.analyze_segment = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self, style_profiler):
        """Create a StyleChecker instance for testing."""
        return StyleChecker(style_profiler=style_profiler)

    @pytest.mark.asyncio
    async def test_batch_check_returns_all_issues(self, style_checker, style_profiler):
        """Test that batch check identifies all style issues."""
        # Arrange
        content = """
        This is the first paragraph. It's simple and easy to read.

        The second paragraph contains exceedingly complex vocabulary and
        convoluted sentence structures that significantly deviate from
        the target style profile parameters.

        Third paragraph returns to simplicity.
        """
        target_characteristics = {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8}

        # Mock profile
        style_profiler.retrieve_profile.return_value = {
            "id": "test-profile",
            "characteristics": target_characteristics
        }

        # Mock segment analysis
        style_profiler.analyze_segment = AsyncMock(side_effect=[
            {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8},  # Para 1 - OK
            {"complexity": 0.9, "formality": 0.8, "tone": 0.5, "readability": 0.2},  # Para 2 - Issues
            {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8},  # Para 3 - OK
        ])

        # Act
        result = await style_checker.batch_check(
            content=content,
            profile_id="test-profile"
        )

        # Assert
        assert result is not None
        assert "issues" in result
        assert isinstance(result["issues"], list)
        assert len(result["issues"]) >= 1  # At least one issue for paragraph 2

    @pytest.mark.asyncio
    async def test_batch_check_ranks_issues_by_severity(self, style_checker, style_profiler):
        """Test that batch check ranks issues by severity (highest first)."""
        # Arrange
        content = "Mild issue sentence. SEVERE issue with many problems. Another mild issue."
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        style_profiler.retrieve_profile.return_value = {
            "id": "test-profile",
            "characteristics": target_characteristics
        }

        # Mock different severity levels
        style_profiler.analyze_segment = AsyncMock(side_effect=[
            {"complexity": 0.6, "formality": 0.5, "tone": 0.5, "readability": 0.5},  # Mild
            {"complexity": 0.95, "formality": 0.95, "tone": 0.95, "readability": 0.1},  # Severe
            {"complexity": 0.6, "formality": 0.5, "tone": 0.5, "readability": 0.5},  # Mild
        ])

        # Act
        result = await style_checker.batch_check(
            content=content,
            profile_id="test-profile"
        )

        # Assert
        issues = result.get("issues", [])
        if len(issues) >= 2:
            # Verify issues are sorted by severity (high to low)
            severities = [issue["severity_score"] for issue in issues]
            assert severities == sorted(severities, reverse=True)

    @pytest.mark.asyncio
    async def test_batch_check_issue_contains_required_fields(self, style_checker, style_profiler):
        """Test that each issue contains all required fields."""
        # Arrange
        content = "Complex issue here."
        target_characteristics = {"complexity": 0.3, "formality": 0.5, "tone": 0.5, "readability": 0.8}

        style_profiler.retrieve_profile.return_value = {
            "id": "test-profile",
            "characteristics": target_characteristics
        }

        style_profiler.analyze_segment = AsyncMock(return_value={
            "complexity": 0.9,
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.2
        })

        # Act
        result = await style_checker.batch_check(
            content=content,
            profile_id="test-profile"
        )

        # Assert
        if result["issues"]:
            issue = result["issues"][0]
            assert "location" in issue
            assert "start" in issue["location"]
            assert "end" in issue["location"]
            assert "severity_score" in issue
            assert "severity_level" in issue
            assert issue["severity_level"] in ["low", "medium", "high", "critical"]
            assert "type" in issue
            assert "description" in issue
            assert "suggestions" in issue
            assert isinstance(issue["suggestions"], list)

    @pytest.mark.asyncio
    async def test_batch_check_summary_statistics(self, style_checker, style_profiler):
        """Test that batch check returns summary statistics."""
        # Arrange
        content = "Some content with potential issues."
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        style_profiler.retrieve_profile.return_value = {
            "id": "test-profile",
            "characteristics": target_characteristics
        }

        style_profiler.analyze_segment = AsyncMock(return_value={
            "complexity": 0.7,
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.5
        })

        # Act
        result = await style_checker.batch_check(
            content=content,
            profile_id="test-profile"
        )

        # Assert
        assert "summary" in result
        summary = result["summary"]
        assert "total_issues" in summary
        assert "issues_by_severity" in summary
        assert "issues_by_type" in summary
        assert "overall_match_score" in summary
        assert isinstance(summary["total_issues"], int)
        assert isinstance(summary["overall_match_score"], float)

    @pytest.mark.asyncio
    async def test_batch_check_empty_content_raises_error(self, style_checker, style_profiler):
        """Test that batch check raises error for empty content."""
        # Act & Assert
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await style_checker.batch_check(
                content="",
                profile_id="test-profile"
            )

    @pytest.mark.asyncio
    async def test_batch_check_nonexistent_profile_raises_error(self, style_checker, style_profiler):
        """Test that batch check raises error for nonexistent profile."""
        # Arrange
        style_profiler.retrieve_profile.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Profile with ID .* not found"):
            await style_checker.batch_check(
                content="Some content",
                profile_id="nonexistent"
            )


class TestPerformanceSLA:
    """Tests for style checking performance requirements."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        profiler.analyze_segment = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self, style_profiler):
        """Create a StyleChecker instance for testing."""
        return StyleChecker(style_profiler=style_profiler)

    @pytest.mark.asyncio
    async def test_realtime_check_completes_under_1_second(self, style_checker, style_profiler):
        """Test that real-time check completes in under 1 second."""
        # Arrange
        text = "This is a sample text for performance testing. " * 50  # ~2500 chars
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        style_profiler.analyze_text.return_value = {
            "complexity": 0.6,
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.5
        }

        # Act
        start_time = time.time()
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result is not None
        assert elapsed_time < 1.0, f"Real-time check took {elapsed_time:.2f}s, exceeds 1s SLA"

    @pytest.mark.asyncio
    async def test_batch_check_completes_under_5_seconds(self, style_checker, style_profiler):
        """Test that batch check completes in reasonable time for typical content."""
        # Arrange
        # Simulate a document with ~10 paragraphs
        content = "\n\n".join([
            f"This is paragraph {i}. It contains several sentences for testing. More text here."
            for i in range(10)
        ])

        style_profiler.retrieve_profile.return_value = {
            "id": "test-profile",
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}
        }

        style_profiler.analyze_segment = AsyncMock(return_value={
            "complexity": 0.5,
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.5
        })

        # Act
        start_time = time.time()
        result = await style_checker.batch_check(
            content=content,
            profile_id="test-profile"
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result is not None
        assert elapsed_time < 5.0, f"Batch check took {elapsed_time:.2f}s, exceeds 5s SLA"

    @pytest.mark.asyncio
    async def test_realtime_check_includes_timing_metadata(self, style_checker, style_profiler):
        """Test that real-time check includes processing time in response."""
        # Arrange
        text = "Sample text for timing test."
        target_characteristics = {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}

        style_profiler.analyze_text.return_value = {
            "complexity": 0.5,
            "formality": 0.5,
            "tone": 0.5,
            "readability": 0.5
        }

        # Act
        result = await style_checker.check_realtime(
            text=text,
            target_characteristics=target_characteristics
        )

        # Assert
        assert result is not None
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], (int, float))
        assert result["processing_time_ms"] >= 0


class TestSeverityCalculation:
    """Tests for severity calculation logic."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler mock for testing."""
        profiler = MagicMock()
        profiler.retrieve_profile = AsyncMock()
        profiler.analyze_text = AsyncMock()
        return profiler

    @pytest.fixture
    def style_checker(self, style_profiler):
        """Create a StyleChecker instance for testing."""
        return StyleChecker(style_profiler=style_profiler)

    def test_calculate_deviation_severity_low(self, style_checker):
        """Test that small deviations are classified as low severity."""
        # Arrange
        deviation = 0.05  # 5% deviation

        # Act
        severity = style_checker.calculate_deviation_severity(deviation)

        # Assert
        assert severity["level"] == "low"
        assert severity["score"] < 0.3

    def test_calculate_deviation_severity_medium(self, style_checker):
        """Test that moderate deviations are classified as medium severity."""
        # Arrange
        deviation = 0.25  # 25% deviation

        # Act
        severity = style_checker.calculate_deviation_severity(deviation)

        # Assert
        assert severity["level"] == "medium"
        assert 0.3 <= severity["score"] < 0.6

    def test_calculate_deviation_severity_high(self, style_checker):
        """Test that large deviations are classified as high severity."""
        # Arrange
        deviation = 0.45  # 45% deviation

        # Act
        severity = style_checker.calculate_deviation_severity(deviation)

        # Assert
        assert severity["level"] == "high"
        assert 0.6 <= severity["score"] < 0.8

    def test_calculate_deviation_severity_critical(self, style_checker):
        """Test that very large deviations are classified as critical severity."""
        # Arrange
        deviation = 0.7  # 70% deviation

        # Act
        severity = style_checker.calculate_deviation_severity(deviation)

        # Assert
        assert severity["level"] == "critical"
        assert severity["score"] >= 0.8

    def test_aggregate_severity_for_multiple_deviations(self, style_checker):
        """Test aggregating severity across multiple deviation types."""
        # Arrange
        deviations = {
            "complexity": 0.3,   # Medium
            "formality": 0.5,    # High
            "tone": 0.1,         # Low
            "readability": 0.05  # Low
        }

        # Act
        aggregate = style_checker.aggregate_severity(deviations)

        # Assert
        assert "overall_level" in aggregate
        assert "overall_score" in aggregate
        assert "breakdown" in aggregate
        assert aggregate["overall_score"] > 0
        # Overall level should reflect the highest severity
        assert aggregate["overall_level"] in ["medium", "high"]
