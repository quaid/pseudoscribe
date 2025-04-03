"""FastAPI application for PseudoScribe"""

from fastapi import FastAPI

from pseudoscribe.api import tenant_config, role
from pseudoscribe.infrastructure.tenant_middleware import TenantMiddleware

app = FastAPI(title="PseudoScribe API")
app.add_middleware(TenantMiddleware)

# Register routers
app.include_router(tenant_config.router)
app.include_router(role.router)
