"""Role management models and schemas"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class RoleCreate(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., description="Name of the role")
    description: Optional[str] = Field(None, description="Description of the role's purpose")
    permissions: List[str] = Field(default_factory=list, description="List of permission strings")

class RoleUpdate(BaseModel):
    """Schema for updating an existing role"""
    name: Optional[str] = Field(None, description="New name for the role")
    description: Optional[str] = Field(None, description="New description for the role")
    permissions: Optional[List[str]] = Field(None, description="Updated list of permissions")

class RoleResponse(BaseModel):
    """Schema for role response"""
    id: int = Field(..., description="Unique identifier for the role")
    name: str = Field(..., description="Name of the role")
    description: Optional[str] = Field(None, description="Description of the role's purpose")
    permissions: List[str] = Field(..., description="List of permission strings")
    tenant_id: str = Field(..., description="ID of the tenant this role belongs to")
    created_at: datetime = Field(..., description="When the role was created")
    updated_at: datetime = Field(..., description="When the role was last updated")
