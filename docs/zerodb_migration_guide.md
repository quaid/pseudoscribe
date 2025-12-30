# Migration Guide: VectorStore to ZeroDB Service

## Overview

This guide helps migrate from the in-memory `VectorStore` to the persistent `ZeroDBService`.

## Quick Comparison

| Feature | Old VectorStore | New ZeroDBService |
|---------|----------------|-------------------|
| Storage | In-memory (numpy) | Persistent (ZeroDB) |
| Initialization | `VectorStore()` | `ZeroDBService.get_instance()` |
| Add Vector | `add_vector(id, vector)` | `upsert_vector(vector, document, metadata)` |
| Search | `find_similar(query_vector, top_k)` | `search_vectors(query_vector, limit)` |
| Persistence | ❌ Lost on restart | ✅ Persistent |
| Multi-tenant | ❌ Not supported | ✅ Namespace isolation |
| Metadata | ❌ Not supported | ✅ Full metadata support |
| Embeddings | External | Built-in generation |

## Migration Steps

### Step 1: Update Imports

**Before:**
```python
from pseudoscribe.infrastructure.vector_store import VectorStore
```

**After:**
```python
from pseudoscribe.infrastructure.zerodb_service import (
    ZeroDBService,
    ZeroDBError
)
```

### Step 2: Initialize Service

**Before:**
```python
vector_store = VectorStore()
vector_store.initialize()
```

**After:**
```python
service = ZeroDBService.get_instance()
# Already initialized automatically
```

### Step 3: Add Vectors

**Before:**
```python
import numpy as np

vector = np.array([0.1, 0.2, 0.3, ...])
success = vector_store.add_vector("vec_123", vector)
```

**After:**
```python
vector = [0.1, 0.2, 0.3, ...]  # Can be list or numpy array
vector_id = await service.upsert_vector(
    vector=vector,
    document="Original text content",
    metadata={
        "tenant_id": "tenant-123",
        "type": "style_profile"
    },
    namespace="tenant-123"
)
```

### Step 4: Search Vectors

**Before:**
```python
query_vector = np.array([0.15, 0.25, 0.35, ...])
results = vector_store.find_similar(
    query_vector=query_vector,
    top_k=5,
    threshold=0.7
)

for result in results:
    vector_id = result["id"]
    score = result["score"]
```

**After:**
```python
query_vector = [0.15, 0.25, 0.35, ...]
results = await service.search_vectors(
    query_vector=query_vector,
    limit=5,
    namespace="tenant-123",
    threshold=0.7
)

for result in results:
    vector_id = result["vector_id"]
    score = result["score"]
    document = result["document"]  # Original text!
    metadata = result["metadata"]
```

### Step 5: Get Vector by ID

**Before:**
```python
vector = vector_store.get_vector("vec_123")
if vector is not None:
    # Use vector
```

**After:**
```python
# Not directly supported, but can search by metadata
results = await service.search_vectors(
    query_vector=vector,  # Use the vector itself
    limit=1,
    namespace="tenant-123",
    filter_metadata={"original_id": "vec_123"}
)
```

## Code Examples

### Example 1: Style Profile Storage

**Before:**
```python
class StyleProfiler:
    def __init__(self):
        self.vector_store = VectorStore()
        self.vector_store.initialize()

    def store_profile(self, user_id: str, style_vector: np.ndarray):
        vector_id = f"style_{user_id}"
        self.vector_store.add_vector(vector_id, style_vector)

    def find_similar_styles(self, query_vector: np.ndarray, top_k: int = 5):
        return self.vector_store.find_similar(query_vector, top_k)
```

**After:**
```python
class StyleProfiler:
    def __init__(self):
        self.service = ZeroDBService.get_instance()

    async def store_profile(
        self,
        user_id: str,
        style_vector: list,
        tenant_id: str,
        sample_text: str
    ):
        vector_id = await self.service.upsert_vector(
            vector=style_vector,
            document=sample_text,
            metadata={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "type": "style_profile",
                "created_at": datetime.utcnow().isoformat()
            },
            namespace=tenant_id
        )
        return vector_id

    async def find_similar_styles(
        self,
        query_vector: list,
        tenant_id: str,
        top_k: int = 5
    ):
        results = await self.service.search_vectors(
            query_vector=query_vector,
            limit=top_k,
            namespace=tenant_id,
            threshold=0.7,
            filter_metadata={"type": "style_profile"}
        )
        return results
```

### Example 2: Document Similarity

**Before:**
```python
def add_document(doc_id: str, embedding: np.ndarray):
    vector_store.add_vector(doc_id, embedding)

def find_similar_documents(query_embedding: np.ndarray):
    return vector_store.find_similar(query_embedding, top_k=10)
```

**After:**
```python
async def add_document(
    doc_id: str,
    embedding: list,
    document_text: str,
    tenant_id: str,
    metadata: dict = None
):
    meta = metadata or {}
    meta.update({
        "doc_id": doc_id,
        "tenant_id": tenant_id
    })

    vector_id = await service.upsert_vector(
        vector=embedding,
        document=document_text,
        metadata=meta,
        namespace=tenant_id
    )
    return vector_id

async def find_similar_documents(
    query_embedding: list,
    tenant_id: str,
    limit: int = 10
):
    results = await service.search_vectors(
        query_vector=query_embedding,
        limit=limit,
        namespace=tenant_id,
        threshold=0.7
    )
    return results
```

## Batch Migration Script

### Migrate Existing Data

```python
import asyncio
import numpy as np
from pseudoscribe.infrastructure.vector_store import VectorStore
from pseudoscribe.infrastructure.zerodb_service import ZeroDBService

async def migrate_vectors(tenant_id: str):
    """Migrate vectors from VectorStore to ZeroDBService"""

    # Old store
    old_store = VectorStore()
    old_store.initialize()

    # New service
    service = ZeroDBService.get_instance()

    # Migrate each vector
    migrated = 0
    for vector_id, vector in old_store.vectors.items():
        try:
            # Convert numpy array to list
            vector_list = vector.tolist() if isinstance(vector, np.ndarray) else vector

            # Store in ZeroDB
            new_id = await service.upsert_vector(
                vector=vector_list,
                document=f"Migrated from old store: {vector_id}",
                metadata={
                    "old_id": vector_id,
                    "tenant_id": tenant_id,
                    "migrated": True,
                    "migration_date": datetime.utcnow().isoformat()
                },
                namespace=tenant_id
            )

            migrated += 1
            print(f"Migrated {vector_id} -> {new_id}")

        except Exception as e:
            print(f"Failed to migrate {vector_id}: {e}")

    print(f"Migration complete: {migrated} vectors migrated")

# Run migration
asyncio.run(migrate_vectors("tenant-123"))
```

## Testing Migration

### Unit Test Update

**Before:**
```python
def test_vector_storage():
    store = VectorStore()
    store.initialize()

    vector = np.array([0.1, 0.2, 0.3])
    store.add_vector("test_1", vector)

    retrieved = store.get_vector("test_1")
    assert retrieved is not None
    np.testing.assert_array_equal(retrieved, vector)
```

**After:**
```python
@pytest.mark.asyncio
async def test_vector_storage(mock_mcp_upsert):
    mock_mcp_upsert.return_value = {"vector_id": "vec_123"}

    service = ZeroDBService.get_instance()

    vector = [0.1, 0.2, 0.3]
    vector_id = await service.upsert_vector(
        vector=vector,
        document="Test document",
        metadata={"test": True},
        namespace="test"
    )

    assert vector_id == "vec_123"
```

## Common Pitfalls

### 1. Forgetting async/await

**Wrong:**
```python
vector_id = service.upsert_vector(vector, document, metadata)
```

**Correct:**
```python
vector_id = await service.upsert_vector(vector, document, metadata)
```

### 2. Not Using Namespaces

**Wrong:**
```python
# All tenants share the same namespace
vector_id = await service.upsert_vector(
    vector=vector,
    document=doc,
    metadata={"tenant_id": tenant_id}
)
```

**Correct:**
```python
# Each tenant has isolated namespace
vector_id = await service.upsert_vector(
    vector=vector,
    document=doc,
    metadata={"tenant_id": tenant_id},
    namespace=tenant_id  # Isolates data
)
```

### 3. Missing Document Text

**Wrong:**
```python
# Document text is empty or generic
vector_id = await service.upsert_vector(
    vector=vector,
    document="",  # Empty!
    metadata=metadata
)
```

**Correct:**
```python
# Store the actual source text
vector_id = await service.upsert_vector(
    vector=vector,
    document=original_text,  # Actual content
    metadata=metadata
)
```

### 4. Not Converting NumPy Arrays

**Wrong:**
```python
import numpy as np
vector = np.array([0.1, 0.2, 0.3])
vector_id = await service.upsert_vector(
    vector=vector,  # NumPy array might cause issues
    document=doc,
    metadata=metadata
)
```

**Correct:**
```python
import numpy as np
vector = np.array([0.1, 0.2, 0.3])
vector_id = await service.upsert_vector(
    vector=vector.tolist(),  # Convert to list
    document=doc,
    metadata=metadata
)
```

## Benefits of Migration

### 1. Persistence
- ✅ Data survives restarts
- ✅ No data loss
- ✅ Automatic backups (via ZeroDB)

### 2. Multi-Tenant Support
- ✅ Namespace isolation
- ✅ Tenant-specific searches
- ✅ Secure data separation

### 3. Metadata
- ✅ Rich metadata support
- ✅ Filterable searches
- ✅ Document text storage

### 4. Scalability
- ✅ Handle millions of vectors
- ✅ Distributed storage
- ✅ Efficient indexing

### 5. Advanced Features
- ✅ Semantic search (text-to-text)
- ✅ Embedding generation
- ✅ Batch operations
- ✅ PostgreSQL integration

## Rollback Plan

If you need to rollback:

1. **Keep old VectorStore code** in a separate branch
2. **Test migration thoroughly** before production
3. **Maintain both systems temporarily** during transition
4. **Export data** from ZeroDB if needed:

```python
async def export_vectors(namespace: str):
    """Export vectors from ZeroDB"""
    results = await service.search_vectors(
        query_vector=[0.0] * 384,  # Dummy vector
        limit=10000,
        namespace=namespace,
        threshold=0.0  # Get all vectors
    )

    # Save to file
    with open(f"export_{namespace}.json", "w") as f:
        json.dump(results, f, indent=2)
```

## Support

For migration issues:
1. Check test suite: `tests/infrastructure/test_zerodb_service.py`
2. Review examples: `examples/zerodb_integration_example.py`
3. Read full docs: `docs/zerodb_service.md`
4. Open issue in GitHub repository

## Timeline

Recommended migration timeline:

1. **Week 1**: Test ZeroDB service in development
2. **Week 2**: Migrate non-critical features
3. **Week 3**: Run parallel systems for comparison
4. **Week 4**: Full migration to ZeroDB
5. **Week 5**: Remove old VectorStore code

## Checklist

- [ ] Read ZeroDB service documentation
- [ ] Update imports in all files
- [ ] Convert synchronous code to async
- [ ] Add namespace parameters for multi-tenancy
- [ ] Store document text with vectors
- [ ] Update unit tests with mocks
- [ ] Run integration tests
- [ ] Migrate existing data
- [ ] Update API endpoints
- [ ] Monitor performance
- [ ] Remove old VectorStore references
