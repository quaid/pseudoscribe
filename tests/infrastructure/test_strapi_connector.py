"""Tests for Strapi Connector Service.

Issue: INT-003 - Strapi Connector Service

These tests verify:
- StrapiConnector extends BaseContentConnector
- Integration with StrapiMCPClient
- Content CRUD operations
- Connector registration
- Multi-tenant support
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from pseudoscribe.infrastructure.strapi_connector import (
    StrapiConnector,
    STRAPI_CONNECTOR_TYPE
)
from pseudoscribe.infrastructure.content_connector import (
    BaseContentConnector,
    ContentItem,
    ContentSchema,
    ContentField,
    FieldType,
    ConnectorStatus,
    ConnectorRegistry,
    ContentNotFoundError,
    get_connector_registry,
    register_connector
)
from pseudoscribe.infrastructure.tenant_config_service import (
    TenantConfigService,
    ConnectorCredentials,
    CredentialType
)
from pseudoscribe.infrastructure.strapi_mcp_client import (
    StrapiMCPClient,
    StrapiContentNotFoundError
)


class TestStrapiConnectorInheritance:
    """Tests for StrapiConnector class inheritance."""

    def test_extends_base_content_connector(self):
        """Test that StrapiConnector extends BaseContentConnector."""
        # Assert
        assert issubclass(StrapiConnector, BaseContentConnector)

    def test_has_connector_type(self):
        """Test that StrapiConnector has correct connector_type."""
        # Assert
        assert StrapiConnector.connector_type == "strapi"
        assert STRAPI_CONNECTOR_TYPE == "strapi"


class TestStrapiConnectorInitialization:
    """Tests for connector initialization."""

    @pytest.fixture
    def config_service(self):
        """Create a TenantConfigService instance."""
        return TenantConfigService()

    @pytest.fixture
    def strapi_credentials(self, config_service):
        """Create and store Strapi credentials."""
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_api_token"
        ))
        return cred_id

    def test_create_connector(self, config_service, strapi_credentials):
        """Test creating a StrapiConnector instance."""
        # Act
        connector = StrapiConnector(
            tenant_id="tenant-123",
            credential_id=strapi_credentials,
            config_service=config_service
        )

        # Assert
        assert connector.tenant_id == "tenant-123"
        assert connector.credential_id == strapi_credentials

    def test_connector_stores_credentials(self, config_service, strapi_credentials):
        """Test that connector can access credentials."""
        # Arrange
        connector = StrapiConnector(
            tenant_id="tenant-123",
            credential_id=strapi_credentials,
            config_service=config_service
        )

        # Act
        creds = connector.get_credentials()

        # Assert
        assert creds is not None
        assert creds.api_url == "https://strapi.example.com"


class TestStrapiConnectorConnection:
    """Tests for connection management."""

    @pytest.fixture
    def connector(self):
        """Create a configured connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        return StrapiConnector("tenant-123", cred_id, config_service)

    @pytest.mark.asyncio
    async def test_connect_success(self, connector):
        """Test successful connection."""
        # Arrange
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.configure_tenant = MagicMock()
            mock_client.health_check = AsyncMock(return_value=ConnectorStatus(
                connected=True,
                message="Connected",
                last_check=datetime.now()
            ))
            mock_get.return_value = mock_client

            # Act
            result = await connector.connect()

            # Assert
            assert result is True
            mock_client.configure_tenant.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, connector):
        """Test connection failure."""
        # Arrange
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.configure_tenant = MagicMock()
            mock_client.health_check = AsyncMock(return_value=ConnectorStatus(
                connected=False,
                message="Connection failed",
                last_check=datetime.now(),
                error="Timeout"
            ))
            mock_get.return_value = mock_client

            # Act
            result = await connector.connect()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_disconnect(self, connector):
        """Test disconnection."""
        # Arrange
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.configure_tenant = MagicMock()
            mock_client.health_check = AsyncMock(return_value=ConnectorStatus(
                connected=True,
                message="Connected",
                last_check=datetime.now()
            ))
            mock_get.return_value = mock_client

            await connector.connect()

            # Act
            await connector.disconnect()

            # Assert - should not raise
            assert True

    @pytest.mark.asyncio
    async def test_health_check(self, connector):
        """Test health check."""
        # Arrange
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.configure_tenant = MagicMock()
            mock_client.health_check = AsyncMock(return_value=ConnectorStatus(
                connected=True,
                message="Strapi connection healthy",
                last_check=datetime.now(),
                latency_ms=50.0
            ))
            mock_get.return_value = mock_client

            await connector.connect()

            # Act
            status = await connector.health_check()

            # Assert
            assert status.connected is True
            assert "healthy" in status.message.lower()


class TestStrapiConnectorFetchContent:
    """Tests for fetching content."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector with mocked MCP client."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        return connector

    @pytest.mark.asyncio
    async def test_fetch_content_success(self, connected_connector):
        """Test fetching content by ID."""
        # Arrange
        expected_item = ContentItem(
            content_id="abc123",
            content_type="article",
            title="Test Article",
            body="Article body content",
            status="draft"
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.fetch_content = AsyncMock(return_value=expected_item)
            mock_get.return_value = mock_client

            # Act
            result = await connected_connector.fetch_content("abc123")

            # Assert
            assert result.content_id == "abc123"
            assert result.title == "Test Article"
            assert result.body == "Article body content"

    @pytest.mark.asyncio
    async def test_fetch_content_not_found(self, connected_connector):
        """Test fetching nonexistent content raises error."""
        # Arrange
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.fetch_content = AsyncMock(
                side_effect=StrapiContentNotFoundError("Not found")
            )
            mock_get.return_value = mock_client

            # Act & Assert
            with pytest.raises(ContentNotFoundError):
                await connected_connector.fetch_content("nonexistent")

    @pytest.mark.asyncio
    async def test_fetch_content_with_content_type(self, connected_connector):
        """Test fetching content with specific content type."""
        # Arrange
        expected_item = ContentItem(
            content_id="blog123",
            content_type="blog",
            title="Blog Post",
            body="Blog content"
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.fetch_content = AsyncMock(return_value=expected_item)
            mock_get.return_value = mock_client

            # Act
            result = await connected_connector.fetch_content(
                "blog123",
                content_type="blog"
            )

            # Assert
            assert result.content_type == "blog"


class TestStrapiConnectorPushContent:
    """Tests for pushing content."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        return connector

    @pytest.mark.asyncio
    async def test_push_content_success(self, connected_connector):
        """Test pushing new content."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="New Article",
            body="Article body"
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.push_content = AsyncMock(return_value="new123")
            mock_get.return_value = mock_client

            # Act
            content_id = await connected_connector.push_content(content)

            # Assert
            assert content_id == "new123"

    @pytest.mark.asyncio
    async def test_push_content_with_metadata(self, connected_connector):
        """Test pushing content with metadata."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Article with Metadata",
            body="Body content",
            metadata={"author": "Test Author", "category": "tech"}
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.push_content = AsyncMock(return_value="meta123")
            mock_get.return_value = mock_client

            # Act
            content_id = await connected_connector.push_content(content)

            # Assert
            assert content_id == "meta123"
            mock_client.push_content.assert_called_once()


class TestStrapiConnectorUpdateContent:
    """Tests for updating content."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        return connector

    @pytest.mark.asyncio
    async def test_update_content_success(self, connected_connector):
        """Test updating existing content."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Updated Title",
            body="Updated body"
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.update_content = AsyncMock(return_value=True)
            mock_get.return_value = mock_client

            # Act
            result = await connected_connector.update_content("existing123", content)

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_content(self, connected_connector):
        """Test updating nonexistent content returns False."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Update",
            body="Body"
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.update_content = AsyncMock(return_value=False)
            mock_get.return_value = mock_client

            # Act
            result = await connected_connector.update_content("nonexistent", content)

            # Assert
            assert result is False


class TestStrapiConnectorListContent:
    """Tests for listing content."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        return connector

    @pytest.mark.asyncio
    async def test_list_content(self, connected_connector):
        """Test listing content."""
        # Arrange
        expected_items = [
            ContentItem(content_id="1", content_type="article", title="Article 1", body="Body 1"),
            ContentItem(content_id="2", content_type="article", title="Article 2", body="Body 2")
        ]

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.list_content = AsyncMock(return_value=expected_items)
            mock_get.return_value = mock_client

            # Act
            items = await connected_connector.list_content()

            # Assert
            assert len(items) == 2
            assert items[0].title == "Article 1"

    @pytest.mark.asyncio
    async def test_list_content_with_type_filter(self, connected_connector):
        """Test listing content filtered by type."""
        # Arrange
        expected_items = [
            ContentItem(content_id="1", content_type="blog", title="Blog 1", body="Body 1")
        ]

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.list_content = AsyncMock(return_value=expected_items)
            mock_get.return_value = mock_client

            # Act
            items = await connected_connector.list_content(content_type="blog")

            # Assert
            assert len(items) == 1
            assert items[0].content_type == "blog"

    @pytest.mark.asyncio
    async def test_list_content_with_pagination(self, connected_connector):
        """Test listing content with pagination."""
        # Arrange
        expected_items = [
            ContentItem(content_id="3", content_type="article", title="Article 3", body="Body 3")
        ]

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.list_content = AsyncMock(return_value=expected_items)
            mock_get.return_value = mock_client

            # Act
            items = await connected_connector.list_content(limit=10, offset=20)

            # Assert
            mock_client.list_content.assert_called_once()
            call_kwargs = mock_client.list_content.call_args[1]
            assert call_kwargs.get('limit') == 10
            assert call_kwargs.get('offset') == 20


class TestStrapiConnectorSchema:
    """Tests for schema operations."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        return connector

    @pytest.mark.asyncio
    async def test_get_schema(self, connected_connector):
        """Test getting content type schema."""
        # Arrange
        expected_schema = ContentSchema(
            content_type="article",
            fields=[
                ContentField(name="title", field_type=FieldType.STRING, required=True),
                ContentField(name="content", field_type=FieldType.RICHTEXT, required=True),
                ContentField(name="tags", field_type=FieldType.ARRAY, required=False)
            ]
        )

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.get_schema = AsyncMock(return_value=expected_schema)
            mock_get.return_value = mock_client

            # Act
            schema = await connected_connector.get_schema("article")

            # Assert
            assert schema.content_type == "article"
            assert len(schema.fields) == 3


class TestStrapiConnectorOptionalOperations:
    """Tests for optional operations (delete, search)."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        return connector

    @pytest.mark.asyncio
    async def test_delete_content(self, connected_connector):
        """Test deleting content."""
        # Note: delete is optional in BaseContentConnector
        # StrapiConnector may or may not implement it
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            # If delete is implemented
            if hasattr(mock_client, 'delete_content'):
                mock_client.delete_content = AsyncMock(return_value=True)
                mock_get.return_value = mock_client

                result = await connected_connector.delete_content("to-delete")
                assert result is True

    @pytest.mark.asyncio
    async def test_search_content(self, connected_connector):
        """Test searching content."""
        # Search may not be implemented
        try:
            await connected_connector.search_content("test query")
        except NotImplementedError:
            # Expected if not implemented
            pass


class TestStrapiConnectorRegistration:
    """Tests for connector registration."""

    def test_connector_registered_globally(self):
        """Test that StrapiConnector is registered in global registry."""
        # Act - import triggers registration
        from pseudoscribe.infrastructure.strapi_connector import StrapiConnector

        # Assert
        registry = get_connector_registry()
        assert registry.is_registered("strapi")

    def test_create_connector_from_registry(self):
        """Test creating connector from registry."""
        # Arrange
        from pseudoscribe.infrastructure.strapi_connector import StrapiConnector

        registry = get_connector_registry()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test",
            api_url="https://strapi.example.com",
            api_token="token"
        ))

        # Act
        connector = registry.create(
            "strapi",
            tenant_id="tenant-123",
            credential_id=cred_id,
            config_service=config_service
        )

        # Assert
        assert isinstance(connector, StrapiConnector)
        assert connector.tenant_id == "tenant-123"


class TestStrapiConnectorTenantIsolation:
    """Tests for multi-tenant isolation."""

    def test_connectors_isolated_by_tenant(self):
        """Test that connectors are isolated per tenant."""
        # Arrange
        config_service = TenantConfigService()

        cred_id_a = config_service.store_credentials("tenant-A", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="strapi-a",
            api_url="https://a.strapi.example.com",
            api_token="token_a"
        ))

        cred_id_b = config_service.store_credentials("tenant-B", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="strapi-b",
            api_url="https://b.strapi.example.com",
            api_token="token_b"
        ))

        # Act
        connector_a = StrapiConnector("tenant-A", cred_id_a, config_service)
        connector_b = StrapiConnector("tenant-B", cred_id_b, config_service)

        # Assert
        assert connector_a.tenant_id != connector_b.tenant_id
        assert connector_a.get_credentials().api_url != connector_b.get_credentials().api_url

    @pytest.mark.asyncio
    async def test_operations_use_tenant_credentials(self):
        """Test that operations use correct tenant credentials."""
        # Arrange
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="tenant-strapi",
            api_url="https://tenant.strapi.example.com",
            api_token="tenant_token"
        ))

        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True

        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.fetch_content = AsyncMock(return_value=ContentItem(
                content_id="test",
                content_type="article",
                title="Test",
                body="Body"
            ))
            mock_get.return_value = mock_client

            # Act
            await connector.fetch_content("test")

            # Assert - verify tenant_id was passed
            mock_client.fetch_content.assert_called_once()
            call_kwargs = mock_client.fetch_content.call_args[1]
            assert call_kwargs.get('tenant_id') == "tenant-123"


class TestStrapiConnectorDefaultContentType:
    """Tests for default content type handling."""

    @pytest.fixture
    def connected_connector(self):
        """Create a connected connector."""
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        connector = StrapiConnector("tenant-123", cred_id, config_service)
        connector._connected = True
        connector._default_content_type = "article"
        return connector

    @pytest.mark.asyncio
    async def test_fetch_uses_default_content_type(self, connected_connector):
        """Test that fetch uses default content type when not specified."""
        # Arrange
        with patch.object(StrapiMCPClient, 'get_instance') as mock_get:
            mock_client = MagicMock()
            mock_client.fetch_content = AsyncMock(return_value=ContentItem(
                content_id="test",
                content_type="article",
                title="Test",
                body="Body"
            ))
            mock_get.return_value = mock_client

            # Act
            await connected_connector.fetch_content("test")

            # Assert
            call_kwargs = mock_client.fetch_content.call_args[1]
            assert call_kwargs.get('content_type') == "article"

    def test_set_default_content_type(self, connected_connector):
        """Test setting default content type."""
        # Act
        connected_connector.set_default_content_type("blog")

        # Assert
        assert connected_connector._default_content_type == "blog"
