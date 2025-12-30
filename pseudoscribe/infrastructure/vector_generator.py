"""Vector embedding generator using ZeroDB embeddings.

This module provides the VectorGenerator class that integrates with ZeroDB's
embedding service to generate real vector embeddings for text. Replaces the
placeholder implementation that returned zero-filled arrays.

Issue: AI-011 - Replace VectorGenerator with ZeroDB Embeddings
"""

import numpy as np
from typing import List, Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


# Placeholder for the MCP function - will be set at runtime or mocked in tests
_mcp_generate_embeddings: Optional[Callable] = None


def set_mcp_embeddings_function(func: Callable) -> None:
    """Set the MCP embeddings function for dependency injection.

    Args:
        func: The MCP embeddings function to use
    """
    global _mcp_generate_embeddings
    _mcp_generate_embeddings = func


class VectorGenerator:
    """Vector embedding generator using ZeroDB's embedding service.

    This class handles the generation of vector embeddings from text using
    ZeroDB's MCP tools with the BAAI/bge-small-en-v1.5 model (384 dimensions).

    Attributes:
        model_name: The embedding model to use (default: BAAI/bge-small-en-v1.5)
        dimension: Expected embedding dimension (384 for the default model)
        initialized: Whether the generator has been initialized
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        mcp_func: Optional[Callable] = None
    ):
        """Initialize the vector generator with specified model.

        Args:
            model_name: Name of the ZeroDB embedding model to use.
                       Options: BAAI/bge-small-en-v1.5 (384-dim, default),
                               BAAI/bge-base-en-v1.5 (768-dim),
                               BAAI/bge-large-en-v1.5 (1024-dim)
            mcp_func: Optional MCP function for dependency injection (for testing)
        """
        self.model_name = model_name
        self.dimension = self._get_model_dimension(model_name)
        self.initialized = False
        self._mcp_func = mcp_func

    def _get_model_dimension(self, model_name: str) -> int:
        """Get the embedding dimension for a given model.

        Args:
            model_name: Name of the embedding model

        Returns:
            int: Embedding dimension
        """
        model_dimensions = {
            "BAAI/bge-small-en-v1.5": 384,
            "BAAI/bge-base-en-v1.5": 768,
            "BAAI/bge-large-en-v1.5": 1024,
        }
        return model_dimensions.get(model_name, 384)

    async def initialize(self) -> bool:
        """Initialize the vector generator.

        Returns:
            bool: True if initialization succeeded, False otherwise.
        """
        try:
            logger.info(f"Initializing vector generator with model: {self.model_name}")
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize vector generator: {str(e)}")
            return False

    async def generate(self, text: str) -> np.ndarray:
        """Generate vector embeddings from input text using ZeroDB.

        Args:
            text: Input text to vectorize

        Returns:
            np.ndarray: Embedding vector (384-dimensional for default model)

        Raises:
            RuntimeError: If the generator is not initialized or ZeroDB fails
            ValueError: If the input text is empty or whitespace-only
        """
        if not self.initialized:
            raise RuntimeError("Vector generator not initialized")

        # Validate input
        if not text or not text.strip():
            raise ValueError("Cannot generate embeddings for empty text")

        try:
            logger.info(f"Generating vector for text: {text[:50]}...")

            # Get the MCP function (from instance, global, or import)
            mcp_func = self._get_mcp_function()

            # Call ZeroDB to generate embeddings
            response = await mcp_func(
                texts=[text],
                model=self.model_name
            )

            # Extract the embedding from the response
            if "embeddings" not in response or len(response["embeddings"]) == 0:
                raise RuntimeError("ZeroDB returned empty embeddings")

            embedding = response["embeddings"][0]

            # Convert to numpy array
            embedding_array = np.array(embedding, dtype=np.float32)

            # Validate the embedding
            if embedding_array.shape[0] != self.dimension:
                raise RuntimeError(
                    f"Expected {self.dimension}-dimensional embedding, "
                    f"got {embedding_array.shape[0]}"
                )

            logger.info(f"Successfully generated {self.dimension}-dimensional embedding")
            return embedding_array

        except ValueError:
            # Re-raise ValueError for empty text
            raise
        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _get_mcp_function(self) -> Callable:
        """Get the MCP embeddings function.

        Returns:
            Callable: The MCP embeddings function

        Raises:
            RuntimeError: If no MCP function is available
        """
        # Priority: instance > global > import
        if self._mcp_func is not None:
            return self._mcp_func

        if _mcp_generate_embeddings is not None:
            return _mcp_generate_embeddings

        # Try to import the actual MCP function
        try:
            # This import path would need to be adjusted based on how MCP tools
            # are made available in the production environment
            from mcp import zerodb
            return zerodb.zerodb_generate_embeddings
        except ImportError:
            pass

        raise RuntimeError(
            "No ZeroDB MCP function available. "
            "Ensure the ZeroDB MCP server is running or inject the function for testing."
        )
