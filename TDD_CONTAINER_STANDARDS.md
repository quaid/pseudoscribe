# TDD Container Standards for PseudoScribe

## Overview

This document defines the first-class container testing environment standards for PseudoScribe, ensuring consistent TDD methodology across all development.

## Container-First TDD Workflow

### 1. **RED Phase - Failing Tests**
```bash
# Run container tests to see failures
./scripts/test-rancher.sh

# Examine specific test failures
kubectl logs job/backend-test
```

### 2. **GREEN Phase - Make Tests Pass**
```bash
# Make minimal code changes
# Rebuild container with changes
./scripts/test-rancher.sh

# Verify tests now pass
```

### 3. **REFACTOR Phase - Clean Code**
```bash
# Refactor while keeping tests green
./scripts/test-rancher.sh

# Ensure all tests still pass
```

## First-Class Artifacts

### 1. **Model Loading Script** (`scripts/setup-test-models.py`)
- **Purpose**: Ensures consistent model availability across environments
- **Environments**: test, development, production
- **Integration**: Automatically run before tests
- **Models**:
  - **Test**: `tinyllama:latest` (637MB) - fast, lightweight
  - **Development**: `tinyllama:latest` + `llama2:7b` (3.8GB)
  - **Production**: `llama2:7b` + `mistral:7b` (4.1GB)

### 2. **Container Test Environment**
- **Kubernetes**: Full service orchestration
- **Services**: API, PostgreSQL, Ollama, Redis
- **Networking**: Service mesh with proper DNS resolution
- **Persistence**: PVC for model storage
- **Monitoring**: Resource usage and performance metrics

### 3. **Test Categories**

#### **Integration Tests** (Primary)
- Test real service interactions
- Use actual Ollama models
- Validate API endpoints with real data
- Test database operations
- Verify service connectivity

#### **Unit Tests** (Supporting)
- Mock external dependencies only when necessary
- Focus on business logic
- Fast execution for development feedback

#### **End-to-End Tests**
- Full user workflow validation
- VSCode extension integration
- Complete request/response cycles

## Container Environment Setup

### **Prerequisites**
```bash
# Ensure Rancher Desktop is running
# Verify kubectl access
kubectl cluster-info

# Verify nerdctl access
nerdctl --namespace k8s.io ps
```

### **Test Execution**
```bash
# Full TDD cycle
./scripts/test-rancher.sh

# Model setup only
python scripts/setup-test-models.py --env test

# Validate test environment
python scripts/setup-test-models.py --env test --validate-only
```

## Development Standards

### **File Structure**
```
pseudoscribe/
├── scripts/
│   ├── setup-test-models.py      # Model loading (first-class)
│   ├── test-rancher.sh           # TDD test runner
│   └── cleanup-rancher.sh        # Environment cleanup
├── tests/
│   ├── api/                      # Integration tests
│   ├── unit/                     # Unit tests
│   └── e2e/                      # End-to-end tests
├── kubernetes/                   # K8s manifests
└── Dockerfile                    # Container definition
```

### **Test Naming Conventions**
- **Integration**: `test_<feature>_integration.py`
- **Unit**: `test_<module>_unit.py`
- **BDD**: `test_<story_id>_bdd.py`
- **E2E**: `test_<workflow>_e2e.py`

### **Container Image Management**
```bash
# Build API image
nerdctl --namespace k8s.io build -t pseudoscribe/api:latest .

# Build VSCode extension test image
nerdctl --namespace k8s.io build -t pseudoscribe/vscode-extension-test:latest -f vscode-extension/Dockerfile vscode-extension/

# List images
nerdctl --namespace k8s.io images | grep pseudoscribe
```

## TDD Best Practices

### **1. Always Start with RED**
- Write failing test first
- Run in container to see actual failure
- Understand what needs to be implemented

### **2. Make Tests GREEN Minimally**
- Write just enough code to pass
- Use real services, not mocks when possible
- Validate in container environment

### **3. REFACTOR Safely**
- Keep tests passing during refactoring
- Use container tests to catch regressions
- Maintain performance requirements

### **4. Container-First Mindset**
- All tests must pass in container
- Local tests are for development speed only
- Container environment is source of truth

## Model Management Standards

### **Test Models**
```python
# Required for all tests
REQUIRED_TEST_MODELS = [
    "tinyllama:latest"  # 637MB, fast loading
]

# Optional for extended testing
OPTIONAL_TEST_MODELS = [
    "llama2:7b"        # 3.8GB, production-like
]
```

### **Model Loading Validation**
```bash
# Before running tests
python scripts/setup-test-models.py --env test --validate-only

# If validation fails, load models
python scripts/setup-test-models.py --env test
```

### **Model Persistence**
- Models stored in Kubernetes PVC
- Persistent across pod restarts
- Shared between test runs
- Automatic cleanup on environment reset

## Performance Standards

### **Test Execution Times**
- **Model Loading**: < 2 minutes (tinyllama)
- **Container Startup**: < 30 seconds
- **Test Suite**: < 5 minutes total
- **Individual Tests**: < 10 seconds each

### **Resource Limits**
- **API Container**: 2GB RAM, 1 CPU
- **Ollama Container**: 4GB RAM, 2 CPU
- **Test Container**: 1GB RAM, 0.5 CPU
- **Total Cluster**: 8GB RAM, 4 CPU

## Troubleshooting

### **Common Issues**

#### **Models Not Loading**
```bash
# Check Ollama service
kubectl logs deployment/ollama

# Verify connectivity
kubectl exec -it deployment/api -- curl http://ollama-svc:11434/api/tags

# Force reload models
python scripts/setup-test-models.py --env test --force-reload
```

#### **Test Failures**
```bash
# Get detailed test output
kubectl logs job/backend-test

# Run specific test
kubectl exec -it deployment/api -- python -m pytest tests/api/test_model_management.py -v

# Check service connectivity
kubectl exec -it deployment/api -- nc -zv postgres-db-svc 5432
kubectl exec -it deployment/api -- nc -zv ollama-svc 11434
```

#### **Container Build Issues**
```bash
# Clean build cache
nerdctl --namespace k8s.io system prune

# Rebuild from scratch
nerdctl --namespace k8s.io build --no-cache -t pseudoscribe/api:latest .
```

## Continuous Integration

### **GitHub Actions Integration**
```yaml
# .github/workflows/tdd.yml
name: TDD Container Tests
on: [push, pull_request]
jobs:
  container-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Kubernetes
        uses: helm/kind-action@v1
      - name: Run TDD Tests
        run: ./scripts/test-rancher.sh
```

### **Pre-commit Hooks**
```bash
# Ensure tests pass before commit
pre-commit install

# Run container tests on commit
git commit -m "feat: implement AI-002"
```

## Quality Gates

### **Definition of Done**
- ✅ All container tests passing
- ✅ Models loaded and validated
- ✅ Performance requirements met
- ✅ Security scans clean
- ✅ Documentation updated
- ✅ BDD scenarios satisfied

### **Deployment Readiness**
- ✅ Container environment validated
- ✅ Integration tests passing
- ✅ Model management working
- ✅ Resource usage within limits
- ✅ Error handling tested

This container-first TDD approach ensures that our development process matches our deployment environment, catching integration issues early and maintaining high code quality.
