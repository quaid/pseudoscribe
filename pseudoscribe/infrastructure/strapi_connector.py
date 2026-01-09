"""Strapi Connector Service.

Issue: INT-003 - Strapi Connector Service

This module provides the Strapi connector implementation:
- Extends BaseContentConnector for unified interface
- Uses StrapiMCPClient for MCP operations
- Registers with ConnectorRegistry for discovery
- Supports multi-tenant isolation
"""

from datetime import datetime
from typing import List, Optional

from pseudoscribe.infrastructure.content_connector import (
    BaseContentConnector,
    ContentItem,
    ContentSchema,
    ConnectorStatus,
    ContentNotFoundError,
    register_connector
)
from pseudoscribe.infrastructure.tenant_config_service import TenantConfigService
from pseudoscribe.infrastructure.strapi_mcp_client import (
    StrapiMCPClient,
    StrapiContentNotFoundError,
    StrapiMCPError
)


# Connector type constant
STRAPI_CONNECTOR_TYPE = "strapi"


class StrapiConnector(BaseContentConnector):
    """Strapi CMS connector implementation.

    Extends BaseContentConnector to provide a unified interface for
    interacting with Strapi CMS via the StrapiMCPClient.
    """

    connector_type: str = STRAPI_CONNECTOR_TYPE

    def __init__(
        self,
        tenant_id: str,
        credential_id: str,
        config_service: TenantConfigService
    ):
        """Initialize the Strapi connector.

        Args:
            tenant_id: The tenant this connector belongs to
            credential_id: ID of stored credentials to use
            config_service: Service for accessing tenant configuration
        """
        super().__init__(tenant_id, credential_id, config_service)
        self._connected = False
        self._client: Optional[StrapiMCPClient] = None
        self._default_content_type = "article"

    def set_default_content_type(self, content_type: str) -> None:
        """Set the default content type for operations.

        Args:
            content_type: The default content type (e.g., "article", "blog")
        """
        self._default_content_type = content_type

    def _get_client(self) -> StrapiMCPClient:
        """Get the MCP client instance.

        Returns:
            The StrapiMCPClient singleton instance
        """
        if self._client is None:
            self._client = StrapiMCPClient.get_instance()
        return self._client

    async def connect(self) -> bool:
        """Establish connection to Strapi via MCP.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self._get_client()

            # Configure the tenant in the MCP client
            client.configure_tenant(
                tenant_id=self.tenant_id,
                credential_id=self.credential_id,
                config_service=self._config_service
            )

            # Verify connection with health check
            status = await client.health_check(self.tenant_id)
            self._connected = status.connected

            return self._connected

        except Exception:
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close the connection to Strapi.

        Note: MCP client is a singleton, so we just mark as disconnected.
        """
        self._connected = False

    async def health_check(self) -> ConnectorStatus:
        """Check the health of the Strapi connection.

        Returns:
            ConnectorStatus with connection details
        """
        if not self._connected:
            return ConnectorStatus(
                connected=False,
                message="Not connected",
                last_check=datetime.now()
            )

        try:
            client = self._get_client()
            return await client.health_check(self.tenant_id)
        except Exception as e:
            return ConnectorStatus(
                connected=False,
                message="Health check failed",
                last_check=datetime.now(),
                error=str(e)
            )

    async def fetch_content(
        self,
        content_id: str,
        content_type: Optional[str] = None
    ) -> ContentItem:
        """Fetch content by ID from Strapi.

        Args:
            content_id: The document ID of the content to fetch
            content_type: Optional content type (uses default if not specified)

        Returns:
            ContentItem with the content data

        Raises:
            ContentNotFoundError: If content doesn't exist
        """
        try:
            client = self._get_client()
            return await client.fetch_content(
                tenant_id=self.tenant_id,
                content_type=content_type or self._default_content_type,
                document_id=content_id
            )
        except StrapiContentNotFoundError as e:
            raise ContentNotFoundError(str(e)) from e

    async def push_content(self, content: ContentItem) -> str:
        """Push new content to Strapi.

        Args:
            content: The content to create

        Returns:
            The document ID of the created content
        """
        client = self._get_client()
        return await client.push_content(
            tenant_id=self.tenant_id,
            content=content
        )

    async def update_content(
        self,
        content_id: str,
        content: ContentItem
    ) -> bool:
        """Update existing content in Strapi.

        Args:
            content_id: The document ID of the content to update
            content: The new content data

        Returns:
            True if updated successfully, False if not found
        """
        client = self._get_client()
        return await client.update_content(
            tenant_id=self.tenant_id,
            document_id=content_id,
            content=content
        )

    async def list_content(
        self,
        content_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ContentItem]:
        """List content from Strapi.

        Args:
            content_type: Optional filter by content type
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of ContentItems
        """
        client = self._get_client()
        return await client.list_content(
            tenant_id=self.tenant_id,
            content_type=content_type or self._default_content_type,
            limit=limit,
            offset=offset
        )

    async def get_schema(self, content_type: str) -> ContentSchema:
        """Get the schema for a content type from Strapi.

        Args:
            content_type: The content type to get schema for

        Returns:
            ContentSchema with field definitions
        """
        client = self._get_client()
        return await client.get_schema(
            tenant_id=self.tenant_id,
            content_type=content_type
        )

    async def delete_content(self, content_id: str) -> bool:
        """Delete content by ID from Strapi.

        Args:
            content_id: The document ID of the content to delete

        Returns:
            True if deleted, False if not found

        Note: This requires the MCP client to support delete operations.
        """
        # Delete is optional - check if client supports it
        client = self._get_client()
        if hasattr(client, 'delete_content'):
            return await client.delete_content(
                tenant_id=self.tenant_id,
                document_id=content_id
            )
        raise NotImplementedError("Delete not supported by this connector")

    async def search_content(
        self,
        query: str,
        content_type: Optional[str] = None,
        limit: int = 100
    ) -> List[ContentItem]:
        """Search content in Strapi.

        Args:
            query: Search query string
            content_type: Optional filter by content type
            limit: Maximum number of items to return

        Returns:
            List of matching ContentItems

        Note: Search functionality depends on Strapi configuration.
        """
        # Search is optional - check if client supports it
        client = self._get_client()
        if hasattr(client, 'search_content'):
            return await client.search_content(
                tenant_id=self.tenant_id,
                query=query,
                content_type=content_type,
                limit=limit
            )
        raise NotImplementedError("Search not supported by this connector")


# Register the connector with the global registry
register_connector(STRAPI_CONNECTOR_TYPE, StrapiConnector)
