"""Tests for Extended Tenant Configuration.

Issue: IF-002 - Tenant Configuration API

These tests verify:
- Tenant settings management (key-value storage)
- Encrypted credential storage for connectors
- Configuration updates
- Settings validation
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from pseudoscribe.infrastructure.tenant_config_service import (
    TenantConfigService,
    TenantSettings,
    ConnectorCredentials,
    CredentialType,
    SettingsValidationError
)


class TestTenantSettings:
    """Tests for tenant settings management."""

    @pytest.fixture
    def config_service(self):
        """Create a TenantConfigService instance."""
        return TenantConfigService()

    def test_set_setting(self, config_service):
        """Test setting a configuration value."""
        # Arrange
        tenant_id = "tenant-123"
        key = "theme"
        value = "dark"

        # Act
        config_service.set_setting(tenant_id, key, value)

        # Assert
        result = config_service.get_setting(tenant_id, key)
        assert result == value

    def test_get_setting_default(self, config_service):
        """Test getting a setting with default value."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        result = config_service.get_setting(tenant_id, "nonexistent", default="fallback")

        # Assert
        assert result == "fallback"

    def test_get_setting_not_found(self, config_service):
        """Test getting a nonexistent setting without default."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        result = config_service.get_setting(tenant_id, "nonexistent")

        # Assert
        assert result is None

    def test_set_complex_setting(self, config_service):
        """Test setting a complex (dict) configuration value."""
        # Arrange
        tenant_id = "tenant-123"
        key = "style_preferences"
        value = {
            "default_profile": "formal",
            "auto_adapt": True,
            "confidence_threshold": 0.85
        }

        # Act
        config_service.set_setting(tenant_id, key, value)

        # Assert
        result = config_service.get_setting(tenant_id, key)
        assert result == value
        assert result["default_profile"] == "formal"
        assert result["auto_adapt"] is True

    def test_get_all_settings(self, config_service):
        """Test getting all settings for a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.set_setting(tenant_id, "theme", "dark")
        config_service.set_setting(tenant_id, "language", "en")
        config_service.set_setting(tenant_id, "timezone", "UTC")

        # Act
        settings = config_service.get_all_settings(tenant_id)

        # Assert
        assert len(settings) == 3
        assert settings["theme"] == "dark"
        assert settings["language"] == "en"
        assert settings["timezone"] == "UTC"

    def test_delete_setting(self, config_service):
        """Test deleting a setting."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.set_setting(tenant_id, "temp_key", "temp_value")

        # Act
        result = config_service.delete_setting(tenant_id, "temp_key")

        # Assert
        assert result is True
        assert config_service.get_setting(tenant_id, "temp_key") is None

    def test_delete_nonexistent_setting(self, config_service):
        """Test deleting a nonexistent setting."""
        # Arrange
        tenant_id = "tenant-123"

        # Act
        result = config_service.delete_setting(tenant_id, "nonexistent")

        # Assert
        assert result is False

    def test_update_setting(self, config_service):
        """Test updating an existing setting."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.set_setting(tenant_id, "theme", "light")

        # Act
        config_service.set_setting(tenant_id, "theme", "dark")

        # Assert
        assert config_service.get_setting(tenant_id, "theme") == "dark"

    def test_tenant_isolation(self, config_service):
        """Test that settings are isolated between tenants."""
        # Arrange
        tenant_a = "tenant-A"
        tenant_b = "tenant-B"

        # Act
        config_service.set_setting(tenant_a, "theme", "dark")
        config_service.set_setting(tenant_b, "theme", "light")

        # Assert
        assert config_service.get_setting(tenant_a, "theme") == "dark"
        assert config_service.get_setting(tenant_b, "theme") == "light"


class TestConnectorCredentials:
    """Tests for encrypted connector credential storage."""

    @pytest.fixture
    def config_service(self):
        return TenantConfigService()

    def test_store_strapi_credentials(self, config_service):
        """Test storing Strapi connector credentials."""
        # Arrange
        tenant_id = "tenant-123"
        credentials = ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="production-strapi",
            api_url="https://cms.example.com",
            api_token="strapi_token_abc123"
        )

        # Act
        cred_id = config_service.store_credentials(tenant_id, credentials)

        # Assert
        assert cred_id is not None
        stored = config_service.get_credentials(tenant_id, cred_id)
        assert stored.name == "production-strapi"
        assert stored.api_url == "https://cms.example.com"
        # Token should be retrievable but stored encrypted
        assert stored.api_token == "strapi_token_abc123"

    def test_store_google_credentials(self, config_service):
        """Test storing Google Docs connector credentials."""
        # Arrange
        tenant_id = "tenant-123"
        credentials = ConnectorCredentials(
            credential_type=CredentialType.GOOGLE_DOCS,
            name="company-gdocs",
            service_account_json='{"type": "service_account", "project_id": "test"}'
        )

        # Act
        cred_id = config_service.store_credentials(tenant_id, credentials)

        # Assert
        stored = config_service.get_credentials(tenant_id, cred_id)
        assert stored.credential_type == CredentialType.GOOGLE_DOCS
        assert stored.name == "company-gdocs"

    def test_list_credentials(self, config_service):
        """Test listing all credentials for a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="strapi-1",
            api_url="https://cms1.example.com",
            api_token="token1"
        ))
        config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="strapi-2",
            api_url="https://cms2.example.com",
            api_token="token2"
        ))

        # Act
        creds = config_service.list_credentials(tenant_id)

        # Assert
        assert len(creds) == 2
        names = [c.name for c in creds]
        assert "strapi-1" in names
        assert "strapi-2" in names

    def test_list_credentials_by_type(self, config_service):
        """Test listing credentials filtered by type."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="strapi-1",
            api_url="https://cms.example.com",
            api_token="token"
        ))
        config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.GOOGLE_DOCS,
            name="gdocs-1",
            service_account_json='{}'
        ))

        # Act
        strapi_creds = config_service.list_credentials(
            tenant_id,
            credential_type=CredentialType.STRAPI
        )

        # Assert
        assert len(strapi_creds) == 1
        assert strapi_creds[0].name == "strapi-1"

    def test_delete_credentials(self, config_service):
        """Test deleting credentials."""
        # Arrange
        tenant_id = "tenant-123"
        cred_id = config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="to-delete",
            api_url="https://delete.example.com",
            api_token="token"
        ))

        # Act
        result = config_service.delete_credentials(tenant_id, cred_id)

        # Assert
        assert result is True
        assert config_service.get_credentials(tenant_id, cred_id) is None

    def test_update_credentials(self, config_service):
        """Test updating existing credentials."""
        # Arrange
        tenant_id = "tenant-123"
        cred_id = config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="my-strapi",
            api_url="https://old.example.com",
            api_token="old_token"
        ))

        # Act
        updated = ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="my-strapi",
            api_url="https://new.example.com",
            api_token="new_token"
        )
        config_service.update_credentials(tenant_id, cred_id, updated)

        # Assert
        stored = config_service.get_credentials(tenant_id, cred_id)
        assert stored.api_url == "https://new.example.com"
        assert stored.api_token == "new_token"

    def test_credentials_not_exposed_in_list(self, config_service):
        """Test that sensitive data is masked in list operations."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.store_credentials(tenant_id, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="secure-strapi",
            api_url="https://cms.example.com",
            api_token="super_secret_token"
        ))

        # Act
        creds = config_service.list_credentials(tenant_id, mask_secrets=True)

        # Assert
        assert len(creds) == 1
        assert creds[0].api_token == "***masked***"
        assert creds[0].api_url == "https://cms.example.com"  # URL not sensitive

    def test_credential_tenant_isolation(self, config_service):
        """Test that credentials are isolated between tenants."""
        # Arrange
        tenant_a = "tenant-A"
        tenant_b = "tenant-B"

        cred_id_a = config_service.store_credentials(tenant_a, ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="tenant-a-strapi",
            api_url="https://a.example.com",
            api_token="token_a"
        ))

        # Act & Assert
        assert config_service.get_credentials(tenant_a, cred_id_a) is not None
        assert config_service.get_credentials(tenant_b, cred_id_a) is None


class TestSettingsValidation:
    """Tests for settings validation."""

    @pytest.fixture
    def config_service(self):
        return TenantConfigService()

    def test_validate_required_settings(self, config_service):
        """Test validation of required settings."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.set_setting(tenant_id, "api_url", "https://api.example.com")
        # Missing required 'api_key'

        required = ["api_url", "api_key"]

        # Act & Assert
        with pytest.raises(SettingsValidationError) as exc_info:
            config_service.validate_settings(tenant_id, required=required)

        assert "api_key" in str(exc_info.value)

    def test_validate_all_present(self, config_service):
        """Test validation passes when all required settings present."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.set_setting(tenant_id, "api_url", "https://api.example.com")
        config_service.set_setting(tenant_id, "api_key", "key123")

        required = ["api_url", "api_key"]

        # Act & Assert - should not raise
        config_service.validate_settings(tenant_id, required=required)


class TestTenantSettingsModel:
    """Tests for TenantSettings model."""

    def test_tenant_settings_creation(self):
        """Test creating a TenantSettings model."""
        # Act
        settings = TenantSettings(
            tenant_id="tenant-123",
            settings={"theme": "dark", "language": "en"}
        )

        # Assert
        assert settings.tenant_id == "tenant-123"
        assert settings.settings["theme"] == "dark"

    def test_tenant_settings_defaults(self):
        """Test TenantSettings with default values."""
        # Act
        settings = TenantSettings(tenant_id="tenant-123")

        # Assert
        assert settings.settings == {}


class TestBulkOperations:
    """Tests for bulk settings operations."""

    @pytest.fixture
    def config_service(self):
        return TenantConfigService()

    def test_set_multiple_settings(self, config_service):
        """Test setting multiple settings at once."""
        # Arrange
        tenant_id = "tenant-123"
        settings = {
            "theme": "dark",
            "language": "en",
            "timezone": "UTC",
            "notifications": True
        }

        # Act
        config_service.set_settings_bulk(tenant_id, settings)

        # Assert
        all_settings = config_service.get_all_settings(tenant_id)
        assert all_settings == settings

    def test_clear_all_settings(self, config_service):
        """Test clearing all settings for a tenant."""
        # Arrange
        tenant_id = "tenant-123"
        config_service.set_setting(tenant_id, "key1", "value1")
        config_service.set_setting(tenant_id, "key2", "value2")

        # Act
        config_service.clear_settings(tenant_id)

        # Assert
        all_settings = config_service.get_all_settings(tenant_id)
        assert len(all_settings) == 0
