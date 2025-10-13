#!/bin/bash
set -e

echo "🚀 Starting improved Rancher test execution..."

# Build and deploy services (reuse existing logic)
echo "[INFO] Building API container image..."
nerdctl build -t pseudoscribe/api:latest .

echo "[INFO] Building VSCode extension test container image..."
nerdctl build -t pseudoscribe/vscode-extension-test:latest -f vscode-extension/Dockerfile vscode-extension/

echo "[SUCCESS] All images built and loaded successfully"

# Clean up any existing resources
echo "[INFO] Cleaning up existing resources..."
kubectl delete job backend-test --ignore-not-found=true
kubectl delete job vscode-extension-test --ignore-not-found=true
kubectl delete deployment,service,pvc --all --ignore-not-found=true

echo "[INFO] Deploying all services to Kubernetes..."

# Deploy services (reuse existing deployment logic)
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

echo "[SUCCESS] Services deployed successfully"

echo "[INFO] Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres-db
kubectl wait --for=condition=available --timeout=300s deployment/ollama  
kubectl wait --for=condition=available --timeout=300s deployment/api

echo "[SUCCESS] All deployments are ready"

echo "[INFO] Running backend tests using batch approach..."

# Use our improved batch testing approach
if ./scripts/test-ollama-batch.sh; then
    echo "[SUCCESS] Backend tests completed successfully"
    test_result=0
else
    echo "[ERROR] Backend tests failed"
    test_result=1
fi

echo "[INFO] Running VSCode extension tests..."
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: vscode-extension-test
spec:
  template:
    spec:
      containers:
      - name: vscode-extension-test
        image: pseudoscribe/vscode-extension-test:latest
        imagePullPolicy: Never
        command: ["/app/run-tests.sh"]
      restartPolicy: Never
  backoffLimit: 0
EOF

if kubectl wait --for=condition=complete --timeout=2m job/vscode-extension-test; then
    echo "[SUCCESS] VSCode extension tests completed"
    kubectl logs job/vscode-extension-test
else
    echo "[ERROR] VSCode extension tests failed or timed out"
    kubectl logs job/vscode-extension-test
    test_result=1
fi

if [ $test_result -eq 0 ]; then
    echo "🎉 ALL TESTS COMPLETED SUCCESSFULLY!"
else
    echo "❌ Some tests failed"
fi

exit $test_result
