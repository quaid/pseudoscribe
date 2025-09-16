"""FastAPI application for PseudoScribe"""

from fastapi import FastAPI

from pseudoscribe.api import tenant_config, role, style, vsc004_style
from pseudoscribe.infrastructure.tenant_middleware import TenantMiddleware

app = FastAPI(title="PseudoScribe API")
app.add_middleware(TenantMiddleware)


@app.get("/health", status_code=200)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Register routers
app.include_router(tenant_config.router)
app.include_router(role.router)
app.include_router(style.router)
app.include_router(vsc004_style.router)
