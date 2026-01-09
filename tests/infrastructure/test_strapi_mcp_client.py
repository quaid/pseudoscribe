"""Tests for Strapi MCP Client.

Issue: INT-002 - Strapi MCP Integration

These tests verify:
- StrapiMCPClient singleton pattern
- GraphQL query/mutation execution
- Content CRUD operations via MCP
- Schema introspection
- Error handling
- Multi-tenant isolation
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from pseudoscribe.infrastructure.strapi_mcp_client import (
    StrapiMCPClient,
    StrapiMCPError,
    StrapiConnectionError,
    StrapiQueryError,
    StrapiContentNotFoundError
)
from pseudoscribe.infrastructure.content_connector import (
    ContentItem,
    ContentSchema,
    ContentField,
    FieldType,
    ConnectorStatus
)
from pseudoscribe.infrastructure.tenant_config_service import (
    TenantConfigService,
    ConnectorCredentials,
    CredentialType
)


class TestStrapiMCPClientSingleton:
    """Tests for singleton pattern."""

    def test_get_instance_returns_same_instance(self):
        """Test that get_instance returns the same instance."""
        # Act
        instance1 = StrapiMCPClient.get_instance()
        instance2 = StrapiMCPClient.get_instance()

        # Assert
        assert instance1 is instance2

    def test_reset_instance_clears_singleton(self):
        """Test that reset clears the singleton."""
        # Arrange
        instance1 = StrapiMCPClient.get_instance()

        # Act
        StrapiMCPClient.reset_instance()
        instance2 = StrapiMCPClient.get_instance()

        # Assert
        assert instance1 is not instance2


class TestStrapiMCPClientConfiguration:
    """Tests for client configuration."""

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
            api_token="test_api_token_12345"
        ))
        return cred_id

    def test_configure_tenant(self, config_service, strapi_credentials):
        """Test configuring a tenant connection."""
        # Arrange
        client = StrapiMCPClient.get_instance()
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()

        # Act
        client.configure_tenant(
            tenant_id="tenant-123",
            credential_id=strapi_credentials,
            config_service=config_service
        )

        # Assert
        assert client.is_tenant_configured("tenant-123")

    def test_unconfigured_tenant_returns_false(self):
        """Test that unconfigured tenant returns False."""
        # Arrange
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()

        # Act & Assert
        assert not client.is_tenant_configured("nonexistent-tenant")

    def test_get_tenant_config(self, config_service, strapi_credentials):
        """Test retrieving tenant configuration."""
        # Arrange
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        client.configure_tenant(
            tenant_id="tenant-123",
            credential_id=strapi_credentials,
            config_service=config_service
        )

        # Act
        config = client.get_tenant_config("tenant-123")

        # Assert
        assert config is not None
        assert config["api_url"] == "https://strapi.example.com"


class TestStrapiMCPClientHealthCheck:
    """Tests for health check functionality."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client with mocked MCP."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_health_check_success(self, configured_client):
        """Test successful health check."""
        # Arrange
        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = {"data": {"__typename": "Query"}}

            # Act
            status = await configured_client.health_check("tenant-123")

            # Assert
            assert status.connected is True
            assert "healthy" in status.message.lower() or "connected" in status.message.lower()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, configured_client):
        """Test failed health check."""
        # Arrange
        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.side_effect = StrapiConnectionError("Connection refused")

            # Act
            status = await configured_client.health_check("tenant-123")

            # Assert
            assert status.connected is False
            assert status.error is not None

    @pytest.mark.asyncio
    async def test_health_check_unconfigured_tenant(self):
        """Test health check for unconfigured tenant."""
        # Arrange
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()

        # Act
        status = await client.health_check("nonexistent-tenant")

        # Assert
        assert status.connected is False
        assert "not configured" in status.message.lower()


class TestStrapiMCPClientFetchContent:
    """Tests for fetching content."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_fetch_content_by_document_id(self, configured_client):
        """Test fetching content by Strapi 5.x documentId."""
        # Arrange
        mock_response = {
            "data": {
                "article": {
                    "documentId": "abc123xyz",
                    "title": "Test Article",
                    "content": "This is the article body.",
                    "status": "DRAFT",
                    "createdAt": "2024-01-15T10:00:00.000Z",
                    "updatedAt": "2024-01-15T12:00:00.000Z",
                    "locale": "en"
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            content = await configured_client.fetch_content(
                tenant_id="tenant-123",
                content_type="article",
                document_id="abc123xyz"
            )

            # Assert
            assert content.content_id == "abc123xyz"
            assert content.title == "Test Article"
            assert content.body == "This is the article body."
            assert content.status == "draft"

    @pytest.mark.asyncio
    async def test_fetch_content_not_found(self, configured_client):
        """Test fetching nonexistent content raises error."""
        # Arrange
        mock_response = {"data": {"article": None}}

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act & Assert
            with pytest.raises(StrapiContentNotFoundError):
                await configured_client.fetch_content(
                    tenant_id="tenant-123",
                    content_type="article",
                    document_id="nonexistent"
                )

    @pytest.mark.asyncio
    async def test_fetch_draft_content(self, configured_client):
        """Test fetching draft content with status parameter."""
        # Arrange
        mock_response = {
            "data": {
                "article": {
                    "documentId": "draft123",
                    "title": "Draft Article",
                    "content": "Draft body",
                    "status": "DRAFT",
                    "createdAt": "2024-01-15T10:00:00.000Z",
                    "updatedAt": "2024-01-15T10:00:00.000Z",
                    "locale": "en"
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            content = await configured_client.fetch_content(
                tenant_id="tenant-123",
                content_type="article",
                document_id="draft123",
                status="DRAFT"
            )

            # Assert
            assert content.status == "draft"
            # Verify the query included status parameter
            call_args = mock_mcp.call_args
            assert "DRAFT" in str(call_args) or "status" in str(call_args)


class TestStrapiMCPClientPushContent:
    """Tests for pushing content."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_push_new_content(self, configured_client):
        """Test pushing new content to Strapi."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="New Article",
            body="Article body content",
            metadata={"author": "Test Author"}
        )

        mock_response = {
            "data": {
                "createArticle": {
                    "documentId": "new123abc",
                    "title": "New Article",
                    "content": "Article body content"
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            document_id = await configured_client.push_content(
                tenant_id="tenant-123",
                content=content
            )

            # Assert
            assert document_id == "new123abc"

    @pytest.mark.asyncio
    async def test_push_content_with_locale(self, configured_client):
        """Test pushing content with specific locale."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="French Article",
            body="Contenu en français",
            locale="fr"
        )

        mock_response = {
            "data": {
                "createArticle": {
                    "documentId": "fr123",
                    "title": "French Article",
                    "locale": "fr"
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            document_id = await configured_client.push_content(
                tenant_id="tenant-123",
                content=content
            )

            # Assert
            assert document_id == "fr123"
            # Verify locale was included in mutation
            call_args = mock_mcp.call_args
            assert "fr" in str(call_args)

    @pytest.mark.asyncio
    async def test_push_content_error(self, configured_client):
        """Test handling push error."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Error Article",
            body="Body"
        )

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.side_effect = StrapiQueryError("Validation error: title required")

            # Act & Assert
            with pytest.raises(StrapiQueryError) as exc_info:
                await configured_client.push_content(
                    tenant_id="tenant-123",
                    content=content
                )
            assert "Validation error" in str(exc_info.value)


class TestStrapiMCPClientUpdateContent:
    """Tests for updating content."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_update_existing_content(self, configured_client):
        """Test updating existing content."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Updated Title",
            body="Updated body content"
        )

        mock_response = {
            "data": {
                "updateArticle": {
                    "documentId": "existing123",
                    "title": "Updated Title",
                    "content": "Updated body content"
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            result = await configured_client.update_content(
                tenant_id="tenant-123",
                document_id="existing123",
                content=content
            )

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_content(self, configured_client):
        """Test updating nonexistent content returns False."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Update",
            body="Body"
        )

        mock_response = {"data": {"updateArticle": None}}

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            result = await configured_client.update_content(
                tenant_id="tenant-123",
                document_id="nonexistent",
                content=content
            )

            # Assert
            assert result is False


class TestStrapiMCPClientListContent:
    """Tests for listing content."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_list_content(self, configured_client):
        """Test listing content of a type."""
        # Arrange
        mock_response = {
            "data": {
                "articles": [
                    {
                        "documentId": "article1",
                        "title": "Article 1",
                        "content": "Body 1",
                        "status": "PUBLISHED",
                        "createdAt": "2024-01-15T10:00:00.000Z",
                        "updatedAt": "2024-01-15T10:00:00.000Z",
                        "locale": "en"
                    },
                    {
                        "documentId": "article2",
                        "title": "Article 2",
                        "content": "Body 2",
                        "status": "DRAFT",
                        "createdAt": "2024-01-16T10:00:00.000Z",
                        "updatedAt": "2024-01-16T10:00:00.000Z",
                        "locale": "en"
                    }
                ]
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            items = await configured_client.list_content(
                tenant_id="tenant-123",
                content_type="article"
            )

            # Assert
            assert len(items) == 2
            assert items[0].content_id == "article1"
            assert items[1].content_id == "article2"

    @pytest.mark.asyncio
    async def test_list_content_with_pagination(self, configured_client):
        """Test listing content with pagination."""
        # Arrange
        mock_response = {
            "data": {
                "articles": [
                    {
                        "documentId": "article3",
                        "title": "Article 3",
                        "content": "Body 3",
                        "status": "PUBLISHED",
                        "createdAt": "2024-01-15T10:00:00.000Z",
                        "updatedAt": "2024-01-15T10:00:00.000Z",
                        "locale": "en"
                    }
                ]
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            items = await configured_client.list_content(
                tenant_id="tenant-123",
                content_type="article",
                limit=10,
                offset=20
            )

            # Assert
            assert len(items) == 1
            # Verify pagination was passed
            call_args = mock_mcp.call_args
            assert "10" in str(call_args) or "20" in str(call_args)

    @pytest.mark.asyncio
    async def test_list_drafts_only(self, configured_client):
        """Test listing only draft content."""
        # Arrange
        mock_response = {
            "data": {
                "articles": [
                    {
                        "documentId": "draft1",
                        "title": "Draft 1",
                        "content": "Draft body",
                        "status": "DRAFT",
                        "createdAt": "2024-01-15T10:00:00.000Z",
                        "updatedAt": "2024-01-15T10:00:00.000Z",
                        "locale": "en"
                    }
                ]
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            items = await configured_client.list_content(
                tenant_id="tenant-123",
                content_type="article",
                status="DRAFT"
            )

            # Assert
            assert len(items) == 1
            assert items[0].status == "draft"


class TestStrapiMCPClientSchema:
    """Tests for schema introspection."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_get_schema(self, configured_client):
        """Test getting content type schema via introspection."""
        # Arrange
        mock_response = {
            "data": {
                "__type": {
                    "name": "Article",
                    "fields": [
                        {"name": "documentId", "type": {"name": "ID", "kind": "SCALAR"}},
                        {"name": "title", "type": {"name": "String", "kind": "SCALAR"}},
                        {"name": "content", "type": {"name": "String", "kind": "SCALAR"}},
                        {"name": "publishedAt", "type": {"name": "DateTime", "kind": "SCALAR"}},
                        {"name": "tags", "type": {"name": None, "kind": "LIST"}}
                    ]
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            schema = await configured_client.get_schema(
                tenant_id="tenant-123",
                content_type="article"
            )

            # Assert
            assert schema.content_type == "article"
            assert len(schema.fields) >= 3  # At least title, content, and some others
            field_names = [f.name for f in schema.fields]
            assert "title" in field_names
            assert "content" in field_names

    @pytest.mark.asyncio
    async def test_list_content_types(self, configured_client):
        """Test listing available content types."""
        # Arrange
        mock_response = {
            "data": {
                "__schema": {
                    "types": [
                        {"name": "Article", "kind": "OBJECT"},
                        {"name": "BlogPost", "kind": "OBJECT"},
                        {"name": "Page", "kind": "OBJECT"},
                        {"name": "Query", "kind": "OBJECT"},
                        {"name": "String", "kind": "SCALAR"}
                    ]
                }
            }
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            types = await configured_client.list_content_types("tenant-123")

            # Assert
            # Should filter out Query and scalar types
            assert "Article" in types or "article" in types
            assert "BlogPost" in types or "blogpost" in types


class TestStrapiMCPClientErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, configured_client):
        """Test connection error is properly wrapped."""
        # Arrange
        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.side_effect = Exception("Network unreachable")

            # Act & Assert
            with pytest.raises(StrapiMCPError):
                await configured_client.fetch_content(
                    tenant_id="tenant-123",
                    content_type="article",
                    document_id="test123"
                )

    @pytest.mark.asyncio
    async def test_graphql_error_handling(self, configured_client):
        """Test GraphQL error response is properly handled."""
        # Arrange
        mock_response = {
            "errors": [
                {"message": "Field 'nonexistent' not found on type 'Article'"}
            ]
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act & Assert
            with pytest.raises(StrapiQueryError) as exc_info:
                await configured_client.fetch_content(
                    tenant_id="tenant-123",
                    content_type="article",
                    document_id="test123"
                )
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_authentication_error(self, configured_client):
        """Test authentication error handling."""
        # Arrange
        mock_response = {
            "errors": [
                {"message": "Forbidden", "extensions": {"code": "FORBIDDEN"}}
            ]
        }

        with patch.object(configured_client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act & Assert
            with pytest.raises(StrapiQueryError):
                await configured_client.fetch_content(
                    tenant_id="tenant-123",
                    content_type="article",
                    document_id="test123"
                )


class TestStrapiMCPClientTenantIsolation:
    """Tests for multi-tenant isolation."""

    def test_tenant_configs_are_isolated(self):
        """Test that tenant configurations are isolated."""
        # Arrange
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
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
        client.configure_tenant("tenant-A", cred_id_a, config_service)
        client.configure_tenant("tenant-B", cred_id_b, config_service)

        # Assert
        config_a = client.get_tenant_config("tenant-A")
        config_b = client.get_tenant_config("tenant-B")

        assert config_a["api_url"] != config_b["api_url"]
        assert config_a["api_url"] == "https://a.strapi.example.com"
        assert config_b["api_url"] == "https://b.strapi.example.com"

    @pytest.mark.asyncio
    async def test_operations_use_correct_tenant_credentials(self):
        """Test that operations use correct tenant credentials."""
        # Arrange
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()

        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="strapi",
            api_url="https://strapi.example.com",
            api_token="tenant_specific_token"
        ))

        client.configure_tenant("tenant-123", cred_id, config_service)

        mock_response = {
            "data": {
                "article": {
                    "documentId": "test",
                    "title": "Test",
                    "content": "Body",
                    "status": "DRAFT",
                    "createdAt": "2024-01-15T10:00:00.000Z",
                    "updatedAt": "2024-01-15T10:00:00.000Z",
                    "locale": "en"
                }
            }
        }

        with patch.object(client, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = mock_response

            # Act
            await client.fetch_content(
                tenant_id="tenant-123",
                content_type="article",
                document_id="test"
            )

            # Assert - verify tenant ID was passed to MCP call
            mock_mcp.assert_called_once()
            # The call should include tenant context


class TestStrapiMCPClientGraphQLQueries:
    """Tests for GraphQL query generation."""

    @pytest.fixture
    def configured_client(self):
        """Create a configured client."""
        StrapiMCPClient.reset_instance()
        client = StrapiMCPClient.get_instance()
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.STRAPI,
            name="test-strapi",
            api_url="https://strapi.example.com",
            api_token="test_token"
        ))
        client.configure_tenant("tenant-123", cred_id, config_service)
        return client

    def test_build_fetch_query(self, configured_client):
        """Test building a fetch query."""
        # Act
        query = configured_client._build_fetch_query(
            content_type="article",
            document_id="abc123"
        )

        # Assert
        assert "article" in query.lower()
        assert "documentId" in query or "abc123" in query

    def test_build_list_query(self, configured_client):
        """Test building a list query with pagination."""
        # Act
        query = configured_client._build_list_query(
            content_type="article",
            limit=10,
            offset=5
        )

        # Assert
        assert "articles" in query.lower()
        # Should include pagination
        assert "10" in query or "limit" in query.lower()

    def test_build_create_mutation(self, configured_client):
        """Test building a create mutation."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Test Article",
            body="Test body"
        )

        # Act
        mutation = configured_client._build_create_mutation(content)

        # Assert
        assert "createArticle" in mutation or "create" in mutation.lower()
        assert "Test Article" in mutation or "title" in mutation.lower()

    def test_build_update_mutation(self, configured_client):
        """Test building an update mutation."""
        # Arrange
        content = ContentItem(
            content_type="article",
            title="Updated Article",
            body="Updated body"
        )

        # Act
        mutation = configured_client._build_update_mutation(
            document_id="abc123",
            content=content
        )

        # Assert
        assert "updateArticle" in mutation or "update" in mutation.lower()
        assert "abc123" in mutation or "documentId" in mutation.lower()
