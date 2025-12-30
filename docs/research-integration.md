# Research Material Integration (AI-014)

## Overview

The Research Material Integration feature enables users to upload PDF research documents, automatically extract and index their content, and perform semantic search across research materials. Documents are stored as vector embeddings in ZeroDB and can be linked to specific writing projects.

## Architecture

### Components

```
┌─────────────────────┐
│   API Endpoints     │
│  (research.py)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ResearchProcessor   │
│ (Infrastructure)    │
└──────────┬──────────┘
           │
           ├─────► PDF Extraction (pdfplumber)
           ├─────► Document Chunking
           └─────► ZeroDB Service (Vector Storage)
```

### Key Files

- **`pseudoscribe/infrastructure/research_processor.py`**: Core business logic
- **`pseudoscribe/api/research.py`**: FastAPI endpoints
- **`tests/infrastructure/test_research_processor.py`**: Infrastructure tests
- **`tests/api/test_research_api.py`**: API endpoint tests

## Features

### 1. PDF Document Upload

**Endpoint**: `POST /api/v1/research/upload`

**Parameters**:
- `file`: PDF file (multipart/form-data)
- `tenant_id`: Tenant identifier (query parameter)
- `project_id`: Project identifier (query parameter)

**Process**:
1. Validates file is a PDF
2. Extracts text from all pages using pdfplumber
3. Chunks text into semantically meaningful segments (default: 1000 chars with 200 char overlap)
4. Generates embeddings using BAAI/bge-small-en-v1.5 model
5. Stores vectors in ZeroDB with metadata
6. Associates document with project

**Response**:
```json
{
  "document_id": "uuid",
  "document_name": "research_paper.pdf",
  "chunk_count": 15,
  "tenant_id": "tenant-123",
  "project_id": "project-456",
  "message": "Successfully processed 15 chunks"
}
```

### 2. Semantic Search

**Endpoint**: `POST /api/v1/research/search`

**Request Body**:
```json
{
  "query": "machine learning algorithms",
  "project_id": "project-456",  // optional
  "limit": 10,
  "threshold": 0.7
}
```

**Parameters**:
- `tenant_id`: Tenant identifier (query parameter)

**Response**:
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "text": "Chunk text content...",
      "document_id": "doc-uuid",
      "document_name": "ml_paper.pdf",
      "chunk_index": 0,
      "similarity_score": 0.95
    }
  ],
  "count": 5
}
```

### 3. List Project Documents

**Endpoint**: `GET /api/v1/research/projects/{project_id}/documents`

**Parameters**:
- `project_id`: Project identifier (path parameter)
- `tenant_id`: Tenant identifier (query parameter)

**Response**:
```json
{
  "documents": [
    {
      "document_id": "doc-uuid",
      "document_name": "paper1.pdf",
      "created_at": "2024-01-01T00:00:00",
      "metadata": {}
    }
  ],
  "count": 2,
  "project_id": "project-456"
}
```

### 4. Delete Document

**Endpoint**: `DELETE /api/v1/research/documents/{document_id}`

**Parameters**:
- `document_id`: Document identifier (path parameter)
- `tenant_id`: Tenant identifier (query parameter)

**Response**:
```json
{
  "document_id": "doc-uuid",
  "chunks_deleted": 15,
  "message": "Successfully deleted document and 15 chunks"
}
```

## Document Chunking Strategies

The `ResearchProcessor` supports multiple chunking strategies:

### 1. Fixed Size (Default)
- Chunks text into fixed-size segments (default: 1000 characters)
- Applies overlap between chunks (default: 200 characters)
- Preserves context at chunk boundaries
- Best for general-purpose document processing

### 2. Sentence-Based
- Chunks by complete sentences
- Respects sentence boundaries
- Better for narrative documents
- Ensures grammatical coherence

### 3. Paragraph-Based
- Chunks by paragraphs
- Preserves document structure
- Ideal for well-structured documents
- Maintains topical coherence

## Multi-Tenant Isolation

Research materials are isolated by tenant using:

1. **Namespace**: Each tenant has a dedicated namespace `research_{tenant_id}`
2. **Metadata Filtering**: All queries filter by `tenant_id` in metadata
3. **Project Association**: Documents can be filtered by `project_id`

## Vector Storage

Documents are stored in ZeroDB using:

- **Embedding Model**: BAAI/bge-small-en-v1.5 (384 dimensions)
- **Similarity Metric**: Cosine similarity
- **Metadata Schema**:
  ```json
  {
    "tenant_id": "string",
    "project_id": "string",
    "document_id": "string",
    "document_name": "string",
    "chunk_index": "integer",
    "total_chunks": "integer",
    "created_at": "ISO 8601 datetime",
    "file_size": "integer (bytes)",
    "content_type": "string"
  }
  ```

## Usage Examples

### Python Client Example

```python
import httpx

# Upload a research document
async with httpx.AsyncClient() as client:
    with open("research_paper.pdf", "rb") as f:
        files = {"file": ("research_paper.pdf", f, "application/pdf")}
        params = {
            "tenant_id": "tenant-123",
            "project_id": "project-456"
        }
        response = await client.post(
            "http://localhost:8000/api/v1/research/upload",
            files=files,
            params=params
        )
        result = response.json()
        document_id = result["document_id"]

    # Search research materials
    search_request = {
        "query": "neural network architectures",
        "project_id": "project-456",
        "limit": 5,
        "threshold": 0.75
    }
    response = await client.post(
        "http://localhost:8000/api/v1/research/search",
        json=search_request,
        params={"tenant_id": "tenant-123"}
    )
    results = response.json()["results"]
```

### cURL Examples

```bash
# Upload document
curl -X POST "http://localhost:8000/api/v1/research/upload?tenant_id=tenant-123&project_id=project-456" \
  -F "file=@research_paper.pdf"

# Search research
curl -X POST "http://localhost:8000/api/v1/research/search?tenant_id=tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "limit": 10,
    "threshold": 0.7
  }'

# List documents
curl -X GET "http://localhost:8000/api/v1/research/projects/project-456/documents?tenant_id=tenant-123"

# Delete document
curl -X DELETE "http://localhost:8000/api/v1/research/documents/doc-uuid?tenant_id=tenant-123"
```

## Testing

### Running Tests

```bash
# Run infrastructure tests
pytest tests/infrastructure/test_research_processor.py -v

# Run API tests
pytest tests/api/test_research_api.py -v

# Run all research tests
pytest -k research -v

# Run with coverage
pytest tests/infrastructure/test_research_processor.py --cov=pseudoscribe.infrastructure.research_processor
```

### Test Coverage

The implementation includes comprehensive tests:

- **Infrastructure Tests** (`test_research_processor.py`):
  - PDF extraction (valid, corrupted, empty files)
  - Document chunking (fixed size, overlap, sentence-based)
  - Vector storage with multi-tenant isolation
  - Semantic search with filtering
  - Document management (list, delete)
  - End-to-end processing workflow

- **API Tests** (`test_research_api.py`):
  - Document upload validation
  - Search with various filters
  - Project document listing
  - Document deletion
  - Error handling (400, 404, 422, 500)
  - Full integration workflow

## Dependencies

New dependencies added in `requirements.txt`:

```
pdfplumber==0.11.0    # PDF text extraction
reportlab==4.0.7      # PDF generation for tests
```

Install with:
```bash
pip install -r requirements.txt
```

## Performance Considerations

### Chunking Performance
- Fixed-size chunking: O(n) where n is document length
- Sentence/paragraph chunking: O(n) with regex overhead
- Recommended chunk size: 500-2000 characters

### Vector Storage
- Embedding generation: ~50ms per chunk (CPU)
- Batch storage: More efficient than individual inserts
- Search latency: <100ms for typical queries

### Recommendations
- For large documents (>100 pages): Process in background task
- For high-volume uploads: Implement rate limiting
- For production: Enable caching for frequently accessed documents

## Future Enhancements

Potential improvements for future iterations:

1. **Advanced PDF Processing**
   - Extract images and tables
   - Preserve document structure (headers, sections)
   - Support OCR for scanned documents

2. **Enhanced Search**
   - Hybrid search (keyword + semantic)
   - Re-ranking based on relevance
   - Citation extraction and linking

3. **Document Management**
   - Version control for documents
   - Automatic duplicate detection
   - Document tagging and categorization

4. **Integration**
   - Real-time search suggestions while writing
   - Auto-citation from research materials
   - Research summary generation

## Troubleshooting

### Common Issues

**Issue**: `pdfplumber not installed` error
```bash
# Solution
pip install pdfplumber==0.11.0
```

**Issue**: PDF extraction fails with corrupted file
```python
# The system raises PDFExtractionError with descriptive message
# Check PDF file integrity and re-upload
```

**Issue**: Search returns no results
```python
# Check:
# 1. Document was successfully uploaded (chunk_count > 0)
# 2. tenant_id and project_id match upload parameters
# 3. Similarity threshold is not too high (try 0.5)
# 4. Query text is relevant to document content
```

**Issue**: Memory usage high for large PDFs
```python
# For documents >50MB:
# 1. Process in background with Celery
# 2. Implement streaming upload
# 3. Consider chunking during upload
```

## Security Considerations

1. **File Validation**
   - Only PDF files accepted
   - File size limits enforced
   - Content type validation

2. **Multi-Tenant Isolation**
   - Namespace isolation in ZeroDB
   - Metadata filtering on all queries
   - No cross-tenant data leakage

3. **Input Sanitization**
   - Query text sanitized
   - Metadata validated
   - Path traversal prevented

## Compliance

- **Data Privacy**: Research materials stored per tenant
- **Data Retention**: Documents can be deleted on request
- **Access Control**: Tenant-based access control enforced

## Maintenance

### Monitoring
- Track upload success/failure rates
- Monitor search latency and quality
- Alert on storage quota thresholds

### Cleanup
```python
# Delete old documents
await research_processor.delete_document(
    tenant_id="tenant-123",
    document_id="doc-uuid"
)

# Optimize vector storage (via ZeroDB admin)
# Run periodically to maintain performance
```

## References

- [Issue #102 (AI-014)](https://github.com/quaid/pseudoscribe/issues/102)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- [ZeroDB Integration Guide](./zerodb-integration.md)
- [Multi-Tenant Architecture](./multi-tenant.md)
