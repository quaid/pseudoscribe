# ZeroDB Service Quick Reference

## Import
```python
from pseudoscribe.infrastructure.zerodb_service import (
    ZeroDBService,
    ZeroDBError,
    ZeroDBConnectionError,
    ZeroDBQueryError
)
```

## Get Instance
```python
service = ZeroDBService.get_instance()
```

## PostgreSQL

### Execute Query
```python
result = await service.execute_query(
    "SELECT * FROM users WHERE tenant_id = $1",
    params=["tenant-123"],
    tenant_id="tenant-123"
)
```

### Get Schema
```python
schema = await service.get_schema_info(table_name="users")
```

### Create Table
```python
columns = [
    {"name": "id", "type": "SERIAL PRIMARY KEY"},
    {"name": "tenant_id", "type": "VARCHAR(255)"},
    {"name": "content", "type": "TEXT"}
]
result = await service.create_table("documents", columns)
```

## Vectors

### Generate Embeddings
```python
embeddings = await service.generate_embeddings(
    texts=["text1", "text2"],
    model="BAAI/bge-small-en-v1.5"
)
```

### Store Vector
```python
vector_id = await service.upsert_vector(
    vector=embedding,
    document="Document text",
    metadata={"tenant_id": "tenant-123"},
    namespace="tenant-123"
)
```

### Search Vectors
```python
results = await service.search_vectors(
    query_vector=embedding,
    limit=10,
    namespace="tenant-123",
    threshold=0.7
)
```

### Semantic Search
```python
results = await service.semantic_search(
    query_text="search query",
    limit=10,
    namespace="tenant-123"
)
```

### Embed and Store
```python
vector_ids = await service.embed_and_store(
    texts=["text1", "text2"],
    namespace="tenant-123",
    metadata={"type": "content"}
)
```

## NoSQL Tables

### Create Table
```python
schema = {
    "fields": {
        "user_id": {"type": "string"},
        "data": {"type": "object"}
    },
    "indexes": ["user_id"]
}
result = await service.create_nosql_table("table_name", schema)
```

### Insert Rows
```python
rows = [{"user_id": "123", "data": {...}}]
result = await service.insert_rows("table_name", rows)
```

### Query Rows
```python
result = await service.query_rows(
    "table_name",
    filter={"user_id": "123"},
    limit=10
)
```

## Error Handling
```python
try:
    result = await service.execute_query(sql)
except ZeroDBQueryError as e:
    logger.error(f"Query failed: {e}")
except ZeroDBConnectionError as e:
    logger.error(f"Connection failed: {e}")
except ZeroDBError as e:
    logger.error(f"General error: {e}")
```

## Multi-Tenant Patterns

### PostgreSQL
```python
# Include tenant_id in WHERE clause
result = await service.execute_query(
    "SELECT * FROM docs WHERE tenant_id = $1",
    params=["tenant-123"],
    tenant_id="tenant-123"
)
```

### Vectors
```python
# Use namespace for isolation
vector_id = await service.upsert_vector(
    vector=embedding,
    document=text,
    metadata={"tenant_id": "tenant-123"},
    namespace="tenant-123"  # Tenant-specific
)

results = await service.search_vectors(
    query_vector=query,
    namespace="tenant-123"  # Only this tenant
)
```

## Embedding Models

| Model | Dimensions | Use Case |
|-------|-----------|----------|
| `BAAI/bge-small-en-v1.5` | 384 | Fast, real-time |
| `BAAI/bge-base-en-v1.5` | 768 | Balanced |
| `BAAI/bge-large-en-v1.5` | 1024 | High quality |

## Common Patterns

### Store Document with Embedding
```python
# 1. Generate embedding
embeddings = await service.generate_embeddings([document])

# 2. Store vector
vector_id = await service.upsert_vector(
    vector=embeddings[0],
    document=document,
    metadata={"tenant_id": tenant_id, "type": "doc"},
    namespace=tenant_id
)

# 3. Store metadata in PostgreSQL
await service.execute_query(
    "INSERT INTO documents (vector_id, title, tenant_id) VALUES ($1, $2, $3)",
    params=[vector_id, title, tenant_id],
    tenant_id=tenant_id
)
```

### Find Similar Documents
```python
# 1. Generate query embedding
query_embeddings = await service.generate_embeddings([query_text])

# 2. Search vectors
results = await service.search_vectors(
    query_vector=query_embeddings[0],
    limit=5,
    namespace=tenant_id,
    threshold=0.7
)

# 3. Fetch full documents
for result in results:
    vector_id = result['vector_id']
    doc = await service.execute_query(
        "SELECT * FROM documents WHERE vector_id = $1 AND tenant_id = $2",
        params=[vector_id, tenant_id],
        tenant_id=tenant_id
    )
```

### Batch Processing
```python
# Batch embed and store
texts = ["doc1", "doc2", "doc3", ...]
vector_ids = await service.embed_and_store(
    texts=texts,
    namespace=tenant_id,
    metadata={"batch_id": batch_id, "tenant_id": tenant_id}
)
```

## Files

- **Service**: `pseudoscribe/infrastructure/zerodb_service.py`
- **Tests**: `tests/infrastructure/test_zerodb_service.py`
- **Docs**: `docs/zerodb_service.md`
- **Examples**: `examples/zerodb_integration_example.py`
