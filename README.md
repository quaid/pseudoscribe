# PseudoScribe

Skip writer's block using an agentic plugin to your favorite content environment.

## Overview

PseudoScribe is an AI-powered writing assistant with a focus on multi-tenant support, containerization, and modular architecture. It helps users overcome writer's block by analyzing text style, providing suggestions, and adapting content to match specific writing styles.

## Features

- **Style Analysis**: Analyze text for complexity, formality, tone, and readability
- **Style Comparison**: Compare two text samples for stylistic similarity
- **Style Adaptation**: Adapt text to match a target writing style
- **Style Checking**: Verify if text matches a target style profile
- **Multi-tenant Support**: Secure isolation between different users/organizations
- **Containerized Deployment**: Easy setup with Podman (or Docker) and podman-compose

## Getting Started

### Prerequisites

- Podman (or Docker) and podman-compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/quaid/pseudoscribe.git
cd pseudoscribe

# Start the containerized environment
./scripts/operate_first.py start
```

## API Endpoints

### Style API

- `POST /api/style/analyze`: Analyze text style characteristics
- `POST /api/style/compare`: Compare styles of two text samples
- `POST /api/style/adapt`: Adapt text to match target style
- `POST /api/style/check`: Check text against target style

### Tenant Configuration API

- `GET /api/tenant/config`: Get tenant configuration
- `POST /api/tenant/config`: Update tenant configuration

### Role Management API

- `GET /api/role`: List available roles
- `POST /api/role`: Create a new role

## Development

PseudoScribe follows the Writer's Block Assistant Development Standards with a focus on:

- Test-Driven Development (TDD)
- "No Mocks or Stubs" policy for production code
- Containerized development workflow
- Behavior-Driven Development (BDD) for testing

### Development Workflow

1. Start with a GitHub Issue
2. Create a feature branch (`feature/AI-{id}`, `bug/B-{id}`, or `chore/CH-{id}`)
3. Follow TDD workflow (Red Tests → Green Tests → Refactor)
4. Create a Pull Request
5. Review and merge

## Architecture

PseudoScribe uses a modular architecture with the following components:

- **API Layer**: FastAPI endpoints
- **Infrastructure Layer**: Core services and utilities
- **Model Layer**: Data models and database interactions

## Security & Privacy

- Local-first architecture
- Multi-tenant isolation
- Proper error handling
- Secure API design

## License

This project is licensed under the MIT License - see the LICENSE file for details.
