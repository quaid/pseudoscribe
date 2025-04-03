"""Middleware for handling tenant isolation"""

from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine, text
from starlette.datastructures import State

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to handle tenant isolation"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and ensure tenant isolation"""
        # Initialize request state if not exists
        if not hasattr(request, "state"):
            request.state = State()
            
        # Skip tenant check for tenant management endpoints
        if request.url.path.startswith("/tenants"):
            return await call_next(request)
            
        # Ensure tenant ID is provided
        tenant_id = get_tenant_id(request)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="X-Tenant-ID header is required"
            )
        
        # Validate tenant and get schema
        try:
            schema = await get_schema_for_tenant(tenant_id)
            request.state.schema = schema
            return await call_next(request)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

def get_tenant_id(request: Request) -> Optional[str]:
    """Get tenant ID from request header"""
    return request.headers.get("X-Tenant-ID")

async def get_schema_for_tenant(tenant_id: str) -> str:
    """Get schema name for tenant ID"""
    engine = create_engine("postgresql://localhost/pseudoscribe")
    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT schema_name FROM tenant_configurations WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        ).fetchone()
        
        if not result:
            raise ValueError("Tenant not found")
            
        return result[0]

def get_current_schema(request: Request) -> str:
    """Get current schema from request state"""
    if not hasattr(request, "state") or not hasattr(request.state, "schema"):
        raise HTTPException(
            status_code=500,
            detail="Schema not set in request state"
        )
    return request.state.schema
