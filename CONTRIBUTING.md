# Contributing to PseudoScribe

Thank you for your interest in contributing to PseudoScribe! This document provides guidelines and instructions for contributing to the project.

## Development Standards

PseudoScribe follows the Writer's Block Assistant Development Standards, which are adapted from the Semantic Seed Venture Studio Coding Standards. Key principles include:

- **Test-Driven Development (TDD)** with a focus on behavior-driven tests
- **"No Mocks or Stubs" policy** for production code
- **Containerized development workflow** following the "operate first" approach
- **Security and privacy** as core design principles

## Development Workflow

### 1. Backlog Management

We use GitHub Issues and Projects for backlog management with a BDD focus.

#### Story Classification

All work items must be classified as:
- **Feature**: New capabilities (e.g., `feature/AI-{id}`)
- **Bug**: Issues affecting functionality (e.g., `bug/B-{id}`)
- **Chore**: Technical debt, refactoring, dependencies (e.g., `chore/CH-{id}`)

### 2. Branch Strategy

```
main
├── feature/AI-{id} (AI Integration)
├── feature/KM-{id} (Knowledge Management)
├── feature/VSC-{id} (VSCode Extension)
├── bug/B-{id}
└── chore/CH-{id}
```

### 3. Development Flow

1. **Start a Story**
   - Pick from prioritized GitHub Issues
   - Create a feature branch with the appropriate naming convention
   - Add a WIP commit with test stubs

2. **TDD Workflow**
   ```
   Red Tests → Green Tests → Refactor → PR
   ```

3. **Pull Request Requirements**
   - All tests passing
   - Security scan clean
   - Documentation updated
   - Performance impact assessed

## Containerized Development

PseudoScribe uses a containerized development workflow that follows the "operate first" principle:

1. **Setup the Environment**
   ```bash
   ./scripts/operate_first.py start
   ```

2. **Test the Environment**
   ```bash
   ./scripts/test_container.py
   ```

3. **Implement New Features**
   - Add new endpoints to the appropriate API modules
   - Update infrastructure components as needed
   - Follow the "No Mocks or Stubs" policy
   - Add comprehensive tests

4. **Rebuild and Test**
   ```bash
   ./scripts/operate_first.py rebuild
   ./scripts/test_container.py
   ```

## Code Style Guidelines

- **Python**: Follow PEP 8 with 4-space indentation
- **Naming Conventions**: snake_case for functions, PascalCase for classes
- **Documentation**: Docstrings for all functions, classes, and modules
- **Test files**: `test_{name}.py` for unit tests

## Documentation Requirements

1. Update the README.md with new features
2. Add API documentation in the docs/ directory
3. Include example usage in tests/
4. Update Architecture Decision Records (ADRs) if applicable

## Definition of Done

- Feature complete per BDD scenarios
- Tests passing (unit, integration, E2E)
- Documentation updated
- Performance metrics met
- Security review passed
- PR approved by at least one reviewer

## Getting Help

If you have questions or need assistance, please:
1. Check existing documentation in the docs/ directory
2. Review open and closed issues in GitHub
3. Open a new issue with the "question" label

Thank you for contributing to PseudoScribe!
