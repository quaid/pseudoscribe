#!/bin/sh
# wait-for-services.sh

set -e

# Wait for PostgreSQL
until nc -z -v -w30 postgres-db-svc 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

# Wait for Ollama
until nc -z -v -w30 ollama-svc 11434; do
  echo "Waiting for Ollama..."
  sleep 1
done

echo "All services are up - executing command"

exec "$@"
