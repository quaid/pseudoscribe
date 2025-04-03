"""Tenant Configuration Management for PseudoScribe"""

from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class TenantConfigCreate(BaseModel):
    """Request model for creating a new tenant configuration"""
    tenant_id: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9-]+$")
    schema_name: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9_]+$")
    display_name: Optional[str] = Field(None, max_length=100)

class TenantConfigResponse(BaseModel):
    """Response model for tenant configuration"""
    tenant_id: str
    schema_name: str
    display_name: Optional[str]
    created_at: str

class TenantConfigManager:
    """Manages tenant configurations"""
    
    def __init__(self, connection_string: str):
        """Initialize with database connection string"""
        self.engine = create_engine(connection_string)
    
    async def create_tenant(self, config: TenantConfigCreate) -> TenantConfigResponse:
        """
        Create a new tenant configuration
        
        Args:
            config: TenantConfigCreate with tenant details
            
        Returns:
            TenantConfigResponse with created tenant details
            
        Raises:
            ValueError: If tenant_id or schema_name already exists
        """
        with self.engine.connect() as conn:
            # Check if tenant_id or schema_name already exists
            result = conn.execute(text("""
                SELECT tenant_id, schema_name 
                FROM public.tenant_configurations 
                WHERE tenant_id = :tenant_id OR schema_name = :schema_name
            """), {
                "tenant_id": config.tenant_id,
                "schema_name": config.schema_name
            })
            
            if result.fetchone():
                raise ValueError("Tenant ID or schema name already exists")
            
            # Insert new tenant configuration
            result = conn.execute(text("""
                INSERT INTO public.tenant_configurations 
                (tenant_id, schema_name, display_name)
                VALUES (:tenant_id, :schema_name, :display_name)
                RETURNING tenant_id, schema_name, display_name, created_at
            """), config.model_dump())
            
            conn.commit()
            row = result.fetchone()
            
            return TenantConfigResponse(
                tenant_id=row.tenant_id,
                schema_name=row.schema_name,
                display_name=row.display_name,
                created_at=str(row.created_at)
            )
    
    async def get_tenant(self, tenant_id: str) -> Optional[TenantConfigResponse]:
        """
        Get tenant configuration by ID
        
        Args:
            tenant_id: ID of the tenant
            
        Returns:
            TenantConfigResponse if found, None otherwise
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tenant_id, schema_name, display_name, created_at
                FROM public.tenant_configurations 
                WHERE tenant_id = :tenant_id
            """), {"tenant_id": tenant_id})
            
            row = result.fetchone()
            if not row:
                return None
                
            return TenantConfigResponse(
                tenant_id=row.tenant_id,
                schema_name=row.schema_name,
                display_name=row.display_name,
                created_at=str(row.created_at)
            )
    
    async def list_tenants(self) -> List[TenantConfigResponse]:
        """
        List all tenant configurations
        
        Returns:
            List of TenantConfigResponse objects
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tenant_id, schema_name, display_name, created_at
                FROM public.tenant_configurations
                ORDER BY created_at DESC
            """))
            
            return [
                TenantConfigResponse(
                    tenant_id=row.tenant_id,
                    schema_name=row.schema_name,
                    display_name=row.display_name,
                    created_at=str(row.created_at)
                )
                for row in result
            ]
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant configuration
        
        Args:
            tenant_id: ID of the tenant to delete
            
        Returns:
            bool: True if tenant was deleted, False if not found
            
        Raises:
            SQLAlchemyError: If deletion fails
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM public.tenant_configurations 
                WHERE tenant_id = :tenant_id
                RETURNING tenant_id
            """), {"tenant_id": tenant_id})
            
            conn.commit()
            return bool(result.fetchone())
