# Cloud-Based Container Testing Strategy

## Overview

This document outlines the strategy for migrating PseudoScribe container testing from local Podman (which has vfkit virtualization issues) to the cloud-based infrastructure provided by pseudoscribe-agent.

## Current Challenge

- Local Podman machine fails with vfkit virtualization framework errors
- macOS virtualization framework corruption requires frequent reboots
- Development workflow is blocked by local container runtime issues

## Solution: Cloud-First Container Testing

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Testing Environment                │
├─────────────────────────────────────────────────────────────┤
│  Jenkins Pipeline (pseudoscribe-agent)                     │
│  ├── Kubernetes Pods                                       │
│  │   ├── Podman Container (docker.intuit.com/oicp/...)    │
│  │   ├── Test Runner Container                            │
│  │   └── Database Container (PostgreSQL)                  │
│  └── Automated Test Execution                              │
├─────────────────────────────────────────────────────────────┤
│  PseudoScribe Integration                                   │
│  ├── Container Tests (migrated from local)                 │
│  ├── API Tests                                             │
│  ├── Integration Tests                                      │
│  └── Performance Tests                                      │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Infrastructure Setup

1. **Extend pseudoscribe-agent Kubernetes Configuration**
   - Add PseudoScribe-specific containers to `KubernetesPods.yaml`
   - Configure PostgreSQL container for database tests
   - Setup Ollama container for AI model testing

2. **Jenkins Pipeline Extension**
   - Modify `Jenkinsfile` to include PseudoScribe test stages
   - Add container build and test steps
   - Configure test result collection and reporting

3. **Docker Configuration**
   - Create multi-stage Dockerfile for PseudoScribe
   - Integrate with Intuit's security-hardened base images
   - Setup proper volume mounts and networking

### Phase 2: Test Migration

1. **Container Test Suite**
   - Migrate `test-containers.sh` to run in Kubernetes pods
   - Adapt tests to use cloud-based container runtime
   - Configure proper service discovery and networking

2. **Database Integration**
   - Setup PostgreSQL container in test environment
   - Configure database migrations and seeding
   - Add database connectivity tests

3. **AI Model Testing**
   - Integrate Ollama container for local AI model testing
   - Configure model downloading and caching
   - Add AI pipeline integration tests

### Phase 3: CI/CD Integration

1. **Automated Testing**
   - Trigger tests on code changes
   - Parallel test execution across multiple pods
   - Test result aggregation and reporting

2. **Environment Management**
   - Ephemeral test environments
   - Resource cleanup after test completion
   - Cost optimization through pod scheduling

## Benefits

### Immediate Benefits
- **No Local Virtualization Issues**: Eliminates vfkit/gvproxy problems
- **Consistent Environment**: Same runtime for all developers
- **Scalable Testing**: Multiple parallel test executions
- **Enterprise Security**: Uses Intuit's hardened container images

### Long-term Benefits
- **Production Parity**: Test environment matches production
- **Cost Efficiency**: Shared cloud resources vs individual local VMs
- **Maintenance Free**: No local container runtime management
- **Collaboration**: Shared test results and environments

## Technical Implementation

### Kubernetes Pod Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pseudoscribe-test-pod
spec:
  containers:
    - name: podman
      image: docker.intuit.com/oicp/standard/podman:latest
      resources:
        limits:
          github.com/fuse: 1
      securityContext:
        capabilities:
          add: ["SYS_ADMIN", "SYS_RESOURCE"]
    
    - name: postgresql
      image: docker.intuit.com/postgres:13
      env:
        - name: POSTGRES_DB
          value: pseudoscribe_test
        - name: POSTGRES_USER
          value: test_user
        - name: POSTGRES_PASSWORD
          value: test_password
    
    - name: ollama
      image: docker.intuit.com/ollama/ollama:latest
      resources:
        limits:
          memory: "4Gi"
          cpu: "2"
```

### Jenkins Pipeline Stages

```groovy
pipeline {
    stages {
        stage('Build PseudoScribe') {
            steps {
                container('podman') {
                    sh 'podman build -t pseudoscribe:test .'
                }
            }
        }
        
        stage('Container Tests') {
            parallel {
                stage('API Tests') {
                    steps {
                        container('podman') {
                            sh './scripts/test-api-containers.sh'
                        }
                    }
                }
                stage('Database Tests') {
                    steps {
                        container('podman') {
                            sh './scripts/test-db-containers.sh'
                        }
                    }
                }
                stage('AI Model Tests') {
                    steps {
                        container('podman') {
                            sh './scripts/test-ai-containers.sh'
                        }
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                container('podman') {
                    sh './scripts/test-integration.sh'
                }
            }
        }
    }
}
```

## Migration Steps

### Step 1: Setup Cloud Infrastructure
1. Extend `KubernetesPods.yaml` with PseudoScribe containers
2. Update `Jenkinsfile` with new test stages
3. Configure container registry access

### Step 2: Migrate Test Scripts
1. Adapt `test-containers.sh` for cloud execution
2. Update container networking for Kubernetes
3. Configure service discovery between containers

### Step 3: Database Integration
1. Setup PostgreSQL container configuration
2. Create database initialization scripts
3. Configure connection strings for test environment

### Step 4: AI Model Integration
1. Setup Ollama container with required models
2. Configure model caching and persistence
3. Add AI pipeline tests

### Step 5: Validation and Rollout
1. Run parallel tests (local vs cloud) during transition
2. Validate test coverage and results
3. Document new development workflow

## Success Metrics

- **Test Execution Time**: Target <10 minutes for full test suite
- **Test Reliability**: >99% success rate for stable tests
- **Developer Productivity**: Eliminate local container setup time
- **Cost Efficiency**: Optimize cloud resource usage
- **Coverage**: Maintain or improve test coverage

## Next Steps

1. Create extended Kubernetes pod configuration
2. Update Jenkins pipeline with PseudoScribe stages
3. Migrate and adapt container test scripts
4. Setup database and AI model containers
5. Validate end-to-end testing workflow

This cloud-first approach eliminates local virtualization issues while providing a more robust, scalable, and maintainable testing environment.
