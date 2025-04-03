# Data Model Documentation

## Core Entities and Relationships

```mermaid
erDiagram
    Tenant ||--o{ User : contains
    Tenant ||--o{ Organization : contains
    User ||--o{ UserRole : has
    Role ||--o{ UserRole : has
    User ||--o{ Content : creates
    User ||--o{ StyleProfile : owns
    Organization ||--o{ Team : contains
    Team ||--o{ User : contains
    Content ||--o{ ContentVersion : has
    Content ||--o{ ContentVector : has
    Content ||--o{ Tag : has
    Content ||--o{ KnowledgeNode : generates
    StyleProfile ||--o{ StyleVector : contains
    KnowledgeNode ||--o{ KnowledgeEdge : has
    KnowledgeNode ||--o{ KnowledgeVector : has

    Tenant {
        uuid id PK
        string name
        timestamp created_at
        boolean is_active
        jsonb settings
    }

    Organization {
        uuid id PK
        uuid tenant_id FK
        string name
        timestamp created_at
        jsonb settings
    }

    User {
        uuid id PK
        uuid tenant_id FK
        string email
        string hashed_password
        timestamp created_at
        boolean is_active
        jsonb preferences
    }

    Team {
        uuid id PK
        uuid org_id FK
        string name
        timestamp created_at
    }

    Role {
        uuid id PK
        string name
        jsonb permissions
        timestamp created_at
    }

    UserRole {
        uuid user_id FK
        uuid role_id FK
        uuid scope_id
        string scope_type
        timestamp created_at
    }

    Content {
        uuid id PK
        uuid user_id FK
        uuid tenant_id FK
        string title
        string content_type
        timestamp created_at
        timestamp updated_at
        jsonb metadata
        boolean is_public
    }

    ContentVersion {
        uuid id PK
        uuid content_id FK
        text content
        integer version
        timestamp created_at
        jsonb diff
    }

    ContentVector {
        uuid id PK
        uuid content_id FK
        vector embedding
        string model_id
        timestamp created_at
    }

    StyleProfile {
        uuid id PK
        uuid user_id FK
        string name
        jsonb parameters
        timestamp created_at
        timestamp updated_at
    }

    StyleVector {
        uuid id PK
        uuid profile_id FK
        vector embedding
        string model_id
        timestamp created_at
    }

    Tag {
        uuid id PK
        uuid content_id FK
        string name
        timestamp created_at
    }

    KnowledgeNode {
        uuid id PK
        uuid content_id FK
        string title
        text content
        jsonb metadata
        timestamp created_at
    }

    KnowledgeEdge {
        uuid id PK
        uuid source_node_id FK
        uuid target_node_id FK
        string relationship_type
        float weight
        timestamp created_at
    }

    KnowledgeVector {
        uuid id PK
        uuid node_id FK
        vector embedding
        string model_id
        timestamp created_at
    }
```

## Key Relationships Explained

### Multi-tenancy and Organization
- Each `Tenant` represents a separate instance of the application
- `Organization` belongs to a `Tenant` and can have multiple `Teams`
- `User` belongs to a `Tenant` and can be part of multiple `Teams`

### RBAC (Role-Based Access Control)
- `Role` defines permissions at various levels
- `UserRole` links users to roles with specific scopes
- Scope can be at Tenant, Organization, or Team level

### Content Management
- `Content` is the core entity for all written material
- `ContentVersion` tracks revisions and changes
- `ContentVector` stores embeddings for RAG and similarity search
- `Tag` allows for content organization and discovery

### Style Management
- `StyleProfile` captures user's writing style preferences
- `StyleVector` stores embeddings of style characteristics
- Multiple style profiles can be maintained per user

### Knowledge Graph
- `KnowledgeNode` represents concepts or ideas
- `KnowledgeEdge` defines relationships between nodes
- `KnowledgeVector` enables semantic search and relationships

## Vector Storage
All vector-based entities (`ContentVector`, `StyleVector`, `KnowledgeVector`) use pgvector for:
- Similarity search
- Style matching
- Semantic relationships
- RAG operations

## Notes on Implementation

### Indexing Strategy
- B-tree indexes on all foreign keys
- GiST indexes on vector columns for similarity search
- Composite indexes on frequently queried combinations

### Partitioning
- Content and vector tables should be partitioned by tenant_id
- Consider time-based partitioning for version history

### Security
- Row-level security policies based on tenant_id
- Encrypted storage for sensitive fields
- Audit logging on all critical tables

### Performance
- Materialized views for complex aggregations
- Async vector computation
- Caching strategy for frequently accessed data
