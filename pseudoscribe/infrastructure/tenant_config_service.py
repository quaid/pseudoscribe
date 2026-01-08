"""Extended Tenant Configuration Service.

Issue: IF-002 - Tenant Configuration API

This module provides extended tenant configuration including:
- Key-value settings storage per tenant
- Encrypted credential storage for connectors
- Settings validation
- Bulk operations
"""

import json
import uuid
import base64
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict


class CredentialType(Enum):
    """Types of connector credentials."""
    STRAPI = "strapi"
    GOOGLE_DOCS = "google_docs"
    CUSTOM = "custom"


class SettingsValidationError(Exception):
    """Raised when settings validation fails."""

    def __init__(self, missing_keys: List[str]):
        self.missing_keys = missing_keys
        super().__init__(f"Missing required settings: {', '.join(missing_keys)}")


@dataclass
class TenantSettings:
    """Model for tenant settings."""
    tenant_id: str
    settings: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConnectorCredentials:
    """Model for connector credentials."""
    credential_type: CredentialType
    name: str
    api_url: Optional[str] = None
    api_token: Optional[str] = None
    service_account_json: Optional[str] = None
    additional_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    credential_id: Optional[str] = None

    def mask_secrets(self) -> 'ConnectorCredentials':
        """Return a copy with secrets masked."""
        return ConnectorCredentials(
            credential_type=self.credential_type,
            name=self.name,
            api_url=self.api_url,
            api_token="***masked***" if self.api_token else None,
            service_account_json="***masked***" if self.service_account_json else None,
            additional_config=self.additional_config,
            created_at=self.created_at,
            credential_id=self.credential_id
        )


class TenantConfigService:
    """Extended tenant configuration service with settings and credentials."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize the tenant config service.

        Args:
            encryption_key: Optional key for encrypting credentials.
                           If not provided, uses a default (for dev only).
        """
        self._settings: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._credentials: Dict[str, Dict[str, ConnectorCredentials]] = defaultdict(dict)
        # In production, this would use a proper encryption key from env/secrets
        self._encryption_key = encryption_key or "dev-key-do-not-use-in-prod"

    def _encrypt(self, value: str) -> str:
        """Encrypt a sensitive value.

        Note: This is a simple implementation. In production, use proper
        encryption like Fernet or AWS KMS.
        """
        # Simple XOR-based obfuscation for demo. Replace with real encryption.
        key_bytes = hashlib.sha256(self._encryption_key.encode()).digest()
        value_bytes = value.encode()
        encrypted = bytes(v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(value_bytes))
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted: str) -> str:
        """Decrypt an encrypted value."""
        key_bytes = hashlib.sha256(self._encryption_key.encode()).digest()
        encrypted_bytes = base64.b64decode(encrypted.encode())
        decrypted = bytes(v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(encrypted_bytes))
        return decrypted.decode()

    # ========== Settings Management ==========

    def set_setting(
        self,
        tenant_id: str,
        key: str,
        value: Any
    ) -> None:
        """Set a configuration value for a tenant.

        Args:
            tenant_id: The tenant to set the setting for
            key: Setting key
            value: Setting value (can be any JSON-serializable type)
        """
        self._settings[tenant_id][key] = value

    def get_setting(
        self,
        tenant_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get a configuration value for a tenant.

        Args:
            tenant_id: The tenant to get the setting for
            key: Setting key
            default: Default value if setting doesn't exist

        Returns:
            The setting value or default
        """
        return self._settings.get(tenant_id, {}).get(key, default)

    def get_all_settings(self, tenant_id: str) -> Dict[str, Any]:
        """Get all settings for a tenant.

        Args:
            tenant_id: The tenant to get settings for

        Returns:
            Dictionary of all settings
        """
        return dict(self._settings.get(tenant_id, {}))

    def delete_setting(self, tenant_id: str, key: str) -> bool:
        """Delete a setting for a tenant.

        Args:
            tenant_id: The tenant to delete the setting for
            key: Setting key to delete

        Returns:
            True if deleted, False if not found
        """
        if tenant_id in self._settings and key in self._settings[tenant_id]:
            del self._settings[tenant_id][key]
            return True
        return False

    def set_settings_bulk(
        self,
        tenant_id: str,
        settings: Dict[str, Any]
    ) -> None:
        """Set multiple settings at once.

        Args:
            tenant_id: The tenant to set settings for
            settings: Dictionary of settings to set
        """
        for key, value in settings.items():
            self._settings[tenant_id][key] = value

    def clear_settings(self, tenant_id: str) -> None:
        """Clear all settings for a tenant.

        Args:
            tenant_id: The tenant to clear settings for
        """
        self._settings[tenant_id] = {}

    def validate_settings(
        self,
        tenant_id: str,
        required: List[str]
    ) -> None:
        """Validate that required settings are present.

        Args:
            tenant_id: The tenant to validate
            required: List of required setting keys

        Raises:
            SettingsValidationError: If any required settings are missing
        """
        current_settings = self._settings.get(tenant_id, {})
        missing = [key for key in required if key not in current_settings]

        if missing:
            raise SettingsValidationError(missing)

    # ========== Credential Management ==========

    def store_credentials(
        self,
        tenant_id: str,
        credentials: ConnectorCredentials
    ) -> str:
        """Store connector credentials for a tenant.

        Args:
            tenant_id: The tenant storing credentials
            credentials: The credentials to store

        Returns:
            Credential ID for retrieval
        """
        cred_id = str(uuid.uuid4())

        # Encrypt sensitive fields
        stored_creds = ConnectorCredentials(
            credential_type=credentials.credential_type,
            name=credentials.name,
            api_url=credentials.api_url,
            api_token=self._encrypt(credentials.api_token) if credentials.api_token else None,
            service_account_json=self._encrypt(credentials.service_account_json) if credentials.service_account_json else None,
            additional_config=credentials.additional_config,
            created_at=credentials.created_at,
            credential_id=cred_id
        )

        self._credentials[tenant_id][cred_id] = stored_creds
        return cred_id

    def get_credentials(
        self,
        tenant_id: str,
        credential_id: str
    ) -> Optional[ConnectorCredentials]:
        """Get credentials by ID.

        Args:
            tenant_id: The tenant to get credentials for
            credential_id: The credential ID

        Returns:
            Decrypted credentials or None if not found
        """
        stored = self._credentials.get(tenant_id, {}).get(credential_id)
        if not stored:
            return None

        # Decrypt sensitive fields
        return ConnectorCredentials(
            credential_type=stored.credential_type,
            name=stored.name,
            api_url=stored.api_url,
            api_token=self._decrypt(stored.api_token) if stored.api_token else None,
            service_account_json=self._decrypt(stored.service_account_json) if stored.service_account_json else None,
            additional_config=stored.additional_config,
            created_at=stored.created_at,
            credential_id=stored.credential_id
        )

    def list_credentials(
        self,
        tenant_id: str,
        credential_type: Optional[CredentialType] = None,
        mask_secrets: bool = False
    ) -> List[ConnectorCredentials]:
        """List credentials for a tenant.

        Args:
            tenant_id: The tenant to list credentials for
            credential_type: Optional filter by type
            mask_secrets: Whether to mask sensitive data

        Returns:
            List of credentials
        """
        all_creds = list(self._credentials.get(tenant_id, {}).values())

        if credential_type:
            all_creds = [c for c in all_creds if c.credential_type == credential_type]

        if mask_secrets:
            return [c.mask_secrets() for c in all_creds]

        # Decrypt for full retrieval
        decrypted = []
        for stored in all_creds:
            decrypted.append(ConnectorCredentials(
                credential_type=stored.credential_type,
                name=stored.name,
                api_url=stored.api_url,
                api_token=self._decrypt(stored.api_token) if stored.api_token else None,
                service_account_json=self._decrypt(stored.service_account_json) if stored.service_account_json else None,
                additional_config=stored.additional_config,
                created_at=stored.created_at,
                credential_id=stored.credential_id
            ))

        return decrypted

    def update_credentials(
        self,
        tenant_id: str,
        credential_id: str,
        credentials: ConnectorCredentials
    ) -> bool:
        """Update existing credentials.

        Args:
            tenant_id: The tenant to update credentials for
            credential_id: The credential ID to update
            credentials: New credential values

        Returns:
            True if updated, False if not found
        """
        if tenant_id not in self._credentials or credential_id not in self._credentials[tenant_id]:
            return False

        # Store with encryption
        stored_creds = ConnectorCredentials(
            credential_type=credentials.credential_type,
            name=credentials.name,
            api_url=credentials.api_url,
            api_token=self._encrypt(credentials.api_token) if credentials.api_token else None,
            service_account_json=self._encrypt(credentials.service_account_json) if credentials.service_account_json else None,
            additional_config=credentials.additional_config,
            created_at=self._credentials[tenant_id][credential_id].created_at,  # Preserve original
            credential_id=credential_id
        )

        self._credentials[tenant_id][credential_id] = stored_creds
        return True

    def delete_credentials(
        self,
        tenant_id: str,
        credential_id: str
    ) -> bool:
        """Delete credentials.

        Args:
            tenant_id: The tenant to delete credentials for
            credential_id: The credential ID to delete

        Returns:
            True if deleted, False if not found
        """
        if tenant_id in self._credentials and credential_id in self._credentials[tenant_id]:
            del self._credentials[tenant_id][credential_id]
            return True
        return False

    # ========== Connector-specific helpers ==========

    def get_strapi_config(self, tenant_id: str, credential_id: str) -> Optional[Dict[str, Any]]:
        """Get Strapi-specific configuration.

        Args:
            tenant_id: The tenant to get config for
            credential_id: The credential ID

        Returns:
            Strapi configuration dict or None
        """
        creds = self.get_credentials(tenant_id, credential_id)
        if not creds or creds.credential_type != CredentialType.STRAPI:
            return None

        return {
            "api_url": creds.api_url,
            "api_token": creds.api_token,
            "name": creds.name,
            **creds.additional_config
        }

    def get_google_docs_config(self, tenant_id: str, credential_id: str) -> Optional[Dict[str, Any]]:
        """Get Google Docs-specific configuration.

        Args:
            tenant_id: The tenant to get config for
            credential_id: The credential ID

        Returns:
            Google Docs configuration dict or None
        """
        creds = self.get_credentials(tenant_id, credential_id)
        if not creds or creds.credential_type != CredentialType.GOOGLE_DOCS:
            return None

        return {
            "service_account_json": creds.service_account_json,
            "name": creds.name,
            **creds.additional_config
        }
