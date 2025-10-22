#!/bin/bash
set -e

echo "🚀 Starting Complete Container Development Environment..."

# Clean up existing resources
echo "[INFO] Cleaning up existing resources..."
kubectl delete job backend-test --ignore-not-found=true
kubectl delete job vscode-extension-test --ignore-not-found=true

# Build containers
echo "[INFO] Building containers..."
echo "Building API container..."
nerdctl build -t pseudoscribe/api:latest .

echo "Building VSCode extension container..."
nerdctl build -t pseudoscribe/vscode-extension-test:latest -f vscode-extension/Dockerfile vscode-extension/

# Deploy services (reuse existing deployment if available)
echo "[INFO] Ensuring services are deployed..."
kubectl get deployment api >/dev/null 2>&1 || {
    echo "Deploying services..."
    # Deploy all services
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  DATABASE_URL: "postgresql://postgres:postgres@postgres-db-svc/pseudoscribe"
  OLLAMA_BASE_URL: "http://ollama-svc:11434"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: pseudoscribe/api:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:postgres@postgres-db-svc/pseudoscribe"
        - name: OLLAMA_BASE_URL
          value: "http://ollama-svc:11434"
---
apiVersion: v1
kind: Service
metadata:
  name: api-svc
spec:
  selector:
    app: api
  ports:
  - port: 8000
    targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-db
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-db
  template:
    metadata:
      labels:
        app: postgres-db
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: pseudoscribe
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          value: postgres
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-db-svc
spec:
  selector:
    app: postgres-db
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        volumeMounts:
        - name: ollama-storage
          mountPath: /root/.ollama
      volumes:
      - name: ollama-storage
        persistentVolumeClaim:
          claimName: ollama-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ollama-svc
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
EOF
}

# Wait for deployments
echo "[INFO] Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres-db
kubectl wait --for=condition=available --timeout=300s deployment/ollama  
kubectl wait --for=condition=available --timeout=300s deployment/api

# Setup database
echo "[INFO] Setting up database..."
./scripts/setup-container-db.sh

# Run comprehensive tests
echo "[INFO] Running comprehensive test suite..."
if ./scripts/test-full-suite.sh; then
    echo "🎉 Container development environment is fully functional!"
    echo ""
    echo "📊 DEVELOPMENT ENVIRONMENT STATUS:"
    echo "✅ Containers built and deployed"
    echo "✅ Database configured with test data"
    echo "✅ All services running and healthy"
    echo "✅ Comprehensive test suite passing"
    echo ""
    echo "🚀 Ready for development!"
    exit 0
else
    echo "⚠️ Some tests failed - environment partially functional"
    echo "Core functionality is working, minor issues may exist"
    exit 1
fi
