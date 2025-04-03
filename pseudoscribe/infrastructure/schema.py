"""Multi-tenant Schema Management for PseudoScribe"""

from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from pydantic import BaseModel

class TenantConfig(BaseModel):
    """Configuration for a tenant's schema"""
    tenant_id: str
    schema_name: str
    display_name: Optional[str] = None

class SchemaManager:
    """Manages tenant schema creation and isolation"""
    
    def __init__(self, connection_string: str):
        """Initialize with database connection string"""
        self.engine = create_engine(connection_string)
    
    async def create_schema(self, tenant: TenantConfig) -> bool:
        """
        Create an isolated schema for a tenant
        
        Args:
            tenant: TenantConfig with tenant details
            
        Returns:
            bool: True if schema created successfully
            
        Raises:
            SchemaError: If schema creation fails
        """
        with self.engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {tenant.schema_name}"))
            conn.commit()
            
            # Initialize baseline tables
            await self.initialize_baseline_tables(tenant)
            
            # Validate schema isolation
            return await self.validate_schema_isolation(tenant)
    
    async def initialize_baseline_tables(self, tenant: TenantConfig) -> bool:
        """
        Create baseline tables in tenant schema
        
        Args:
            tenant: TenantConfig with tenant details
            
        Returns:
            bool: True if tables created successfully
            
        Raises:
            SchemaError: If table creation fails
        """
        with self.engine.connect() as conn:
            # Create tenant info table
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {tenant.schema_name}.tenant_info (
                    tenant_id VARCHAR(255) PRIMARY KEY,
                    display_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create roles table
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {tenant.schema_name}.roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
                    tenant_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (name)
                )
            """))
            
            # Insert tenant info
            conn.execute(text(f"""
                INSERT INTO {tenant.schema_name}.tenant_info (tenant_id, display_name)
                VALUES (:tenant_id, :display_name)
                ON CONFLICT (tenant_id) DO UPDATE
                SET display_name = EXCLUDED.display_name
            """), {
                "tenant_id": tenant.tenant_id,
                "display_name": tenant.display_name
            })
            
            conn.commit()
            return True
    
    async def validate_schema_isolation(self, tenant: TenantConfig) -> bool:
        """
        Verify schema isolation for tenant
        
        Args:
            tenant: TenantConfig with tenant details
            
        Returns:
            bool: True if schema is properly isolated
        """
        with self.engine.connect() as conn:
            # Check if schema exists
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = :schema_name
            """), {
                "schema_name": tenant.schema_name
            })
            
            if not result.fetchone():
                return False
            
            # Check if tenant_info table exists and contains correct tenant_id
            result = conn.execute(text(f"""
                SELECT tenant_id 
                FROM {tenant.schema_name}.tenant_info 
                WHERE tenant_id = :tenant_id
            """), {
                "tenant_id": tenant.tenant_id
            })
            
            return bool(result.fetchone())
