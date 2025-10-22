"""FastAPI application for PseudoScribe"""

from fastapi import FastAPI

from pseudoscribe.api import tenant_config, role, style, advanced_style, live_suggestions, collaboration, performance, ollama_integration
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
app.include_router(advanced_style.router)
app.include_router(live_suggestions.router)
app.include_router(collaboration.router)
app.include_router(performance.router)
app.include_router(ollama_integration.router)
