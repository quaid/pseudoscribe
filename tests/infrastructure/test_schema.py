"""BDD Tests for Multi-tenant Schema Management"""

import pytest
import os
from pseudoscribe.infrastructure.schema import SchemaManager, TenantConfig

@pytest.mark.asyncio
class TestSchemaCreation:
    """
    Feature: Multi-tenant Schema
    As a system administrator
    I want to create isolated schemas for tenants
    So that each tenant's data remains secure and separate
    """
    
    async def test_schema_creation(self):
        """
        Scenario: Schema creation
        Given tenant onboarding request
        When creating schema
        Then isolated schema created
        And baseline tables added
        """
        # Given
        db_url = os.getenv("DATABASE_URL", "postgresql://localhost/pseudoscribe")
        manager = SchemaManager(db_url)
        tenant = TenantConfig(
            tenant_id="test-tenant-1",
            schema_name="tenant_1",
            display_name="Test Tenant 1"
        )
        
        # When
        schema_created = await manager.create_schema(tenant)
        tables_created = await manager.initialize_baseline_tables(tenant)
        
        # Then
        assert schema_created is True
        assert tables_created is True
        assert await manager.validate_schema_isolation(tenant) is True
    
    async def test_schema_isolation(self):
        """
        Scenario: Schema isolation verification
        Given multiple tenant schemas
        When accessing data
        Then data is isolated between tenants
        """
        # Given
        db_url = os.getenv("DATABASE_URL", "postgresql://localhost/pseudoscribe")
        manager = SchemaManager(db_url)
        tenant1 = TenantConfig(
            tenant_id="test-tenant-1",
            schema_name="tenant_1"
        )
        tenant2 = TenantConfig(
            tenant_id="test-tenant-2",
            schema_name="tenant_2"
        )
        
        # When
        await manager.create_schema(tenant1)
        await manager.create_schema(tenant2)
        
        # Then
        assert await manager.validate_schema_isolation(tenant1) is True
        assert await manager.validate_schema_isolation(tenant2) is True
