# PseudoScribe

**Tech Stack**: Python, FastAPI, PostgreSQL (pgvector), Ollama, VSCode Extension
**Repository**: https://github.com/quaid/pseudoscribe
**Last Updated**: 2025-12-29

## Project Overview

PseudoScribe is an AI-powered writing assistant that helps users overcome writer's block by analyzing text style, providing suggestions, and adapting content to match specific writing styles. It features multi-tenant support, containerization, and modular architecture.

## Architecture Patterns

### Data Storage
- **Primary Database**: PostgreSQL with pgvector for vector storage
- **Vector Storage**: pgvector for RAG implementation
- **Caching**: Redis (optional)

### API Design
- **Style**: RESTful FastAPI
- **Authentication**: Multi-tenant with RBAC
- **Versioning**: URL-based (/api/v1/)

## Directory Structure

```
/home/quaid/Documents/Projects/pseudoscribe/
├── pseudoscribe/       # Main Python package
├── tests/              # Test suites (unit, integration, functional)
├── features/           # BDD feature files
├── scripts/            # Development and deployment scripts
├── docs/               # Documentation
├── vscode-extension/   # VSCode extension source
├── kubernetes/         # Kubernetes deployment manifests
└── migrations/         # Alembic database migrations
```

## Coding Conventions

### Naming
- **Files**: snake_case.py
- **Functions**: snake_case
- **Variables**: snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Classes**: PascalCase

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Prefer explicit over implicit imports

## Critical Files

| File | Purpose |
|------|---------|
| `pseudoscribe/` | Main application package |
| `start_api.py` | API entry point |
| `pytest.ini` | Test configuration |
| `alembic.ini` | Database migration configuration |
| `docker-compose.yml` | Container orchestration |

## Development Workflow

### Setup
```bash
# Clone and enter directory
git clone https://github.com/quaid/pseudoscribe.git
cd pseudoscribe

# Start containerized environment
./scripts/operate_first.py start
```

### Running Locally
```bash
# With containers
./scripts/operate_first.py start

# Or with Kubernetes
./scripts/test-rancher.sh
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_example.py

# Run with coverage
pytest --cov=pseudoscribe
```

## Environment Variables

Required environment variables are defined in `.env.example`. Copy to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - For AI features (optional, uses Ollama by default)
- `ANTHROPIC_API_KEY` - Alternative AI provider

## MCP Integration

This project uses the following MCP servers:
- **ZeroDB**: Persistent memory and vector storage
- **GitHub**: Issue tracking and PR management

## Notes for Claude

- Follow TDD workflow: Red tests -> Green tests -> Refactor
- Use Conventional Commits format (feat:, fix:, docs:, refactor:, chore:)
- Branch naming: feature/AI-{id}, bug/B-{id}, chore/CH-{id}
- Run tests before committing: `pytest`
- Multi-tenant isolation is critical - always consider tenant context

---

*Generated with Claude Code /init-new-project command. Update as project evolves.*
