"""BDD-style tests for role management API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from pseudoscribe.api.app import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Set up test database before each test"""
    engine = create_engine("postgresql://localhost/pseudoscribe")
    
    # Create test tenant and schema
    with engine.connect() as conn:
        # Insert test tenant if not exists
        conn.execute(text("""
            INSERT INTO public.tenant_configurations (tenant_id, schema_name)
            VALUES ('test-tenant', 'tenant_test_tenant')
            ON CONFLICT (tenant_id) DO NOTHING
        """))
        conn.commit()
        
        # Create tenant schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS tenant_test_tenant"))
        conn.commit()
        
        # Create roles table in tenant schema
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tenant_test_tenant.roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
                tenant_id VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            )
        """))
        conn.commit()
    
    yield
    
    # Clean up
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS tenant_test_tenant CASCADE"))
        conn.commit()

@pytest.mark.asyncio
async def test_create_role():
    """
    Scenario: Create a new role
    Given a valid tenant
    When creating a role with valid data
    Then the role is created successfully
    """
    # Given
    headers = {"X-Tenant-ID": "test-tenant"}
    role_data = {
        "name": "Editor",
        "description": "Can edit and review content",
        "permissions": ["edit:content", "review:content"]
    }
    
    # When
    response = client.post("/roles/", headers=headers, json=role_data)
    
    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == role_data["name"]
    assert data["description"] == role_data["description"]
    assert data["permissions"] == role_data["permissions"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_duplicate_role():
    """
    Scenario: Create a duplicate role
    Given an existing role
    When creating a role with the same name in the same tenant
    Then an error is returned
    """
    # Given
    headers = {"X-Tenant-ID": "test-tenant"}
    role_data = {
        "name": "Editor",
        "description": "Can edit content",
        "permissions": ["edit:content"]
    }
    client.post("/roles/", headers=headers, json=role_data)
    
    # When
    response = client.post("/roles/", headers=headers, json=role_data)
    
    # Then
    assert response.status_code == 409
    assert "Role already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_role():
    """
    Scenario: Get role details
    Given an existing role
    When requesting role details
    Then role information is returned
    """
    # Given
    headers = {"X-Tenant-ID": "test-tenant"}
    role_data = {
        "name": "Editor",
        "description": "Can edit content",
        "permissions": ["edit:content"]
    }
    create_response = client.post("/roles/", headers=headers, json=role_data)
    role_id = create_response.json()["id"]
    
    # When
    response = client.get(f"/roles/{role_id}", headers=headers)
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == role_data["name"]
    assert data["description"] == role_data["description"]
    assert data["permissions"] == role_data["permissions"]

@pytest.mark.asyncio
async def test_list_roles():
    """
    Scenario: List all roles
    Given multiple existing roles
    When listing roles
    Then all roles for the tenant are returned
    """
    # Given
    headers = {"X-Tenant-ID": "test-tenant"}
    roles = [
        {
            "name": "Editor",
            "description": "Can edit content",
            "permissions": ["edit:content"]
        },
        {
            "name": "Reviewer",
            "description": "Can review content",
            "permissions": ["review:content"]
        }
    ]
    for role in roles:
        client.post("/roles/", headers=headers, json=role)
    
    # When
    response = client.get("/roles/", headers=headers)
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(roles)
    assert {role["name"] for role in data} == {role["name"] for role in roles}

@pytest.mark.asyncio
async def test_update_role():
    """
    Scenario: Update role details
    Given an existing role
    When updating role information
    Then the role is updated successfully
    """
    # Given
    headers = {"X-Tenant-ID": "test-tenant"}
    role_data = {
        "name": "Editor",
        "description": "Can edit content",
        "permissions": ["edit:content"]
    }
    create_response = client.post("/roles/", headers=headers, json=role_data)
    role_id = create_response.json()["id"]
    
    # When
    update_data = {
        "name": "Senior Editor",
        "description": "Can edit and publish content",
        "permissions": ["edit:content", "publish:content"]
    }
    response = client.put(f"/roles/{role_id}", headers=headers, json=update_data)
    
    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["permissions"] == update_data["permissions"]

@pytest.mark.asyncio
async def test_delete_role():
    """
    Scenario: Delete a role
    Given an existing role
    When deleting the role
    Then the role is removed successfully
    """
    # Given
    headers = {"X-Tenant-ID": "test-tenant"}
    role_data = {
        "name": "Editor",
        "description": "Can edit content",
        "permissions": ["edit:content"]
    }
    create_response = client.post("/roles/", headers=headers, json=role_data)
    role_id = create_response.json()["id"]
    
    # When
    response = client.delete(f"/roles/{role_id}", headers=headers)
    
    # Then
    assert response.status_code == 204
    
    # Verify role is deleted
    get_response = client.get(f"/roles/{role_id}", headers=headers)
    assert get_response.status_code == 404
