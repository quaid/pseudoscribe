"""Tests for Content Connector Base.

Issue: INT-001 - Content Connector Base

These tests verify:
- BaseContentConnector abstract interface
- ContentItem unified content model
- Connector registration and discovery
- Credential integration with TenantConfigService
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from pseudoscribe.infrastructure.content_connector import (
    BaseContentConnector,
    ContentItem,
    ContentSchema,
    ContentField,
    FieldType,
    ConnectorRegistry,
    ConnectorStatus,
    ConnectorError,
    ContentNotFoundError
)
from pseudoscribe.infrastructure.tenant_config_service import (
    TenantConfigService,
    ConnectorCredentials,
    CredentialType
)


class MockConnector(BaseContentConnector):
    """Mock connector implementation for testing."""

    connector_type = "mock"

    def __init__(self, tenant_id: str, credential_id: str, config_service: TenantConfigService):
        super().__init__(tenant_id, credential_id, config_service)
        self._items: Dict[str, ContentItem] = {}

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def health_check(self) -> ConnectorStatus:
        return ConnectorStatus(
            connected=True,
            message="Mock connector healthy",
            last_check=datetime.now()
        )

    async def fetch_content(self, content_id: str) -> ContentItem:
        if content_id not in self._items:
            raise ContentNotFoundError(f"Content {content_id} not found")
        return self._items[content_id]

    async def push_content(self, content: ContentItem) -> str:
        content_id = content.content_id or f"mock-{len(self._items)}"
        content.content_id = content_id
        self._items[content_id] = content
        return content_id

    async def update_content(self, content_id: str, content: ContentItem) -> bool:
        if content_id not in self._items:
            return False
        content.content_id = content_id
        self._items[content_id] = content
        return True

    async def list_content(
        self,
        content_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ContentItem]:
        items = list(self._items.values())
        if content_type:
            items = [i for i in items if i.content_type == content_type]
        return items[offset:offset + limit]

    async def get_schema(self, content_type: str) -> ContentSchema:
        return ContentSchema(
            content_type=content_type,
            fields=[
                ContentField(name="title", field_type=FieldType.STRING, required=True),
                ContentField(name="body", field_type=FieldType.RICHTEXT, required=True)
            ]
        )


class TestContentItem:
    """Tests for ContentItem model."""

    def test_create_content_item(self):
        """Test creating a ContentItem."""
        # Act
        item = ContentItem(
            content_type="article",
            title="Test Article",
            body="This is the article body.",
            metadata={"author": "Test Author"}
        )

        # Assert
        assert item.content_type == "article"
        assert item.title == "Test Article"
        assert item.body == "This is the article body."
        assert item.metadata["author"] == "Test Author"

    def test_content_item_with_id(self):
        """Test ContentItem with explicit ID."""
        # Act
        item = ContentItem(
            content_id="article-123",
            content_type="article",
            title="Existing Article",
            body="Body content"
        )

        # Assert
        assert item.content_id == "article-123"

    def test_content_item_timestamps(self):
        """Test ContentItem timestamp handling."""
        # Arrange
        now = datetime.now()

        # Act
        item = ContentItem(
            content_type="article",
            title="Test",
            body="Body",
            created_at=now,
            updated_at=now
        )

        # Assert
        assert item.created_at == now
        assert item.updated_at == now

    def test_content_item_to_dict(self):
        """Test converting ContentItem to dictionary."""
        # Arrange
        item = ContentItem(
            content_id="test-1",
            content_type="article",
            title="Test",
            body="Body content",
            metadata={"key": "value"}
        )

        # Act
        result = item.to_dict()

        # Assert
        assert result["content_id"] == "test-1"
        assert result["content_type"] == "article"
        assert result["title"] == "Test"
        assert result["metadata"]["key"] == "value"

    def test_content_item_from_dict(self):
        """Test creating ContentItem from dictionary."""
        # Arrange
        data = {
            "content_id": "test-1",
            "content_type": "article",
            "title": "From Dict",
            "body": "Body from dict",
            "metadata": {"source": "test"}
        }

        # Act
        item = ContentItem.from_dict(data)

        # Assert
        assert item.content_id == "test-1"
        assert item.title == "From Dict"
        assert item.metadata["source"] == "test"


class TestContentSchema:
    """Tests for ContentSchema model."""

    def test_create_schema(self):
        """Test creating a ContentSchema."""
        # Act
        schema = ContentSchema(
            content_type="article",
            fields=[
                ContentField(name="title", field_type=FieldType.STRING, required=True),
                ContentField(name="body", field_type=FieldType.RICHTEXT, required=True),
                ContentField(name="tags", field_type=FieldType.ARRAY, required=False)
            ]
        )

        # Assert
        assert schema.content_type == "article"
        assert len(schema.fields) == 3
        assert schema.fields[0].name == "title"
        assert schema.fields[0].required is True

    def test_schema_get_required_fields(self):
        """Test getting required fields from schema."""
        # Arrange
        schema = ContentSchema(
            content_type="article",
            fields=[
                ContentField(name="title", field_type=FieldType.STRING, required=True),
                ContentField(name="body", field_type=FieldType.RICHTEXT, required=True),
                ContentField(name="tags", field_type=FieldType.ARRAY, required=False)
            ]
        )

        # Act
        required = schema.get_required_fields()

        # Assert
        assert len(required) == 2
        assert all(f.required for f in required)


class TestBaseContentConnector:
    """Tests for BaseContentConnector abstract class."""

    @pytest.fixture
    def config_service(self):
        """Create a TenantConfigService instance."""
        return TenantConfigService()

    @pytest.fixture
    def mock_connector(self, config_service):
        """Create a mock connector instance."""
        # Store credentials first
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.CUSTOM,
            name="mock-connector",
            api_url="https://mock.example.com",
            api_token="mock_token"
        ))
        return MockConnector("tenant-123", cred_id, config_service)

    @pytest.mark.asyncio
    async def test_connector_connect(self, mock_connector):
        """Test connector connection."""
        # Act
        result = await mock_connector.connect()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_connector_health_check(self, mock_connector):
        """Test connector health check."""
        # Act
        status = await mock_connector.health_check()

        # Assert
        assert status.connected is True
        assert "healthy" in status.message.lower()

    @pytest.mark.asyncio
    async def test_fetch_content(self, mock_connector):
        """Test fetching content."""
        # Arrange
        item = ContentItem(
            content_type="article",
            title="Test Article",
            body="Article body"
        )
        content_id = await mock_connector.push_content(item)

        # Act
        fetched = await mock_connector.fetch_content(content_id)

        # Assert
        assert fetched.title == "Test Article"
        assert fetched.body == "Article body"

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_content(self, mock_connector):
        """Test fetching nonexistent content raises error."""
        # Act & Assert
        with pytest.raises(ContentNotFoundError):
            await mock_connector.fetch_content("nonexistent-id")

    @pytest.mark.asyncio
    async def test_push_content(self, mock_connector):
        """Test pushing new content."""
        # Arrange
        item = ContentItem(
            content_type="article",
            title="New Article",
            body="New body content"
        )

        # Act
        content_id = await mock_connector.push_content(item)

        # Assert
        assert content_id is not None
        fetched = await mock_connector.fetch_content(content_id)
        assert fetched.title == "New Article"

    @pytest.mark.asyncio
    async def test_update_content(self, mock_connector):
        """Test updating existing content."""
        # Arrange
        item = ContentItem(
            content_type="article",
            title="Original Title",
            body="Original body"
        )
        content_id = await mock_connector.push_content(item)

        # Act
        updated_item = ContentItem(
            content_type="article",
            title="Updated Title",
            body="Updated body"
        )
        result = await mock_connector.update_content(content_id, updated_item)

        # Assert
        assert result is True
        fetched = await mock_connector.fetch_content(content_id)
        assert fetched.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_list_content(self, mock_connector):
        """Test listing content."""
        # Arrange
        for i in range(3):
            await mock_connector.push_content(ContentItem(
                content_type="article",
                title=f"Article {i}",
                body=f"Body {i}"
            ))

        # Act
        items = await mock_connector.list_content()

        # Assert
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_list_content_with_type_filter(self, mock_connector):
        """Test listing content filtered by type."""
        # Arrange
        await mock_connector.push_content(ContentItem(
            content_type="article",
            title="Article",
            body="Body"
        ))
        await mock_connector.push_content(ContentItem(
            content_type="blog",
            title="Blog Post",
            body="Body"
        ))

        # Act
        articles = await mock_connector.list_content(content_type="article")

        # Assert
        assert len(articles) == 1
        assert articles[0].content_type == "article"

    @pytest.mark.asyncio
    async def test_get_schema(self, mock_connector):
        """Test getting content schema."""
        # Act
        schema = await mock_connector.get_schema("article")

        # Assert
        assert schema.content_type == "article"
        assert len(schema.fields) > 0

    def test_connector_has_tenant_id(self, mock_connector):
        """Test that connector stores tenant ID."""
        # Assert
        assert mock_connector.tenant_id == "tenant-123"

    def test_connector_has_credential_id(self, mock_connector):
        """Test that connector stores credential ID."""
        # Assert
        assert mock_connector.credential_id is not None

    def test_get_credentials(self, mock_connector):
        """Test getting credentials from connector."""
        # Act
        creds = mock_connector.get_credentials()

        # Assert
        assert creds is not None
        assert creds.api_url == "https://mock.example.com"


class TestConnectorRegistry:
    """Tests for ConnectorRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry."""
        return ConnectorRegistry()

    def test_register_connector(self, registry):
        """Test registering a connector class."""
        # Act
        registry.register("mock", MockConnector)

        # Assert
        assert "mock" in registry.list_types()

    def test_get_connector_class(self, registry):
        """Test getting a registered connector class."""
        # Arrange
        registry.register("mock", MockConnector)

        # Act
        connector_class = registry.get("mock")

        # Assert
        assert connector_class == MockConnector

    def test_get_unregistered_connector(self, registry):
        """Test getting an unregistered connector raises error."""
        # Act & Assert
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list_connector_types(self, registry):
        """Test listing all registered connector types."""
        # Arrange
        registry.register("mock1", MockConnector)
        registry.register("mock2", MockConnector)

        # Act
        types = registry.list_types()

        # Assert
        assert "mock1" in types
        assert "mock2" in types

    def test_create_connector_instance(self, registry):
        """Test creating a connector instance from registry."""
        # Arrange
        registry.register("mock", MockConnector)
        config_service = TenantConfigService()
        cred_id = config_service.store_credentials("tenant-123", ConnectorCredentials(
            credential_type=CredentialType.CUSTOM,
            name="test",
            api_url="https://test.example.com",
            api_token="token"
        ))

        # Act
        connector = registry.create(
            "mock",
            tenant_id="tenant-123",
            credential_id=cred_id,
            config_service=config_service
        )

        # Assert
        assert isinstance(connector, MockConnector)
        assert connector.tenant_id == "tenant-123"


class TestConnectorStatus:
    """Tests for ConnectorStatus model."""

    def test_create_status(self):
        """Test creating a ConnectorStatus."""
        # Act
        status = ConnectorStatus(
            connected=True,
            message="All systems operational",
            last_check=datetime.now()
        )

        # Assert
        assert status.connected is True
        assert "operational" in status.message

    def test_status_with_error(self):
        """Test ConnectorStatus with error."""
        # Act
        status = ConnectorStatus(
            connected=False,
            message="Connection failed",
            error="Timeout after 30s"
        )

        # Assert
        assert status.connected is False
        assert status.error == "Timeout after 30s"
