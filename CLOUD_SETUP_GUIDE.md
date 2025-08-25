# PseudoScribe Cloud Container Testing Setup Guide

## Overview

This guide walks through setting up cloud-based container testing for PseudoScribe using the pseudoscribe-agent infrastructure, eliminating local Podman virtualization issues.

## Prerequisites

- Access to Intuit's Jenkins CI/CD environment
- Kubernetes cluster access via Service Paved Road
- Container registry permissions (`docker.intuit.com`)
- Git repository with appropriate branch permissions

## Quick Start

### 1. Copy Cloud Infrastructure Files

Copy the following files from this setup to your Jenkins pipeline:

```bash
# Kubernetes pod configuration
cp pseudoscribe/KubernetesPods-PseudoScribe.yaml .jenkins/

# Jenkins pipeline
cp pseudoscribe/Jenkinsfile-PseudoScribe Jenkinsfile

# Cloud test script
cp pseudoscribe/scripts/test-containers-cloud.sh scripts/
chmod +x scripts/test-containers-cloud.sh
```

### 2. Configure Jenkins Pipeline

1. **Update Jenkins Job Configuration**:
   - Point to `Jenkinsfile-PseudoScribe`
   - Set Kubernetes YAML file path to `KubernetesPods-PseudoScribe.yaml`

2. **Environment Variables**:
   ```groovy
   environment {
       PSEUDOSCRIBE_ENV = 'test'
       DATABASE_URL = 'postgresql://test_user:test_password@localhost:5432/pseudoscribe_test'
       OLLAMA_BASE_URL = 'http://localhost:11434'
       REDIS_URL = 'redis://localhost:6379'
   }
   ```

### 3. Test Execution

Run the pipeline to execute cloud-based container tests:

```bash
# Trigger via Jenkins UI or webhook
# Tests will run in Kubernetes pods automatically
```

## Architecture Details

### Container Stack

The cloud testing environment includes:

- **Podman Container**: `docker.intuit.com/oicp/standard/podman:latest`
  - Container build and runtime operations
  - Isolated container storage (10GB)
  - Security capabilities for container operations

- **PostgreSQL Database**: `docker.intuit.com/postgres:13`
  - Test database with pre-configured credentials
  - Isolated storage (2GB)
  - Automatic initialization

- **Ollama AI Service**: `docker.intuit.com/ollama/ollama:latest`
  - Local AI model testing
  - Model caching (5GB storage)
  - API endpoint for AI operations

- **Redis Cache**: `docker.intuit.com/redis:7-alpine`
  - Session and cache management
  - High-performance in-memory operations

- **Test Runner**: Python 3.12 environment
  - Test execution and reporting
  - Dependency management
  - Result collection

### Resource Allocation

```yaml
Pod Resources:
  Total Limits: 12GB RAM, 6 CPU cores
  Total Requests: 8GB RAM, 4 CPU cores

Per Container:
  - Podman: 4GB RAM, 2 CPU (limits)
  - PostgreSQL: 1GB RAM, 500m CPU (limits)
  - Ollama: 4GB RAM, 2 CPU (limits)
  - Redis: 512MB RAM, 250m CPU (limits)
  - Test Runner: 2GB RAM, 1 CPU (limits)
```

## Test Categories

### 1. Service Connectivity Tests
- PostgreSQL database connection
- Redis cache connectivity  
- Ollama AI service availability
- Network communication between services

### 2. Container Build Tests
- PseudoScribe application container build
- Multi-stage build validation
- Image security scanning
- Build artifact verification

### 3. API Container Tests
- Container startup and health checks
- API endpoint availability
- Service integration validation
- Container networking tests

### 4. Integration Tests
- End-to-end workflow testing
- Database integration
- AI model integration
- Cache layer integration

### 5. Performance Tests
- Container startup time
- API response times
- Resource utilization
- Concurrent request handling

### 6. Security Tests
- Container vulnerability scanning
- Dependency security checks
- Runtime security validation
- Access control verification

## Pipeline Stages

### Stage 1: Setup (Parallel)
- **Prepare Workspace**: Copy code, install dependencies
- **Initialize Services**: Start PostgreSQL, Redis, Ollama

### Stage 2: Code Quality (Parallel)
- **Lint**: Code style and formatting checks
- **Type Check**: Static type analysis
- **Security Scan**: Dependency vulnerability scanning

### Stage 3: Unit Tests
- Python unit tests with coverage
- Test result publishing
- Coverage reporting

### Stage 4: Container Build & Test (Parallel)
- **Build Containers**: Application and test containers
- **Container Tests**: Cloud container test execution

### Stage 5: Integration Tests
- Service integration validation
- Database connectivity tests
- AI model integration tests

### Stage 6: Performance Tests (Conditional)
- Load testing
- Performance benchmarking
- Resource utilization analysis

### Stage 7: End-to-End Tests (Conditional)
- Full application stack testing
- User workflow validation
- Cross-service communication

### Stage 8: Security Scan
- Container image vulnerability scanning
- Runtime security validation

### Stage 9: Publish Artifacts (Conditional)
- Container image publishing
- Artifact archiving

## Configuration Files

### KubernetesPods-PseudoScribe.yaml
Defines the Kubernetes pod specification with all required containers and resources.

### Jenkinsfile-PseudoScribe
Complete Jenkins pipeline with all test stages, parallel execution, and proper error handling.

### test-containers-cloud.sh
Cloud-optimized test script that validates all services and runs comprehensive container tests.

## Benefits Over Local Development

### Immediate Benefits
- **No Virtualization Issues**: Eliminates vfkit/gvproxy problems
- **Consistent Environment**: Same runtime for all developers
- **Parallel Execution**: Multiple test suites run simultaneously
- **Enterprise Security**: Hardened container images

### Development Workflow Benefits
- **Faster Feedback**: Cloud resources provide faster test execution
- **No Local Setup**: Developers don't need local container runtime
- **Shared Results**: Test results visible to entire team
- **Automatic Cleanup**: Resources cleaned up after tests

### Operational Benefits
- **Cost Efficiency**: Pay-per-use cloud resources
- **Scalability**: Auto-scaling based on test load
- **Reliability**: Enterprise-grade infrastructure
- **Monitoring**: Built-in observability and logging

## Troubleshooting

### Common Issues

1. **Pod Startup Failures**
   - Check resource limits and requests
   - Verify image pull permissions
   - Review Kubernetes events

2. **Service Connectivity Issues**
   - Verify port configurations
   - Check service readiness probes
   - Review network policies

3. **Test Failures**
   - Check test result artifacts
   - Review container logs
   - Verify environment variables

### Debug Commands

```bash
# Check pod status
kubectl get pods -l app=pseudoscribe-test

# View pod logs
kubectl logs <pod-name> -c <container-name>

# Describe pod for events
kubectl describe pod <pod-name>

# Access pod for debugging
kubectl exec -it <pod-name> -c test-runner -- /bin/bash
```

## Migration from Local Development

### Step 1: Update CI/CD Configuration
- Replace local test scripts with cloud versions
- Update Jenkins pipeline configuration
- Configure Kubernetes pod specifications

### Step 2: Adapt Test Scripts
- Update connection strings for containerized services
- Modify file paths for cloud environment
- Adjust timeouts for cloud networking

### Step 3: Validate Test Coverage
- Ensure all existing tests run in cloud environment
- Verify test results match local execution
- Add cloud-specific tests as needed

### Step 4: Team Onboarding
- Document new development workflow
- Train team on cloud testing environment
- Establish monitoring and alerting

## Next Steps

1. **Deploy Infrastructure**: Apply Kubernetes and Jenkins configurations
2. **Run Initial Tests**: Execute pipeline to validate setup
3. **Monitor Performance**: Track test execution times and resource usage
4. **Optimize Configuration**: Adjust resources based on actual usage
5. **Team Training**: Onboard development team to new workflow

This cloud-based approach provides a robust, scalable, and maintainable solution for PseudoScribe container testing while eliminating local virtualization issues.
