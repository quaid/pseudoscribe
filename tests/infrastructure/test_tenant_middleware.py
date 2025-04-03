"""BDD-style tests for tenant isolation middleware"""

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from starlette.datastructures import State

from pseudoscribe.infrastructure.tenant_middleware import (
    TenantMiddleware,
    get_tenant_id,
    get_current_schema,
    get_schema_for_tenant
)

# Test app setup
app = FastAPI()
app.add_middleware(TenantMiddleware)

@app.get("/test")
async def test_endpoint(schema: str = Depends(get_current_schema)):
    return {"schema": schema}

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Set up test database before each test"""
    engine = create_engine("postgresql://localhost/pseudoscribe")
    
    # Create tenant_configurations table
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.tenant_configurations (
                tenant_id VARCHAR(255) PRIMARY KEY,
                schema_name VARCHAR(255) UNIQUE,
                display_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        
        # Insert test tenant
        conn.execute(text("""
            INSERT INTO public.tenant_configurations (tenant_id, schema_name)
            VALUES ('test-tenant', 'tenant_1')
            ON CONFLICT (tenant_id) DO NOTHING
        """))
        conn.commit()
    
    yield
    
    # Clean up
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM public.tenant_configurations"))
        conn.commit()

@pytest.mark.asyncio
async def test_valid_tenant_header():
    """
    Scenario: Request with valid tenant header
    Given a valid tenant ID in header
    When making an API request
    Then correct schema is returned
    """
    # Given/When
    response = client.get("/test", headers={"X-Tenant-ID": "test-tenant"})
    
    # Then
    assert response.status_code == 200
    assert response.json()["schema"] == "tenant_1"

@pytest.mark.asyncio
async def test_missing_tenant_header():
    """
    Scenario: Request without tenant header
    Given no tenant ID in header
    When making an API request
    Then error is returned
    """
    # Given/When
    with pytest.raises(HTTPException) as exc_info:
        response = client.get("/test")
    
    # Then
    assert exc_info.value.status_code == 400
    assert "X-Tenant-ID header is required" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_invalid_tenant_header():
    """
    Scenario: Request with invalid tenant header
    Given invalid tenant ID in header
    When making an API request
    Then error is returned
    """
    # Given/When
    with pytest.raises(HTTPException) as exc_info:
        response = client.get("/test", headers={"X-Tenant-ID": "nonexistent"})
    
    # Then
    assert exc_info.value.status_code == 404
    assert "Tenant not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_tenant_id():
    """
    Scenario: Extract tenant ID from request
    Given request with tenant header
    When extracting tenant ID
    Then correct ID is returned
    """
    # Given
    request = client.get("/test", headers={"X-Tenant-ID": "test-tenant"}).request
    
    # When
    tenant_id = get_tenant_id(request)
    
    # Then
    assert tenant_id == "test-tenant"

@pytest.mark.asyncio
async def test_get_schema_for_tenant():
    """
    Scenario: Get schema for tenant
    Given valid tenant ID
    When getting schema
    Then correct schema name is returned
    """
    # Given/When
    schema = await get_schema_for_tenant("test-tenant")
    
    # Then
    assert schema == "tenant_1"

@pytest.mark.asyncio
async def test_get_current_schema():
    """
    Scenario: Get current schema for tenant
    Given valid tenant ID
    When getting schema
    Then correct schema name is returned
    """
    # Given
    request = client.get("/test", headers={"X-Tenant-ID": "test-tenant"}).request
    request.state = State()
    request.state.schema = "tenant_1"
    
    # When
    schema = get_current_schema(request)
    
    # Then
    assert schema == "tenant_1"

@pytest.mark.asyncio
async def test_get_current_schema_missing():
    """
    Scenario: Get current schema when not set
    Given request without schema
    When getting schema
    Then error is returned
    """
    # Given
    request = client.get("/test", headers={"X-Tenant-ID": "test-tenant"}).request
    request.state = State()
    
    # When/Then
    with pytest.raises(HTTPException) as exc_info:
        get_current_schema(request)
    
    assert exc_info.value.status_code == 500
    assert "Schema not set" in str(exc_info.value.detail)
