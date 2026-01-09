"""Content Connector Base Classes.

Issue: INT-001 - Content Connector Base

This module provides the base abstraction for content connectors including:
- BaseContentConnector abstract class
- ContentItem unified content model
- ContentSchema for content type definitions
- ConnectorRegistry for connector discovery
"""

from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Type
from enum import Enum

from pseudoscribe.infrastructure.tenant_config_service import (
    TenantConfigService,
    ConnectorCredentials
)


class FieldType(Enum):
    """Field types for content schemas."""
    STRING = "string"
    TEXT = "text"
    RICHTEXT = "richtext"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"
    MEDIA = "media"
    RELATION = "relation"


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class ContentNotFoundError(ConnectorError):
    """Raised when content is not found."""
    pass


class ConnectionError(ConnectorError):
    """Raised when connection fails."""
    pass


@dataclass
class ConnectorStatus:
    """Status of a connector connection."""
    connected: bool
    message: str
    last_check: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class ContentField:
    """Definition of a content field."""
    name: str
    field_type: FieldType
    required: bool = False
    description: Optional[str] = None
    default_value: Any = None


@dataclass
class ContentSchema:
    """Schema definition for a content type."""
    content_type: str
    fields: List[ContentField] = field(default_factory=list)
    description: Optional[str] = None

    def get_required_fields(self) -> List[ContentField]:
        """Get all required fields."""
        return [f for f in self.fields if f.required]

    def get_field(self, name: str) -> Optional[ContentField]:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None


@dataclass
class ContentItem:
    """Unified content representation across connectors."""
    content_type: str
    title: str
    body: str
    content_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "draft"
    locale: str = "en"
    media: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content_id": self.content_id,
            "content_type": self.content_type,
            "title": self.title,
            "body": self.body,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "locale": self.locale,
            "media": self.media
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentItem':
        """Create from dictionary representation."""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            content_id=data.get("content_id"),
            content_type=data.get("content_type", "unknown"),
            title=data.get("title", ""),
            body=data.get("body", ""),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            status=data.get("status", "draft"),
            locale=data.get("locale", "en"),
            media=data.get("media", [])
        )


class BaseContentConnector(ABC):
    """Abstract base class for content connectors.

    All content connectors (Strapi, Google Docs, etc.) must implement
    this interface to ensure consistent behavior across integrations.
    """

    connector_type: str = "base"

    def __init__(
        self,
        tenant_id: str,
        credential_id: str,
        config_service: TenantConfigService
    ):
        """Initialize the connector.

        Args:
            tenant_id: The tenant this connector belongs to
            credential_id: ID of stored credentials to use
            config_service: Service for accessing tenant configuration
        """
        self.tenant_id = tenant_id
        self.credential_id = credential_id
        self._config_service = config_service

    def get_credentials(self) -> Optional[ConnectorCredentials]:
        """Get the credentials for this connector.

        Returns:
            ConnectorCredentials or None if not found
        """
        return self._config_service.get_credentials(
            self.tenant_id,
            self.credential_id
        )

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the content source.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the content source."""
        pass

    @abstractmethod
    async def health_check(self) -> ConnectorStatus:
        """Check the health of the connection.

        Returns:
            ConnectorStatus with connection details
        """
        pass

    @abstractmethod
    async def fetch_content(self, content_id: str) -> ContentItem:
        """Fetch content by ID.

        Args:
            content_id: The ID of the content to fetch

        Returns:
            ContentItem with the content data

        Raises:
            ContentNotFoundError: If content doesn't exist
        """
        pass

    @abstractmethod
    async def push_content(self, content: ContentItem) -> str:
        """Push new content to the source.

        Args:
            content: The content to create

        Returns:
            The ID of the created content
        """
        pass

    @abstractmethod
    async def update_content(self, content_id: str, content: ContentItem) -> bool:
        """Update existing content.

        Args:
            content_id: The ID of the content to update
            content: The new content data

        Returns:
            True if updated successfully, False if not found
        """
        pass

    @abstractmethod
    async def list_content(
        self,
        content_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ContentItem]:
        """List content from the source.

        Args:
            content_type: Optional filter by content type
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of ContentItems
        """
        pass

    @abstractmethod
    async def get_schema(self, content_type: str) -> ContentSchema:
        """Get the schema for a content type.

        Args:
            content_type: The content type to get schema for

        Returns:
            ContentSchema with field definitions
        """
        pass

    async def delete_content(self, content_id: str) -> bool:
        """Delete content by ID.

        Args:
            content_id: The ID of the content to delete

        Returns:
            True if deleted, False if not found

        Note: This is optional - subclasses may override.
        """
        raise NotImplementedError("Delete not supported by this connector")

    async def search_content(
        self,
        query: str,
        content_type: Optional[str] = None,
        limit: int = 100
    ) -> List[ContentItem]:
        """Search content by query.

        Args:
            query: Search query string
            content_type: Optional filter by content type
            limit: Maximum number of items to return

        Returns:
            List of matching ContentItems

        Note: This is optional - subclasses may override.
        """
        raise NotImplementedError("Search not supported by this connector")


class ConnectorRegistry:
    """Registry for content connector types.

    Allows registration and discovery of connector implementations.
    """

    def __init__(self):
        """Initialize the registry."""
        self._connectors: Dict[str, Type[BaseContentConnector]] = {}

    def register(
        self,
        connector_type: str,
        connector_class: Type[BaseContentConnector]
    ) -> None:
        """Register a connector class.

        Args:
            connector_type: Unique identifier for this connector type
            connector_class: The connector class to register
        """
        self._connectors[connector_type] = connector_class

    def get(self, connector_type: str) -> Type[BaseContentConnector]:
        """Get a registered connector class.

        Args:
            connector_type: The type of connector to get

        Returns:
            The connector class

        Raises:
            KeyError: If connector type not registered
        """
        if connector_type not in self._connectors:
            raise KeyError(f"Connector type '{connector_type}' not registered")
        return self._connectors[connector_type]

    def list_types(self) -> List[str]:
        """List all registered connector types.

        Returns:
            List of connector type identifiers
        """
        return list(self._connectors.keys())

    def create(
        self,
        connector_type: str,
        tenant_id: str,
        credential_id: str,
        config_service: TenantConfigService
    ) -> BaseContentConnector:
        """Create a connector instance.

        Args:
            connector_type: The type of connector to create
            tenant_id: The tenant ID
            credential_id: The credential ID to use
            config_service: The tenant config service

        Returns:
            An instance of the connector
        """
        connector_class = self.get(connector_type)
        return connector_class(tenant_id, credential_id, config_service)

    def is_registered(self, connector_type: str) -> bool:
        """Check if a connector type is registered.

        Args:
            connector_type: The type to check

        Returns:
            True if registered, False otherwise
        """
        return connector_type in self._connectors


# Global registry instance
_global_registry: Optional[ConnectorRegistry] = None


def get_connector_registry() -> ConnectorRegistry:
    """Get the global connector registry.

    Returns:
        The global ConnectorRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ConnectorRegistry()
    return _global_registry


def register_connector(
    connector_type: str,
    connector_class: Type[BaseContentConnector]
) -> None:
    """Register a connector in the global registry.

    Args:
        connector_type: Unique identifier for this connector type
        connector_class: The connector class to register
    """
    get_connector_registry().register(connector_type, connector_class)
