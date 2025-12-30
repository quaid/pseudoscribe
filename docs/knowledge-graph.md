# Knowledge Graph Implementation (KM-009)

**Status**: Implemented
**Date**: 2025-12-30
**Issue**: #103

## Overview

The Knowledge Graph feature provides a ZeroDB-backed system for managing relationships between documents in an Obsidian vault. It enables semantic search, cross-reference suggestions, and relationship tracking using vector embeddings.

## Architecture

### Components

1. **knowledge_graph.py** - Core knowledge graph implementation
   - `parse_markdown_links()` - Extracts wiki and markdown links
   - `KnowledgeGraph` - Main class for graph operations
     - `store_document()` - Store docs with embeddings
     - `find_related()` - Semantic search
     - `suggest_references()` - Cross-reference suggestions
     - `build_graph_from_vault()` - Build graph from vault
     - `sync_vault_changes()` - Sync vault updates

2. **knowledge.py** - REST API endpoints
   - `POST /api/v1/knowledge/sync` - Sync vault to graph
   - `GET /api/v1/knowledge/related` - Find related documents
   - `POST /api/v1/knowledge/suggest` - Suggest references
   - `GET /api/v1/knowledge/health` - Health check

3. **vault_sync.py** - Existing vault synchronization (unchanged)
   - Already implements vault scanning and change detection

### Data Flow

```
Obsidian Vault
      ↓
VaultSync.scan_vault()
      ↓
KnowledgeGraph.build_graph_from_vault()
      ↓
parse_markdown_links() → Extract relationships
      ↓
ZeroDBService.generate_embeddings() → Vector embeddings
      ↓
ZeroDBService.upsert_vector() → Store in ZeroDB
      ↓
Knowledge Graph (vectors + metadata in ZeroDB)
```

### Search Flow

```
User Query
      ↓
KnowledgeGraph.find_related()
      ↓
ZeroDBService.semantic_search()
      ↓
Vector similarity search
      ↓
Related Documents (with scores)
```

## Features Implemented

### 1. Markdown Link Parsing
- Extracts `[[wiki links]]` and `[[link|alias]]` syntax
- Parses `[text](link.md)` markdown links
- Filters out external URLs (http/https)
- Handles relative paths and nested folders

### 2. Document Storage
- Generates embeddings using BAAI/bge-small-en-v1.5 model
- Stores document content as vectors in ZeroDB
- Metadata includes:
  - `doc_path` - Relative path in vault
  - `tenant_id` - Multi-tenant isolation
  - `links` - Extracted link relationships
  - `title` - Document title (from first heading)
  - Custom metadata (tags, etc.)

### 3. Semantic Search
- Find documents similar to query text
- Configurable similarity threshold (0.0-1.0)
- Limit number of results
- Returns documents with:
  - Similarity score
  - Path and title
  - Outgoing links

### 4. Cross-Reference Suggestions
- Analyze content to suggest relevant references
- Exclude current document from suggestions
- Filter by minimum relevance score
- Useful for identifying missing links

### 5. Vault Synchronization
- Detect added, modified, and deleted files
- Update embeddings for changed documents
- Track relationships as they evolve
- Incremental updates (don't rebuild entire graph)

## API Usage

### Sync Vault

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/sync \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: my-tenant" \
  -d '{
    "vault_path": "/home/user/Documents/my-vault",
    "namespace": "personal-notes"
  }'
```

Response:
```json
{
  "status": "success",
  "added": ["notes/new-idea.md"],
  "modified": ["notes/updated.md"],
  "deleted": [],
  "total_documents": 42
}
```

### Find Related Documents

```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/related?query=machine%20learning&limit=5&threshold=0.7" \
  -H "X-Tenant-ID: my-tenant"
```

Response:
```json
{
  "query": "machine learning",
  "results": [
    {
      "doc_path": "ml/intro.md",
      "title": "Introduction to ML",
      "score": 0.92,
      "links": ["Neural Networks", "Data Science"]
    }
  ],
  "count": 1
}
```

### Suggest References

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/suggest \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: my-tenant" \
  -d '{
    "content": "# My Note\n\nWriting about deep learning...",
    "current_doc_path": "ml/my-note.md",
    "limit": 5,
    "threshold": 0.75
  }'
```

Response:
```json
{
  "suggestions": [
    {
      "doc_path": "ml/neural-nets.md",
      "title": "Neural Networks",
      "score": 0.88,
      "links": ["Deep Learning"]
    }
  ],
  "count": 1
}
```

## Multi-Tenant Support

- Each tenant has isolated namespace: `kg-{tenant_id}`
- Tenant ID from `X-Tenant-ID` header
- All operations scoped to tenant namespace
- No cross-tenant data leakage

## Performance Considerations

### Embedding Model
- Default: `BAAI/bge-small-en-v1.5` (384 dimensions)
- Fast generation, good quality
- Alternative: `BAAI/bge-base-en-v1.5` (768 dim) for better accuracy
- Alternative: `BAAI/bge-large-en-v1.5` (1024 dim) for best accuracy

### Vector Search
- Uses ZeroDB's optimized vector search
- Cosine similarity by default
- Threshold filtering reduces result set
- Indexed for fast retrieval

### Incremental Sync
- Only process changed files (via `sync_vault_changes()`)
- VaultSync tracks modification times
- Upsert updates existing vectors
- No need to rebuild entire graph

## Testing

### Unit Tests
- `tests/infrastructure/test_knowledge_graph.py`
  - Link parsing (wiki, markdown, special chars)
  - Document storage with metadata
  - Semantic search with thresholds
  - Reference suggestions
  - Graph building from vault
  - Vault sync integration

### API Tests
- `tests/api/test_knowledge_api.py`
  - Sync endpoint validation
  - Related documents endpoint
  - Suggest references endpoint
  - Error handling
  - Parameter validation

### Running Tests

```bash
# Run all knowledge graph tests
pytest tests/infrastructure/test_knowledge_graph.py -v

# Run API tests
pytest tests/api/test_knowledge_api.py -v

# Run with coverage
pytest tests/ --cov=pseudoscribe.infrastructure.knowledge_graph --cov-report=term-missing
```

## Future Enhancements

### Planned Features
1. **Graph Visualization**
   - Render relationship graphs
   - Interactive exploration
   - Orphan document detection

2. **Backlink Tracking**
   - Find documents that link to current doc
   - Bidirectional navigation
   - Link popularity metrics

3. **Vector Deletion**
   - Delete vectors for removed documents
   - Cleanup orphaned vectors
   - Storage optimization

4. **Advanced Metadata**
   - Extract tags from frontmatter
   - Track creation/modification dates
   - Author attribution

5. **Query Expansion**
   - Suggest related queries
   - Autocomplete from graph
   - Query history

### Performance Optimizations
- Batch embedding generation
- Incremental index updates
- Caching for frequent queries
- Lazy loading for large vaults

## Integration with PseudoScribe

### Writing Assistance
- Suggest relevant references while writing
- Auto-link to related content
- Context-aware style recommendations

### Style Analysis
- Analyze writing style across graph
- Identify style patterns in related docs
- Style consistency checking

### Collaboration
- Share knowledge graphs between team members
- Collaborative note-taking
- Shared reference library

## Dependencies

- **ZeroDB** - Vector storage and search
- **VaultSync** - Vault scanning and change detection
- **FastAPI** - REST API framework
- **BAAI/bge models** - Embedding generation

## Configuration

### Environment Variables
```bash
# Database connection (inherited from ZeroDB)
ZERODB_PROJECT_ID=your-project-id
ZERODB_API_KEY=your-api-key

# Optional: Custom embedding model
KNOWLEDGE_GRAPH_MODEL=BAAI/bge-small-en-v1.5

# Optional: Default namespace prefix
KNOWLEDGE_GRAPH_NAMESPACE_PREFIX=kg
```

### Code Configuration
```python
from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

# Initialize with custom settings
kg = KnowledgeGraph(
    tenant_id="my-tenant",
    namespace="custom-vault",
    embedding_model="BAAI/bge-base-en-v1.5"
)
```

## Troubleshooting

### Issue: Vault sync fails
- **Check**: Vault path exists and is readable
- **Check**: .obsidian directory is excluded from sync
- **Check**: Markdown files have valid UTF-8 encoding

### Issue: No results from semantic search
- **Check**: Vault has been synced successfully
- **Check**: Threshold is not too high (try 0.5-0.7)
- **Check**: Query text is relevant to vault content

### Issue: Slow performance
- **Check**: Use smaller embedding model (384-dim)
- **Check**: Limit result count
- **Check**: Increase similarity threshold
- **Check**: Vault size (consider batch processing)

## References

- GitHub Issue: #103 (KM-009)
- ZeroDB Documentation: [ZeroDB MCP](https://github.com/ainative/zerodb-mcp)
- Obsidian Link Syntax: [Obsidian Help](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
- BGE Models: [BAAI/bge on HuggingFace](https://huggingface.co/BAAI/bge-small-en-v1.5)

## Contributors

- PseudoScribe Team
- Claude Opus 4.5 (TDD Implementation)

---

**Last Updated**: 2025-12-30
**Version**: 1.0.0
