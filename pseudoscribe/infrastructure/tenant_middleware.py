"""Tenant isolation middleware"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import State
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from pseudoscribe.infrastructure.tenant_config import TenantConfigManager

# Initialize tenant config manager
manager = TenantConfigManager("postgresql://localhost/pseudoscribe")

def get_tenant_id(request: Request) -> str:
    """Extract tenant ID from request headers"""
    return request.headers.get("X-Tenant-ID")

def get_current_schema(request: Request) -> str:
    """Get current schema from request state"""
    if not hasattr(request.state, "schema"):
        raise HTTPException(status_code=500, detail="Schema not set")
    return request.state.schema

async def get_schema_for_tenant(tenant_id: str) -> str:
    """Get schema name for a tenant"""
    tenant = await manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant.schema_name

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for tenant isolation"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and ensure tenant isolation"""
        # Initialize request state if not exists
        if not hasattr(request, "state"):
            request.state = State()

        # Skip tenant check for tenant management and health endpoints
        if request.url.path.startswith(('/tenants', '/health', '/docs', '/redoc', '/openapi.json')):
            return await call_next(request)

        # Ensure tenant ID is provided
        tenant_id = get_tenant_id(request)
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="X-Tenant-ID header is required"
            )

        # Get schema for tenant
        try:
            schema = await get_schema_for_tenant(tenant_id)
            request.state.schema = schema
            return await call_next(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
