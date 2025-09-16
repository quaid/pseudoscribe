"""Tenant configuration API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pseudoscribe.api.dependencies import get_db
from pseudoscribe.api.dependencies import get_tenant_config_manager
from pseudoscribe.infrastructure.tenant_config import (
    TenantConfigManager,
    TenantConfigCreate,
    TenantConfigResponse
)

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/", response_model=TenantConfigResponse)
async def create_tenant(
    tenant: TenantConfigCreate, 
    db: Session = Depends(get_db),
    manager: TenantConfigManager = Depends(get_tenant_config_manager)
):
    """Create a new tenant configuration"""
    try:
        return await manager.create_tenant(db, tenant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tenant_id}", response_model=TenantConfigResponse)
async def get_tenant(
    tenant_id: str, 
    db: Session = Depends(get_db),
    manager: TenantConfigManager = Depends(get_tenant_config_manager)
):
    """Get tenant configuration by ID"""
    tenant = await manager.get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.get("/", response_model=list[TenantConfigResponse])
async def list_tenants(
    db: Session = Depends(get_db), 
    manager: TenantConfigManager = Depends(get_tenant_config_manager)
):
    """List all tenant configurations"""
    return await manager.list_tenants(db)

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str, 
    db: Session = Depends(get_db),
    manager: TenantConfigManager = Depends(get_tenant_config_manager)
):
    """Delete a tenant configuration"""
    if not await manager.delete_tenant(db, tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"status": "success", "message": f"Tenant {tenant_id} deleted"}
