"""Tests for style profile merging and multi-sample analysis.

Issue: AI-007 - Style Profiling

These tests verify:
- Weighted vector merging when updating profiles with new samples
- Sample count tracking for weight adjustments
- Multi-sample profile creation
- BDD scenario: Profile updates merge vectors and adjust weights
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List

from pseudoscribe.infrastructure.style_profiler import StyleProfiler


class TestProfileMerging:
    """Tests for profile merging functionality."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler instance for testing."""
        model_manager = MagicMock()
        return StyleProfiler(model_manager=model_manager)

    @pytest.mark.asyncio
    async def test_merge_profile_with_new_sample(self, style_profiler):
        """Test that merging a new sample updates the profile vector with weighted average."""
        # Arrange
        existing_profile = {
            "id": "test-profile",
            "name": "Test Profile",
            "vector": np.array([1.0, 0.0, 0.0]),
            "characteristics": {
                "complexity": 0.5,
                "formality": 0.5,
                "tone": 0.5,
                "readability": 0.5
            },
            "sample_count": 1,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        new_vector = np.array([0.0, 1.0, 0.0])
        new_characteristics = {
            "complexity": 0.7,
            "formality": 0.3,
            "tone": 0.6,
            "readability": 0.4
        }

        # Act
        merged_profile = style_profiler.merge_profile(
            existing_profile=existing_profile,
            new_vector=new_vector,
            new_characteristics=new_characteristics
        )

        # Assert
        assert merged_profile is not None
        assert merged_profile["sample_count"] == 2

        # Vector should be weighted average: (1*[1,0,0] + 1*[0,1,0]) / 2 = [0.5, 0.5, 0]
        expected_vector = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(merged_profile["vector"], expected_vector)

    @pytest.mark.asyncio
    async def test_merge_profile_weights_by_sample_count(self, style_profiler):
        """Test that merging respects existing sample count for weighting."""
        # Arrange - profile with 3 existing samples
        existing_profile = {
            "id": "test-profile",
            "name": "Test Profile",
            "vector": np.array([0.9, 0.0, 0.0]),
            "characteristics": {
                "complexity": 0.6,
                "formality": 0.6,
                "tone": 0.6,
                "readability": 0.6
            },
            "sample_count": 3,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        new_vector = np.array([0.0, 0.9, 0.0])
        new_characteristics = {
            "complexity": 0.2,
            "formality": 0.2,
            "tone": 0.2,
            "readability": 0.2
        }

        # Act
        merged_profile = style_profiler.merge_profile(
            existing_profile=existing_profile,
            new_vector=new_vector,
            new_characteristics=new_characteristics
        )

        # Assert
        assert merged_profile["sample_count"] == 4

        # Vector: (3*[0.9,0,0] + 1*[0,0.9,0]) / 4 = [0.675, 0.225, 0]
        expected_vector = np.array([0.675, 0.225, 0.0])
        np.testing.assert_array_almost_equal(merged_profile["vector"], expected_vector)

    @pytest.mark.asyncio
    async def test_merge_characteristics_weighted_average(self, style_profiler):
        """Test that characteristics are merged using weighted average."""
        # Arrange
        existing_profile = {
            "id": "test-profile",
            "name": "Test Profile",
            "vector": np.array([1.0, 0.0, 0.0]),
            "characteristics": {
                "complexity": 0.8,
                "formality": 0.6,
                "tone": 0.4,
                "readability": 0.5
            },
            "sample_count": 2,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        new_vector = np.array([0.0, 1.0, 0.0])
        new_characteristics = {
            "complexity": 0.2,
            "formality": 0.9,
            "tone": 0.7,
            "readability": 0.8
        }

        # Act
        merged_profile = style_profiler.merge_profile(
            existing_profile=existing_profile,
            new_vector=new_vector,
            new_characteristics=new_characteristics
        )

        # Assert - characteristics weighted: (2*existing + 1*new) / 3
        expected_complexity = (2 * 0.8 + 1 * 0.2) / 3  # 0.6
        expected_formality = (2 * 0.6 + 1 * 0.9) / 3  # 0.7
        expected_tone = (2 * 0.4 + 1 * 0.7) / 3  # 0.5
        expected_readability = (2 * 0.5 + 1 * 0.8) / 3  # 0.6

        assert abs(merged_profile["characteristics"]["complexity"] - expected_complexity) < 0.01
        assert abs(merged_profile["characteristics"]["formality"] - expected_formality) < 0.01
        assert abs(merged_profile["characteristics"]["tone"] - expected_tone) < 0.01
        assert abs(merged_profile["characteristics"]["readability"] - expected_readability) < 0.01

    @pytest.mark.asyncio
    async def test_merge_profile_updates_timestamp(self, style_profiler):
        """Test that merging updates the updated_at timestamp."""
        # Arrange
        existing_profile = {
            "id": "test-profile",
            "name": "Test Profile",
            "vector": np.array([1.0, 0.0, 0.0]),
            "characteristics": {
                "complexity": 0.5,
                "formality": 0.5,
                "tone": 0.5,
                "readability": 0.5
            },
            "sample_count": 1,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        # Act
        merged_profile = style_profiler.merge_profile(
            existing_profile=existing_profile,
            new_vector=np.array([0.0, 1.0, 0.0]),
            new_characteristics={"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5}
        )

        # Assert
        assert merged_profile["created_at"] == "2025-01-01T00:00:00Z"  # Preserved
        assert merged_profile["updated_at"] != "2025-01-01T00:00:00Z"  # Updated


class TestMultiSampleProfileCreation:
    """Tests for creating profiles from multiple writing samples."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler instance for testing."""
        model_manager = MagicMock()
        return StyleProfiler(model_manager=model_manager)

    @pytest.mark.asyncio
    async def test_create_profile_from_multiple_samples(self, style_profiler):
        """Test creating a profile from multiple writing samples."""
        # Arrange
        samples = [
            "This is the first writing sample. It demonstrates a particular style.",
            "Here is another sample with slightly different characteristics.",
            "A third sample to help establish the overall style profile."
        ]

        # Mock vector generation for each sample
        mock_vectors = [
            np.array([0.9, 0.1, 0.0]),
            np.array([0.8, 0.2, 0.0]),
            np.array([0.85, 0.15, 0.0])
        ]
        style_profiler.model_manager.generate_vectors = AsyncMock(
            side_effect=mock_vectors
        )

        # Act
        profile = await style_profiler.create_profile_from_samples(
            samples=samples,
            profile_name="Multi-Sample Profile"
        )

        # Assert
        assert profile is not None
        assert profile["name"] == "Multi-Sample Profile"
        assert profile["sample_count"] == 3
        assert "vector" in profile
        assert "characteristics" in profile

    @pytest.mark.asyncio
    async def test_create_profile_averages_vectors(self, style_profiler):
        """Test that multi-sample profile averages the vectors."""
        # Arrange
        samples = ["Sample one", "Sample two"]

        mock_vectors = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0])
        ]
        style_profiler.model_manager.generate_vectors = AsyncMock(
            side_effect=mock_vectors
        )

        # Act
        profile = await style_profiler.create_profile_from_samples(
            samples=samples,
            profile_name="Averaged Profile"
        )

        # Assert
        expected_vector = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(profile["vector"], expected_vector)

    @pytest.mark.asyncio
    async def test_create_profile_empty_samples_raises_error(self, style_profiler):
        """Test that creating a profile with no samples raises an error."""
        # Act & Assert
        with pytest.raises(ValueError, match="At least one sample is required"):
            await style_profiler.create_profile_from_samples(
                samples=[],
                profile_name="Empty Profile"
            )

    @pytest.mark.asyncio
    async def test_create_profile_averages_characteristics(self, style_profiler):
        """Test that multi-sample profile averages characteristics."""
        # Arrange
        samples = ["Sample one", "Sample two"]

        mock_vectors = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0])
        ]
        style_profiler.model_manager.generate_vectors = AsyncMock(
            side_effect=mock_vectors
        )

        # Act
        profile = await style_profiler.create_profile_from_samples(
            samples=samples,
            profile_name="Characteristics Test"
        )

        # Assert - characteristics should be present and valid
        assert "characteristics" in profile
        assert 0 <= profile["characteristics"]["complexity"] <= 1
        assert 0 <= profile["characteristics"]["formality"] <= 1
        assert 0 <= profile["characteristics"]["tone"] <= 1
        assert 0 <= profile["characteristics"]["readability"] <= 1


class TestProfileUpdateWithNewSample:
    """Tests for updating existing profiles with new writing samples."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler instance for testing."""
        model_manager = MagicMock()
        return StyleProfiler(model_manager=model_manager)

    @pytest.mark.asyncio
    async def test_update_profile_with_sample_text(self, style_profiler):
        """Test updating a profile with a new text sample."""
        # Arrange
        existing_profile = {
            "id": "test-profile",
            "name": "Test Profile",
            "vector": np.array([1.0, 0.0, 0.0]),
            "characteristics": {
                "complexity": 0.5,
                "formality": 0.5,
                "tone": 0.5,
                "readability": 0.5
            },
            "sample_count": 1,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        new_sample = "This is a new writing sample to update the profile."
        new_vector = np.array([0.0, 1.0, 0.0])

        style_profiler.model_manager.generate_vectors = AsyncMock(
            return_value=new_vector
        )

        # Act
        updated_profile = await style_profiler.update_profile_with_sample(
            profile=existing_profile,
            sample_text=new_sample
        )

        # Assert
        assert updated_profile is not None
        assert updated_profile["sample_count"] == 2
        # Vector should be merged
        np.testing.assert_array_almost_equal(
            updated_profile["vector"],
            np.array([0.5, 0.5, 0.0])
        )

    @pytest.mark.asyncio
    async def test_update_profile_preserves_id(self, style_profiler):
        """Test that updating preserves the profile ID."""
        # Arrange
        existing_profile = {
            "id": "original-id-123",
            "name": "Test Profile",
            "vector": np.array([1.0, 0.0, 0.0]),
            "characteristics": {
                "complexity": 0.5,
                "formality": 0.5,
                "tone": 0.5,
                "readability": 0.5
            },
            "sample_count": 1,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        style_profiler.model_manager.generate_vectors = AsyncMock(
            return_value=np.array([0.0, 1.0, 0.0])
        )

        # Act
        updated_profile = await style_profiler.update_profile_with_sample(
            profile=existing_profile,
            sample_text="New sample text"
        )

        # Assert
        assert updated_profile["id"] == "original-id-123"

    @pytest.mark.asyncio
    async def test_update_profile_empty_text_raises_error(self, style_profiler):
        """Test that updating with empty text raises an error."""
        # Arrange
        existing_profile = {
            "id": "test-profile",
            "name": "Test Profile",
            "vector": np.array([1.0, 0.0, 0.0]),
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5},
            "sample_count": 1,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Sample text cannot be empty"):
            await style_profiler.update_profile_with_sample(
                profile=existing_profile,
                sample_text=""
            )


class TestVectorNormalization:
    """Tests for vector normalization in profile operations."""

    @pytest.fixture
    def style_profiler(self):
        """Create a StyleProfiler instance for testing."""
        model_manager = MagicMock()
        return StyleProfiler(model_manager=model_manager)

    def test_normalize_vector(self, style_profiler):
        """Test that vectors are normalized to unit length."""
        # Arrange
        vector = np.array([3.0, 4.0, 0.0])  # Length = 5

        # Act
        normalized = style_profiler.normalize_vector(vector)

        # Assert
        expected = np.array([0.6, 0.8, 0.0])
        np.testing.assert_array_almost_equal(normalized, expected)
        # Verify unit length
        assert abs(np.linalg.norm(normalized) - 1.0) < 0.0001

    def test_normalize_zero_vector_returns_zero(self, style_profiler):
        """Test that normalizing a zero vector returns zero vector."""
        # Arrange
        zero_vector = np.array([0.0, 0.0, 0.0])

        # Act
        normalized = style_profiler.normalize_vector(zero_vector)

        # Assert
        np.testing.assert_array_equal(normalized, zero_vector)
