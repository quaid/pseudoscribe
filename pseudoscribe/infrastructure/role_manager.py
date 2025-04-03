"""Role management functionality"""

from datetime import datetime, UTC
from typing import List, Optional
import json

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from pseudoscribe.models.role import RoleCreate, RoleResponse, RoleUpdate

class RoleManager:
    """Manages role operations"""
    
    def __init__(self, database_url: str = "postgresql://localhost/pseudoscribe"):
        """Initialize role manager with database connection"""
        self.engine = create_engine(database_url)
    
    async def create_role(self, tenant_id: str, role: RoleCreate) -> RoleResponse:
        """Create a new role for a tenant"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO public.roles (name, description, permissions, tenant_id)
                        VALUES (:name, :description, cast(:permissions as jsonb), :tenant_id)
                        RETURNING id, name, description, permissions, tenant_id, created_at, updated_at
                    """),
                    {
                        "name": role.name,
                        "description": role.description,
                        "permissions": json.dumps(list(role.permissions)),  # Convert to JSON string
                        "tenant_id": tenant_id
                    }
                )
                conn.commit()
                row = result.fetchone()
                
                return RoleResponse(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    permissions=row.permissions,
                    tenant_id=row.tenant_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Role already exists")
    
    async def get_role(self, tenant_id: str, role_id: int) -> Optional[RoleResponse]:
        """Get a role by ID"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, name, description, permissions, tenant_id, created_at, updated_at
                    FROM public.roles
                    WHERE id = :role_id AND tenant_id = :tenant_id
                """),
                {"role_id": role_id, "tenant_id": tenant_id}
            )
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Role not found")
            
            return RoleResponse(
                id=row.id,
                name=row.name,
                description=row.description,
                permissions=row.permissions,
                tenant_id=row.tenant_id,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
    
    async def list_roles(self, tenant_id: str) -> List[RoleResponse]:
        """List all roles for a tenant"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, name, description, permissions, tenant_id, created_at, updated_at
                    FROM public.roles
                    WHERE tenant_id = :tenant_id
                    ORDER BY name
                """),
                {"tenant_id": tenant_id}
            )
            
            return [
                RoleResponse(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    permissions=row.permissions,
                    tenant_id=row.tenant_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                for row in result
            ]
    
    async def update_role(self, tenant_id: str, role_id: int, role: RoleUpdate) -> RoleResponse:
        """Update an existing role"""
        try:
            with self.engine.connect() as conn:
                # Get current role data
                current = conn.execute(
                    text("""
                        SELECT name, description, permissions
                        FROM public.roles
                        WHERE id = :role_id AND tenant_id = :tenant_id
                    """),
                    {"role_id": role_id, "tenant_id": tenant_id}
                ).fetchone()
                
                if not current:
                    raise HTTPException(status_code=404, detail="Role not found")
                
                # Update with new values or keep current ones
                result = conn.execute(
                    text("""
                        UPDATE public.roles
                        SET name = :name,
                            description = :description,
                            permissions = cast(:permissions as jsonb),
                            updated_at = :updated_at
                        WHERE id = :role_id AND tenant_id = :tenant_id
                        RETURNING id, name, description, permissions, tenant_id, created_at, updated_at
                    """),
                    {
                        "role_id": role_id,
                        "tenant_id": tenant_id,
                        "name": role.name or current.name,
                        "description": role.description or current.description,
                        "permissions": json.dumps(list(role.permissions)) if role.permissions is not None else json.dumps(current.permissions),
                        "updated_at": datetime.now(UTC)
                    }
                )
                conn.commit()
                row = result.fetchone()
                
                return RoleResponse(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    permissions=row.permissions,
                    tenant_id=row.tenant_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Role name already exists")
    
    async def delete_role(self, tenant_id: str, role_id: int) -> None:
        """Delete a role"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM public.roles
                    WHERE id = :role_id AND tenant_id = :tenant_id
                    RETURNING id
                """),
                {"role_id": role_id, "tenant_id": tenant_id}
            )
            conn.commit()
            
            if not result.rowcount:
                raise HTTPException(status_code=404, detail="Role not found")
