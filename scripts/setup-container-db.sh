#!/bin/bash
set -e

echo "🗄️ Setting up container database for development..."

# Function to setup database tables
setup_database() {
    echo "📋 Creating necessary database tables..."
    
    kubectl exec deployment/api -- python -c "
from pseudoscribe.api.dependencies import SessionLocal
from sqlalchemy import text
import sys

db = SessionLocal()
try:
    # Create tenant_configurations table
    print('Creating tenant_configurations table...')
    db.execute(text('''
        CREATE TABLE IF NOT EXISTS public.tenant_configurations (
            tenant_id VARCHAR(255) PRIMARY KEY,
            schema_name VARCHAR(255) NOT NULL UNIQUE,
            display_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    '''))
    
    # Insert test tenant
    print('Inserting test tenant...')
    db.execute(text('''
        INSERT INTO public.tenant_configurations (tenant_id, schema_name, display_name)
        VALUES ('test-tenant', 'test_tenant_schema', 'Test Tenant')
        ON CONFLICT (tenant_id) DO NOTHING;
    '''))
    
    # Create any other necessary tables for development
    print('Creating additional development tables...')
    
    db.commit()
    print('✅ Database setup completed successfully')
    
except Exception as e:
    print(f'❌ Database setup failed: {e}')
    db.rollback()
    sys.exit(1)
finally:
    db.close()
"
}

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment/postgres-db

# Setup database
setup_database

echo "🎉 Container database setup complete!"
