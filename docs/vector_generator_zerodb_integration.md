# VectorGenerator ZeroDB Integration Guide

**Issue**: AI-011 - Replace VectorGenerator with ZeroDB Embeddings
**Date**: 2025-12-29
**Status**: Implementation Complete

## Overview

The `VectorGenerator` class has been updated to use ZeroDB's embedding service instead of returning zero-filled placeholder arrays. This enables real RAG (Retrieval-Augmented Generation) functionality.

## Changes Made

### 1. Updated Vector Generator (`pseudoscribe/infrastructure/vector_generator.py`)

**Key Changes**:
- Integrated ZeroDB MCP embedding service
- Uses `BAAI/bge-small-en-v1.5` model (384 dimensions) by default
- Supports multiple embedding models (384-dim, 768-dim, 1024-dim)
- Dependency injection pattern for testability
- Comprehensive error handling

**Features**:
- Real embeddings (not zeros)
- Input validation (empty text, whitespace)
- Dimension validation
- Graceful error handling

### 2. Comprehensive Test Suite (`tests/infrastructure/test_vector_generator.py`)

**Test Coverage**:
- Non-zero embedding verification
- Correct dimensionality (384 for default model)
- No NaN values
- Empty/whitespace text error handling
- Uninitialized generator error handling
- ZeroDB MCP integration verification
- Multiple model support
- Error handling for malformed responses
- Multiple call consistency

**Test Pattern**: Uses dependency injection with mocked MCP functions for isolation.

## Usage

### Basic Usage (Production)

```python
from pseudoscribe.infrastructure.vector_generator import VectorGenerator

# Create generator with default model (BAAI/bge-small-en-v1.5, 384-dim)
generator = VectorGenerator()

# Initialize
await generator.initialize()

# Generate embeddings
text = "Sample writing style to analyze"
embedding = await generator.generate(text)

# embedding is a numpy array of shape (384,) with float32 dtype
print(embedding.shape)  # (384,)
print(embedding.dtype)  # float32
```

### Using Different Models

```python
# Use larger model for better quality (768 dimensions)
generator = VectorGenerator(model_name="BAAI/bge-base-en-v1.5")
await generator.initialize()
embedding = await generator.generate(text)
print(embedding.shape)  # (768,)

# Use largest model (1024 dimensions)
generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")
await generator.initialize()
embedding = await generator.generate(text)
print(embedding.shape)  # (1024,)
```

### Testing Usage

```python
from unittest.mock import AsyncMock
import numpy as np

# Create mock MCP function
async def mock_embeddings(texts, model):
    embedding = np.random.randn(384).astype(np.float32)
    return {
        "embeddings": [embedding.tolist()],
        "model": model,
        "dimension": 384
    }

# Inject mock for testing
generator = VectorGenerator(mcp_func=AsyncMock(side_effect=mock_embeddings))
await generator.initialize()
result = await generator.generate("test text")
```

## Production Integration

### Wiring ZeroDB MCP Function

The implementation expects the ZeroDB MCP function to be available. There are three ways to provide it:

#### Option 1: Constructor Injection (Recommended for Testing)
```python
from mcp.zerodb import zerodb_generate_embeddings

generator = VectorGenerator(mcp_func=zerodb_generate_embeddings)
```

#### Option 2: Global Function (Recommended for Production)
```python
from pseudoscribe.infrastructure.vector_generator import set_mcp_embeddings_function
from mcp.zerodb import zerodb_generate_embeddings

# Set globally at application startup
set_mcp_embeddings_function(zerodb_generate_embeddings)

# Now all VectorGenerator instances will use it
generator = VectorGenerator()
```

#### Option 3: Import Fallback (Automatic)
The implementation will attempt to import from `mcp.zerodb` automatically if no function is provided.

### Error Handling

```python
from pseudoscribe.infrastructure.vector_generator import VectorGenerator

generator = VectorGenerator()
await generator.initialize()

try:
    # Empty text raises ValueError
    embedding = await generator.generate("")
except ValueError as e:
    print(f"Input validation error: {e}")

try:
    # ZeroDB errors wrapped in RuntimeError
    embedding = await generator.generate("valid text")
except RuntimeError as e:
    print(f"Embedding generation failed: {e}")
```

## Model Specifications

| Model | Dimensions | Performance | Use Case |
|-------|------------|-------------|----------|
| `BAAI/bge-small-en-v1.5` | 384 | Fast | Real-time style analysis, quick searches |
| `BAAI/bge-base-en-v1.5` | 768 | Balanced | General purpose RAG |
| `BAAI/bge-large-en-v1.5` | 1024 | High quality | Precise style matching, high-stakes use cases |

## Migration from Old Implementation

### Before (Zero-filled arrays)
```python
generator = VectorGenerator()
await generator.initialize()
embedding = await generator.generate("text")
# Returns: np.zeros(768, dtype=np.float32)
```

### After (Real embeddings)
```python
generator = VectorGenerator()  # Now uses 384-dim by default
await generator.initialize()
embedding = await generator.generate("text")
# Returns: Real 384-dim embedding from ZeroDB
```

**Breaking Changes**:
- Default dimension changed from 768 to 384
- Requires ZeroDB MCP server to be running
- Empty/whitespace text now raises `ValueError` instead of returning zeros

## Running Tests

```bash
# Run all VectorGenerator tests
pytest tests/infrastructure/test_vector_generator.py -v

# Run specific test
pytest tests/infrastructure/test_vector_generator.py::TestVectorGenerator::test_generate_returns_non_zero_embeddings -v

# Run with coverage
pytest tests/infrastructure/test_vector_generator.py --cov=pseudoscribe.infrastructure.vector_generator
```

## Acceptance Criteria

- [x] VectorGenerator produces real embeddings (not zeros)
- [x] Embeddings have 384 dimensions (default model)
- [x] Unit tests pass with mocked ZeroDB calls
- [x] Code follows PEP 8 and project conventions
- [x] Comprehensive error handling
- [x] Type hints on all functions
- [x] Clear documentation

## Next Steps

1. **Integration Testing**: Test with actual ZeroDB MCP server
2. **Performance Testing**: Benchmark embedding generation speed
3. **Cache Layer**: Consider caching frequently-requested embeddings
4. **Batch Processing**: Add batch embedding generation for efficiency
5. **Update ModelManager**: Wire VectorGenerator into existing ModelManager

## Related Files

- `/home/quaid/Documents/Projects/pseudoscribe/pseudoscribe/infrastructure/vector_generator.py`
- `/home/quaid/Documents/Projects/pseudoscribe/tests/infrastructure/test_vector_generator.py`
- `/home/quaid/Documents/Projects/pseudoscribe/tests/infrastructure/test_vector_generation.py` (may need updating)

## References

- [ZeroDB MCP Documentation](https://zerodb.ai/docs/mcp)
- [BAAI/bge Models](https://huggingface.co/BAAI)
- [GitHub Issue #91](https://github.com/quaid/pseudoscribe/issues/91)
