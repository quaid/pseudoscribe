"""
Unit tests for VectorGenerator using ZeroDB embeddings.

Tests follow the AAA pattern (Arrange, Act, Assert) and verify:
1. Real embeddings are generated (not zeros)
2. Correct dimensionality (384 for BAAI/bge-small-en-v1.5)
3. Error handling for edge cases
4. ZeroDB MCP integration
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock
from pseudoscribe.infrastructure.vector_generator import VectorGenerator


class TestVectorGenerator:
    """Test suite for VectorGenerator with ZeroDB integration."""

    @pytest.fixture
    def mock_zerodb_func(self):
        """Create a mock ZeroDB embedding function with realistic data."""
        async def mock_func(texts, model):
            # Create a realistic 384-dimensional embedding (not zeros)
            embedding = np.random.randn(384).astype(np.float32)
            return {
                "embeddings": [embedding.tolist()],
                "model": model,
                "dimension": 384
            }
        return AsyncMock(side_effect=mock_func)

    @pytest.fixture
    def vector_generator(self, mock_zerodb_func):
        """Fixture for VectorGenerator instance with mocked MCP function."""
        return VectorGenerator(mcp_func=mock_zerodb_func)

    @pytest.mark.asyncio
    async def test_generate_returns_non_zero_embeddings(self, vector_generator):
        """
        AI-011: Verify VectorGenerator produces real embeddings, not zeros.

        Given: A VectorGenerator instance
        When: Generating embeddings for text
        Then: The returned vector should not be all zeros
        """
        # Arrange
        test_text = "Sample text for embedding generation"

        # Act
        await vector_generator.initialize()
        result = await vector_generator.generate(test_text)

        # Assert
        assert isinstance(result, np.ndarray), "Result should be numpy array"
        assert not np.allclose(result, 0), "Embeddings should not be all zeros"
        assert np.any(result != 0), "At least some values should be non-zero"

    @pytest.mark.asyncio
    async def test_generate_correct_dimensions(self, vector_generator):
        """
        AI-011: Verify embeddings have correct dimensionality (384).

        Given: A VectorGenerator using BAAI/bge-small-en-v1.5
        When: Generating embeddings
        Then: The vector should have 384 dimensions
        """
        # Arrange
        test_text = "Another sample text"

        # Act
        await vector_generator.initialize()
        result = await vector_generator.generate(test_text)

        # Assert
        assert result.shape == (384,), "Expected 384-dimensional vector"
        assert result.dtype == np.float32, "Expected float32 dtype"

    @pytest.mark.asyncio
    async def test_generate_no_nan_values(self, vector_generator):
        """
        AI-011: Verify embeddings do not contain NaN values.

        Given: A VectorGenerator instance
        When: Generating embeddings
        Then: The result should not contain any NaN values
        """
        # Arrange
        test_text = "Clean text without issues"

        # Act
        await vector_generator.initialize()
        result = await vector_generator.generate(test_text)

        # Assert
        assert not np.isnan(result).any(), "Vector should not contain NaN values"

    @pytest.mark.asyncio
    async def test_generate_empty_text_raises_error(self, vector_generator):
        """
        AI-011: Verify proper error handling for empty text.

        Given: A VectorGenerator instance
        When: Attempting to generate embeddings for empty text
        Then: A ValueError should be raised
        """
        # Arrange
        empty_text = ""

        # Act & Assert
        await vector_generator.initialize()
        with pytest.raises(ValueError, match="Cannot generate embeddings for empty text"):
            await vector_generator.generate(empty_text)

    @pytest.mark.asyncio
    async def test_generate_whitespace_only_raises_error(self, vector_generator):
        """
        AI-011: Verify proper error handling for whitespace-only text.

        Given: A VectorGenerator instance
        When: Attempting to generate embeddings for whitespace-only text
        Then: A ValueError should be raised
        """
        # Arrange
        whitespace_text = "   \t\n  "

        # Act & Assert
        await vector_generator.initialize()
        with pytest.raises(ValueError, match="Cannot generate embeddings for empty text"):
            await vector_generator.generate(whitespace_text)

    @pytest.mark.asyncio
    async def test_generate_uninitialized_raises_error(self):
        """
        AI-011: Verify error when generator is not initialized.

        Given: An uninitialized VectorGenerator
        When: Attempting to generate embeddings
        Then: A RuntimeError should be raised
        """
        # Arrange
        mock_func = AsyncMock()
        generator = VectorGenerator(mcp_func=mock_func)
        test_text = "Sample text"

        # Act & Assert
        with pytest.raises(RuntimeError, match="Vector generator not initialized"):
            await generator.generate(test_text)

    @pytest.mark.asyncio
    async def test_zerodb_mcp_called_with_correct_params(self, mock_zerodb_func):
        """
        AI-011: Verify ZeroDB MCP is called with correct parameters.

        Given: A VectorGenerator instance
        When: Generating embeddings
        Then: ZeroDB should be called with the correct model and text
        """
        # Arrange
        test_text = "Test text for verification"
        generator = VectorGenerator(mcp_func=mock_zerodb_func)

        # Act
        await generator.initialize()
        await generator.generate(test_text)

        # Assert
        mock_zerodb_func.assert_called_once()
        call_args = mock_zerodb_func.call_args
        assert call_args[1]["texts"] == [test_text]
        assert call_args[1]["model"] == "BAAI/bge-small-en-v1.5"

    @pytest.mark.asyncio
    async def test_generate_handles_zerodb_error(self):
        """
        AI-011: Verify graceful error handling when ZeroDB fails.

        Given: A VectorGenerator instance
        When: ZeroDB returns an error
        Then: A RuntimeError should be raised with a descriptive message
        """
        # Arrange
        test_text = "Sample text"
        mock_func = AsyncMock(side_effect=Exception("ZeroDB connection failed"))
        generator = VectorGenerator(mcp_func=mock_func)

        # Act & Assert
        await generator.initialize()
        with pytest.raises(
            RuntimeError,
            match="Failed to generate embeddings.*ZeroDB connection failed"
        ):
            await generator.generate(test_text)

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self):
        """
        AI-011: Verify initialization sets the initialized flag.

        Given: An uninitialized VectorGenerator
        When: Initializing the generator
        Then: The initialized flag should be True
        """
        # Arrange
        mock_func = AsyncMock()
        generator = VectorGenerator(mcp_func=mock_func)
        assert not generator.initialized

        # Act
        result = await generator.initialize()

        # Assert
        assert result is True
        assert generator.initialized is True

    @pytest.mark.asyncio
    async def test_generate_multiple_texts_consistency(self):
        """
        AI-011: Verify consistent behavior across multiple calls.

        Given: A VectorGenerator instance
        When: Generating embeddings multiple times
        Then: Each call should return valid embeddings
        """
        # Arrange
        texts = ["First text", "Second text", "Third text"]
        call_count = 0

        async def mock_func(texts, model):
            nonlocal call_count
            call_count += 1
            # Each call returns a different embedding
            embedding = np.random.randn(384).astype(np.float32)
            return {
                "embeddings": [embedding.tolist()],
                "model": model,
                "dimension": 384
            }

        generator = VectorGenerator(mcp_func=AsyncMock(side_effect=mock_func))

        # Act
        await generator.initialize()
        results = [await generator.generate(text) for text in texts]

        # Assert
        assert len(results) == 3
        assert call_count == 3
        for result in results:
            assert result.shape == (384,)
            assert not np.allclose(result, 0)
            assert not np.isnan(result).any()

    @pytest.mark.asyncio
    async def test_different_model_dimensions(self):
        """
        AI-011: Verify support for different embedding models.

        Given: VectorGenerator instances with different models
        When: Generating embeddings
        Then: Each should return the correct dimensionality
        """
        # Arrange & Act & Assert
        models_and_dims = [
            ("BAAI/bge-small-en-v1.5", 384),
            ("BAAI/bge-base-en-v1.5", 768),
            ("BAAI/bge-large-en-v1.5", 1024),
        ]

        for model_name, expected_dim in models_and_dims:
            async def mock_func(texts, model):
                embedding = np.random.randn(expected_dim).astype(np.float32)
                return {
                    "embeddings": [embedding.tolist()],
                    "model": model,
                    "dimension": expected_dim
                }

            generator = VectorGenerator(
                model_name=model_name,
                mcp_func=AsyncMock(side_effect=mock_func)
            )
            await generator.initialize()
            result = await generator.generate("Test text")

            assert result.shape == (expected_dim,), \
                f"Model {model_name} should produce {expected_dim}-dim vectors"

    @pytest.mark.asyncio
    async def test_generate_validates_response_dimension(self):
        """
        AI-011: Verify dimension validation of ZeroDB response.

        Given: A VectorGenerator instance
        When: ZeroDB returns wrong dimensionality
        Then: A RuntimeError should be raised
        """
        # Arrange
        test_text = "Sample text"

        async def mock_func(texts, model):
            # Return wrong dimension (768 instead of 384)
            embedding = np.random.randn(768).astype(np.float32)
            return {
                "embeddings": [embedding.tolist()],
                "model": model,
                "dimension": 768
            }

        generator = VectorGenerator(mcp_func=AsyncMock(side_effect=mock_func))

        # Act & Assert
        await generator.initialize()
        with pytest.raises(
            RuntimeError,
            match="Expected 384-dimensional embedding, got 768"
        ):
            await generator.generate(test_text)

    @pytest.mark.asyncio
    async def test_generate_handles_empty_response(self):
        """
        AI-011: Verify error handling for empty ZeroDB response.

        Given: A VectorGenerator instance
        When: ZeroDB returns empty embeddings
        Then: A RuntimeError should be raised
        """
        # Arrange
        test_text = "Sample text"

        async def mock_func(texts, model):
            return {"embeddings": [], "model": model, "dimension": 384}

        generator = VectorGenerator(mcp_func=AsyncMock(side_effect=mock_func))

        # Act & Assert
        await generator.initialize()
        with pytest.raises(RuntimeError, match="ZeroDB returned empty embeddings"):
            await generator.generate(test_text)

    @pytest.mark.asyncio
    async def test_generate_handles_missing_embeddings_key(self):
        """
        AI-011: Verify error handling for malformed ZeroDB response.

        Given: A VectorGenerator instance
        When: ZeroDB returns response without embeddings key
        Then: A RuntimeError should be raised
        """
        # Arrange
        test_text = "Sample text"

        async def mock_func(texts, model):
            return {"model": model, "dimension": 384}  # Missing "embeddings" key

        generator = VectorGenerator(mcp_func=AsyncMock(side_effect=mock_func))

        # Act & Assert
        await generator.initialize()
        with pytest.raises(RuntimeError, match="ZeroDB returned empty embeddings"):
            await generator.generate(test_text)

    @pytest.mark.asyncio
    async def test_no_mcp_function_raises_error(self):
        """
        AI-011: Verify error when no MCP function is available.

        Given: A VectorGenerator without MCP function
        When: Attempting to generate embeddings
        Then: A RuntimeError should be raised
        """
        # Arrange
        generator = VectorGenerator()  # No mcp_func provided
        test_text = "Sample text"

        # Act & Assert
        await generator.initialize()
        with pytest.raises(
            RuntimeError,
            match="No ZeroDB MCP function available"
        ):
            await generator.generate(test_text)
