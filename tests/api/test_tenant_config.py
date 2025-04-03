"""BDD-style tests for tenant configuration API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from pseudoscribe.api.app import app

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
        
        # Clean up existing data
        conn.execute(text("DELETE FROM public.tenant_configurations"))
        conn.commit()
    
    yield
    
    # Clean up after tests
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM public.tenant_configurations"))
        conn.commit()

def test_create_tenant():
    """
    Scenario: Create new tenant configuration
    Given valid tenant configuration
    When creating tenant
    Then tenant is created successfully
    """
    # Given
    tenant_data = {
        "tenant_id": "test-tenant-1",
        "schema_name": "tenant_1",
        "display_name": "Test Tenant 1"
    }
    
    # When
    response = client.post("/tenants/", json=tenant_data)
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == tenant_data["tenant_id"]
    assert data["schema_name"] == tenant_data["schema_name"]
    assert data["display_name"] == tenant_data["display_name"]
    assert "created_at" in data

def test_create_duplicate_tenant():
    """
    Scenario: Create duplicate tenant configuration
    Given existing tenant configuration
    When creating tenant with same ID
    Then error is returned
    """
    # Given
    tenant_data = {
        "tenant_id": "test-tenant-1",
        "schema_name": "tenant_1"
    }
    client.post("/tenants/", json=tenant_data)
    
    # When
    response = client.post("/tenants/", json=tenant_data)
    
    # Then
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_tenant():
    """
    Scenario: Get tenant configuration
    Given existing tenant configuration
    When retrieving tenant
    Then tenant details are returned
    """
    # Given
    tenant_data = {
        "tenant_id": "test-tenant-1",
        "schema_name": "tenant_1"
    }
    client.post("/tenants/", json=tenant_data)
    
    # When
    response = client.get("/tenants/test-tenant-1")
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == tenant_data["tenant_id"]
    assert data["schema_name"] == tenant_data["schema_name"]

def test_get_nonexistent_tenant():
    """
    Scenario: Get nonexistent tenant configuration
    Given no tenant configuration
    When retrieving tenant
    Then error is returned
    """
    # When
    response = client.get("/tenants/nonexistent")
    
    # Then
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_list_tenants():
    """
    Scenario: List tenant configurations
    Given multiple tenant configurations
    When listing tenants
    Then all tenants are returned
    """
    # Given
    tenants = [
        {"tenant_id": "test-1", "schema_name": "tenant_1"},
        {"tenant_id": "test-2", "schema_name": "tenant_2"}
    ]
    for tenant in tenants:
        client.post("/tenants/", json=tenant)
    
    # When
    response = client.get("/tenants/")
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {t["tenant_id"] for t in data} == {"test-1", "test-2"}

def test_delete_tenant():
    """
    Scenario: Delete tenant configuration
    Given existing tenant configuration
    When deleting tenant
    Then tenant is removed
    """
    # Given
    tenant_data = {
        "tenant_id": "test-tenant-1",
        "schema_name": "tenant_1"
    }
    client.post("/tenants/", json=tenant_data)
    
    # When
    response = client.delete("/tenants/test-tenant-1")
    
    # Then
    assert response.status_code == 200
    get_response = client.get("/tenants/test-tenant-1")
    assert get_response.status_code == 404
