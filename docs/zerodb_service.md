# ZeroDB Service Integration

## Overview

The `ZeroDBService` provides a unified Python interface for ZeroDB operations in PseudoScribe. It wraps the ZeroDB MCP (Model Context Protocol) tools with proper error handling, type hints, and multi-tenant support.

## Architecture

### Singleton Pattern
The service uses the singleton pattern to ensure only one instance exists throughout the application lifecycle:

```python
from pseudoscribe.infrastructure.zerodb_service import ZeroDBService

# Get the singleton instance
service = ZeroDBService.get_instance()
```

### Error Handling
Custom exceptions provide clear error reporting:

- `ZeroDBError` - Base exception for all ZeroDB operations
- `ZeroDBConnectionError` - Connection failures
- `ZeroDBQueryError` - Query execution failures

### Multi-Tenant Support
All operations support tenant isolation through:
- `tenant_id` parameter for PostgreSQL queries
- `namespace` parameter for vector operations

## PostgreSQL Operations

### Execute Query
Execute SQL queries with parameter binding and tenant context:

```python
# Simple SELECT
result = await service.execute_query(
    "SELECT * FROM documents WHERE tenant_id = $1",
    params=["tenant-123"],
    tenant_id="tenant-123"
)

# Read-only query with timeout
result = await service.execute_query(
    "SELECT COUNT(*) FROM users",
    read_only=True,
    timeout_seconds=10
)
```

### Schema Information
Get table schema information:

```python
# All tables
schema = await service.get_schema_info()

# Specific table
schema = await service.get_schema_info(
    table_name="users",
    include_indexes=True,
    include_constraints=True
)
```

### Create Table
Create new PostgreSQL tables:

```python
columns = [
    {"name": "id", "type": "SERIAL PRIMARY KEY"},
    {"name": "tenant_id", "type": "VARCHAR(255)", "nullable": False},
    {"name": "content", "type": "TEXT"},
    {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
]

result = await service.create_table(
    "documents",
    columns,
    if_not_exists=True,
    indexes=[{"columns": ["tenant_id"]}]
)
```

### Database Statistics
Get performance and usage statistics:

```python
stats = await service.get_stats(
    include_storage=True,
    include_connections=True,
    include_queries=True,
    time_range="day"
)
```

## Vector Operations

### Upsert Vector
Store or update vector embeddings:

```python
vector = [0.1, 0.2, 0.3] * 128  # 384-dimensional vector
metadata = {
    "tenant_id": "tenant-123",
    "document_type": "style_profile",
    "author": "user-456"
}

vector_id = await service.upsert_vector(
    vector=vector,
    document="This is the source text...",
    metadata=metadata,
    namespace="tenant-123"
)
```

### Vector Search
Find similar vectors using cosine similarity:

```python
query_vector = [0.15, 0.25, 0.35] * 128

results = await service.search_vectors(
    query_vector=query_vector,
    limit=10,
    namespace="tenant-123",
    threshold=0.7,
    filter_metadata={"document_type": "style_profile"}
)

for result in results:
    print(f"Document: {result['document']}")
    print(f"Score: {result['score']}")
```

### Semantic Search
Search using text queries (auto-embedding):

```python
results = await service.semantic_search(
    query_text="How to write engaging content",
    limit=10,
    namespace="tenant-123",
    threshold=0.7,
    model="BAAI/bge-small-en-v1.5"
)
```

## Embedding Operations

### Generate Embeddings
Convert text to vector embeddings:

```python
texts = [
    "First document text",
    "Second document text",
    "Third document text"
]

embeddings = await service.generate_embeddings(
    texts=texts,
    model="BAAI/bge-small-en-v1.5"  # 384 dimensions
)

# Each embedding is a list of floats
for i, embedding in enumerate(embeddings):
    print(f"Text {i}: {len(embedding)} dimensions")
```

### Embed and Store
Generate embeddings and store in one operation:

```python
texts = [
    "Write engaging introductions",
    "Use active voice",
    "Keep paragraphs concise"
]

metadata = {"type": "writing_tips", "tenant_id": "tenant-123"}

vector_ids = await service.embed_and_store(
    texts=texts,
    namespace="tenant-123",
    metadata=metadata,
    model="BAAI/bge-small-en-v1.5"
)
```

## NoSQL Table Operations

### Create Table
Create document-based tables:

```python
schema = {
    "fields": {
        "user_id": {"type": "string"},
        "preferences": {"type": "object"},
        "settings": {"type": "object"}
    },
    "indexes": ["user_id"]
}

result = await service.create_nosql_table(
    table_name="user_preferences",
    schema=schema,
    description="User preference storage"
)
```

### Insert Rows
Insert documents into NoSQL tables:

```python
rows = [
    {"user_id": "user-123", "preferences": {"theme": "dark"}},
    {"user_id": "user-456", "preferences": {"theme": "light"}}
]

result = await service.insert_rows(
    table_id="user_preferences",
    rows=rows,
    return_ids=True
)
```

### Query Rows
Query with MongoDB-style filters:

```python
result = await service.query_rows(
    table_id="user_preferences",
    filter={"user_id": "user-123"},
    limit=10,
    offset=0,
    sort={"created_at": -1},
    projection={"preferences": 1, "settings": 1}
)
```

## Multi-Tenant Isolation

### PostgreSQL Tenant Isolation
Use `tenant_id` in queries and metadata:

```python
# Include tenant_id in WHERE clause
result = await service.execute_query(
    "SELECT * FROM documents WHERE tenant_id = $1",
    params=["tenant-123"],
    tenant_id="tenant-123"
)
```

### Vector Namespace Isolation
Use namespaces to separate tenant data:

```python
# Store vectors in tenant namespace
vector_id = await service.upsert_vector(
    vector=vector,
    document=text,
    metadata={"tenant_id": "tenant-123"},
    namespace="tenant-123"  # Isolates by tenant
)

# Search only within tenant namespace
results = await service.search_vectors(
    query_vector=query,
    namespace="tenant-123"  # Only searches this tenant's vectors
)
```

## Error Handling

### Basic Error Handling
```python
from pseudoscribe.infrastructure.zerodb_service import (
    ZeroDBError,
    ZeroDBConnectionError,
    ZeroDBQueryError
)

try:
    result = await service.execute_query(sql_query)
except ZeroDBQueryError as e:
    logger.error(f"Query failed: {e}")
    # Handle query-specific error
except ZeroDBConnectionError as e:
    logger.error(f"Connection failed: {e}")
    # Handle connection error
except ZeroDBError as e:
    logger.error(f"ZeroDB error: {e}")
    # Handle general error
```

### Async Error Handling
All methods are async and should be awaited:

```python
async def process_document(text: str, tenant_id: str):
    try:
        # Generate embedding
        embeddings = await service.generate_embeddings([text])

        # Store vector
        vector_id = await service.upsert_vector(
            vector=embeddings[0],
            document=text,
            metadata={"tenant_id": tenant_id},
            namespace=tenant_id
        )

        return vector_id
    except ZeroDBError as e:
        logger.error(f"Failed to process document: {e}")
        raise
```

## Supported Models

### Embedding Models
- `BAAI/bge-small-en-v1.5` - 384 dimensions (default, fast)
- `BAAI/bge-base-en-v1.5` - 768 dimensions (balanced)
- `BAAI/bge-large-en-v1.5` - 1024 dimensions (high quality)

### Vector Dimensions
The service automatically detects and routes vectors based on dimensions:
- 384, 768, 1024, or 1536 dimensions supported

## Testing

### Unit Tests
Tests use mocked MCP tools:

```python
@pytest.fixture
def mock_mcp_postgres_query():
    with patch('mcp__zerodb__zerodb_postgres_query.mcp__zerodb__zerodb_postgres_query') as mock:
        yield mock

@pytest.mark.asyncio
async def test_execute_query(zerodb_service, mock_mcp_postgres_query):
    mock_mcp_postgres_query.return_value = {"rows": [], "row_count": 0}
    result = await zerodb_service.execute_query("SELECT 1")
    assert result["row_count"] == 0
```

### Integration Tests
Test with actual ZeroDB instance:

```python
@pytest.mark.integration
async def test_vector_roundtrip():
    service = ZeroDBService.get_instance()

    # Generate embedding
    texts = ["Test document"]
    embeddings = await service.generate_embeddings(texts)

    # Store vector
    vector_id = await service.upsert_vector(
        vector=embeddings[0],
        document=texts[0],
        metadata={"test": True},
        namespace="test"
    )

    # Search for it
    results = await service.search_vectors(
        query_vector=embeddings[0],
        namespace="test"
    )

    assert len(results) > 0
    assert results[0]["vector_id"] == vector_id
```

## Best Practices

### 1. Use Namespaces for Tenant Isolation
```python
# GOOD: Tenant-specific namespace
await service.upsert_vector(
    vector=embedding,
    document=text,
    metadata={"tenant_id": tenant_id},
    namespace=f"tenant-{tenant_id}"
)

# BAD: Shared namespace
await service.upsert_vector(
    vector=embedding,
    document=text,
    metadata={"tenant_id": tenant_id},
    namespace="default"  # Multiple tenants mixed together
)
```

### 2. Include Tenant Context in Metadata
```python
# GOOD: Metadata includes tenant_id
metadata = {
    "tenant_id": "tenant-123",
    "document_type": "style_profile",
    "user_id": "user-456"
}
```

### 3. Use Parameter Binding for SQL
```python
# GOOD: Parameterized query
await service.execute_query(
    "SELECT * FROM documents WHERE tenant_id = $1 AND user_id = $2",
    params=["tenant-123", "user-456"]
)

# BAD: String concatenation (SQL injection risk)
await service.execute_query(
    f"SELECT * FROM documents WHERE tenant_id = '{tenant_id}'"
)
```

### 4. Handle Errors Gracefully
```python
# GOOD: Specific error handling
try:
    result = await service.semantic_search(query)
except ZeroDBQueryError:
    # Fallback to alternative search
    result = await fallback_search(query)
except ZeroDBConnectionError:
    # Retry with backoff
    result = await retry_with_backoff(service.semantic_search, query)
```

### 5. Choose Appropriate Models
```python
# GOOD: Match model to use case
# Fast, real-time search
embeddings = await service.generate_embeddings(
    texts,
    model="BAAI/bge-small-en-v1.5"  # 384-dim, fast
)

# High-quality semantic search
embeddings = await service.generate_embeddings(
    texts,
    model="BAAI/bge-large-en-v1.5"  # 1024-dim, accurate
)
```

## Performance Considerations

### Connection Pooling
The service uses connection pooling internally. No need to create multiple instances.

### Batch Operations
Prefer batch operations when processing multiple items:

```python
# GOOD: Batch embedding generation
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = await service.generate_embeddings(texts)

# BAD: Individual embedding generation
embeddings = []
for text in texts:
    embedding = await service.generate_embeddings([text])
    embeddings.append(embedding[0])
```

### Query Optimization
Use appropriate limits and thresholds:

```python
# GOOD: Limited results
results = await service.search_vectors(
    query_vector=query,
    limit=10,  # Only get what you need
    threshold=0.7  # Filter low-quality matches
)

# BAD: Unlimited results
results = await service.search_vectors(
    query_vector=query,
    limit=1000,  # Too many results
    threshold=0.0  # Returns everything
)
```

## File Location

- **Service**: `/home/quaid/Documents/Projects/pseudoscribe/pseudoscribe/infrastructure/zerodb_service.py`
- **Tests**: `/home/quaid/Documents/Projects/pseudoscribe/tests/infrastructure/test_zerodb_service.py`
- **Documentation**: `/home/quaid/Documents/Projects/pseudoscribe/docs/zerodb_service.md`

## Related Documentation

- [ZeroDB MCP Server Documentation](https://github.com/ainative/zerodb-mcp)
- [Multi-Tenant Architecture](./multi_tenant_architecture.md)
- [Vector Store Integration](./vector_store_integration.md)

## Support

For issues or questions:
1. Check the test suite for examples
2. Review ZeroDB MCP server documentation
3. Open an issue in the PseudoScribe repository
