"""Role management API endpoints"""

from typing import List

from fastapi import APIRouter, Depends, Response, status

from pseudoscribe.infrastructure.role_manager import RoleManager
from pseudoscribe.infrastructure.tenant_middleware import get_tenant_id
from pseudoscribe.models.role import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])
role_manager = RoleManager()

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, tenant_id: str = Depends(get_tenant_id)) -> RoleResponse:
    """Create a new role"""
    return await role_manager.create_role(tenant_id, role)

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, tenant_id: str = Depends(get_tenant_id)) -> RoleResponse:
    """Get role details"""
    return await role_manager.get_role(tenant_id, role_id)

@router.get("/", response_model=List[RoleResponse])
async def list_roles(tenant_id: str = Depends(get_tenant_id)) -> List[RoleResponse]:
    """List all roles"""
    return await role_manager.list_roles(tenant_id)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role: RoleUpdate, tenant_id: str = Depends(get_tenant_id)) -> RoleResponse:
    """Update role details"""
    return await role_manager.update_role(tenant_id, role_id, role)

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: int, tenant_id: str = Depends(get_tenant_id)) -> Response:
    """Delete a role"""
    await role_manager.delete_role(tenant_id, role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
