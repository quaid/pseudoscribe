"""Tenant configuration API endpoints"""

from fastapi import APIRouter, HTTPException

from pseudoscribe.infrastructure.tenant_config import (
    TenantConfigManager,
    TenantConfigCreate,
    TenantConfigResponse
)

router = APIRouter(prefix="/tenants", tags=["tenants"])

# Initialize tenant config manager
# TODO: Move connection string to config
manager = TenantConfigManager("postgresql://localhost/pseudoscribe")

@router.post("/", response_model=TenantConfigResponse)
async def create_tenant(config: TenantConfigCreate):
    """Create a new tenant configuration"""
    try:
        return await manager.create_tenant(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tenant_id}", response_model=TenantConfigResponse)
async def get_tenant(tenant_id: str):
    """Get tenant configuration by ID"""
    tenant = await manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.get("/", response_model=list[TenantConfigResponse])
async def list_tenants():
    """List all tenant configurations"""
    return await manager.list_tenants()

@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Delete a tenant configuration"""
    if not await manager.delete_tenant(tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"status": "success", "message": f"Tenant {tenant_id} deleted"}
