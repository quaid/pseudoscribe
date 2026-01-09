"""Strapi MCP Client.

Issue: INT-002 - Strapi MCP Integration

This module provides the MCP client for Strapi CMS integration:
- Singleton pattern for efficient connection management
- GraphQL query/mutation execution via MCP
- Multi-tenant isolation with per-tenant credentials
- Strapi 5.x compatibility (documentId, status parameter)
"""

import functools
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

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


class StrapiMCPError(Exception):
    """Base exception for Strapi MCP errors."""
    pass


class StrapiConnectionError(StrapiMCPError):
    """Raised when connection to Strapi fails."""
    pass


class StrapiQueryError(StrapiMCPError):
    """Raised when a GraphQL query/mutation fails."""
    pass


class StrapiContentNotFoundError(StrapiMCPError):
    """Raised when content is not found."""
    pass


def strapi_error_handler(func: Callable) -> Callable:
    """Decorator for consistent error handling."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except StrapiMCPError:
            raise
        except Exception as e:
            raise StrapiMCPError(f"Strapi operation failed: {str(e)}") from e
    return wrapper


@dataclass
class TenantConfig:
    """Configuration for a tenant's Strapi connection."""
    tenant_id: str
    credential_id: str
    config_service: TenantConfigService
    api_url: str
    api_token: str


class StrapiMCPClient:
    """MCP client for Strapi CMS integration.

    Follows the singleton pattern for efficient connection management.
    Supports multi-tenant isolation with per-tenant credentials.
    Compatible with Strapi 5.x (documentId, status parameter).
    """

    _instance: Optional['StrapiMCPClient'] = None

    def __init__(self):
        """Initialize the Strapi MCP client.

        Note: Use get_instance() instead of direct instantiation.
        """
        self._tenant_configs: Dict[str, TenantConfig] = {}

    @classmethod
    def get_instance(cls) -> 'StrapiMCPClient':
        """Get the singleton instance.

        Returns:
            The StrapiMCPClient singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance.

        Useful for testing or reconfiguration.
        """
        cls._instance = None

    def configure_tenant(
        self,
        tenant_id: str,
        credential_id: str,
        config_service: TenantConfigService
    ) -> None:
        """Configure a tenant's Strapi connection.

        Args:
            tenant_id: The tenant identifier
            credential_id: ID of stored credentials
            config_service: Service for accessing credentials
        """
        credentials = config_service.get_credentials(tenant_id, credential_id)
        if not credentials:
            raise ValueError(f"Credentials not found for tenant {tenant_id}")

        self._tenant_configs[tenant_id] = TenantConfig(
            tenant_id=tenant_id,
            credential_id=credential_id,
            config_service=config_service,
            api_url=credentials.api_url or "",
            api_token=credentials.api_token or ""
        )

    def is_tenant_configured(self, tenant_id: str) -> bool:
        """Check if a tenant is configured.

        Args:
            tenant_id: The tenant identifier

        Returns:
            True if configured, False otherwise
        """
        return tenant_id in self._tenant_configs

    def get_tenant_config(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a tenant.

        Args:
            tenant_id: The tenant identifier

        Returns:
            Configuration dictionary or None if not found
        """
        config = self._tenant_configs.get(tenant_id)
        if not config:
            return None

        return {
            "api_url": config.api_url,
            "credential_id": config.credential_id
        }

    async def _call_mcp_tool(
        self,
        tenant_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an MCP tool for Strapi operations.

        Args:
            tenant_id: The tenant identifier
            tool_name: Name of the MCP tool to call
            arguments: Arguments for the tool

        Returns:
            Response from the MCP tool
        """
        # In production, this would call the actual MCP server
        # For now, this is a placeholder that will be mocked in tests
        config = self._tenant_configs.get(tenant_id)
        if not config:
            raise StrapiConnectionError(f"Tenant {tenant_id} not configured")

        # Placeholder for actual MCP call
        raise NotImplementedError("MCP tool call not implemented")

    async def health_check(self, tenant_id: str) -> ConnectorStatus:
        """Check the health of the Strapi connection.

        Args:
            tenant_id: The tenant identifier

        Returns:
            ConnectorStatus with connection details
        """
        if not self.is_tenant_configured(tenant_id):
            return ConnectorStatus(
                connected=False,
                message="Tenant not configured",
                last_check=datetime.now()
            )

        try:
            # Simple introspection query to check connectivity
            result = await self._call_mcp_tool(
                tenant_id=tenant_id,
                tool_name="strapi_graphql",
                arguments={
                    "query": "{ __typename }"
                }
            )

            if "data" in result:
                return ConnectorStatus(
                    connected=True,
                    message="Strapi connection healthy",
                    last_check=datetime.now()
                )
            else:
                return ConnectorStatus(
                    connected=False,
                    message="Invalid response from Strapi",
                    last_check=datetime.now(),
                    error="No data in response"
                )

        except Exception as e:
            return ConnectorStatus(
                connected=False,
                message="Connection failed",
                last_check=datetime.now(),
                error=str(e)
            )

    def _build_fetch_query(
        self,
        content_type: str,
        document_id: str,
        status: Optional[str] = None
    ) -> str:
        """Build a GraphQL query to fetch content.

        Args:
            content_type: The content type (e.g., "article")
            document_id: The Strapi 5.x documentId
            status: Optional status filter (DRAFT, PUBLISHED)

        Returns:
            GraphQL query string
        """
        status_param = f', status: {status}' if status else ''
        return f'''
            query {{
                {content_type}(documentId: "{document_id}"{status_param}) {{
                    documentId
                    title
                    content
                    status
                    createdAt
                    updatedAt
                    locale
                }}
            }}
        '''

    def _build_list_query(
        self,
        content_type: str,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> str:
        """Build a GraphQL query to list content.

        Args:
            content_type: The content type (e.g., "article")
            limit: Maximum number of items
            offset: Number of items to skip
            status: Optional status filter

        Returns:
            GraphQL query string
        """
        # Pluralize content type for list query
        plural_type = f"{content_type}s"
        status_filter = f', filters: {{ status: {{ eq: "{status}" }} }}' if status else ''

        return f'''
            query {{
                {plural_type}(
                    pagination: {{ limit: {limit}, start: {offset} }}
                    {status_filter}
                ) {{
                    documentId
                    title
                    content
                    status
                    createdAt
                    updatedAt
                    locale
                }}
            }}
        '''

    def _build_create_mutation(self, content: ContentItem) -> str:
        """Build a GraphQL mutation to create content.

        Args:
            content: The content to create

        Returns:
            GraphQL mutation string
        """
        # Capitalize content type for mutation name
        type_name = content.content_type.capitalize()

        # Build data object
        data_fields = [
            f'title: "{content.title}"',
            f'content: "{content.body}"',
            f'locale: "{content.locale}"'
        ]

        # Add metadata fields if present
        for key, value in content.metadata.items():
            if isinstance(value, str):
                data_fields.append(f'{key}: "{value}"')
            elif isinstance(value, bool):
                data_fields.append(f'{key}: {str(value).lower()}')
            elif isinstance(value, (int, float)):
                data_fields.append(f'{key}: {value}')

        data_str = ", ".join(data_fields)

        return f'''
            mutation {{
                create{type_name}(data: {{ {data_str} }}) {{
                    documentId
                    title
                    content
                }}
            }}
        '''

    def _build_update_mutation(
        self,
        document_id: str,
        content: ContentItem
    ) -> str:
        """Build a GraphQL mutation to update content.

        Args:
            document_id: The Strapi 5.x documentId
            content: The updated content

        Returns:
            GraphQL mutation string
        """
        type_name = content.content_type.capitalize()

        data_fields = [
            f'title: "{content.title}"',
            f'content: "{content.body}"'
        ]

        data_str = ", ".join(data_fields)

        return f'''
            mutation {{
                update{type_name}(
                    documentId: "{document_id}"
                    data: {{ {data_str} }}
                ) {{
                    documentId
                    title
                    content
                }}
            }}
        '''

    def _parse_response_to_content_item(
        self,
        data: Dict[str, Any],
        content_type: str
    ) -> ContentItem:
        """Parse a GraphQL response to ContentItem.

        Args:
            data: The response data
            content_type: The content type

        Returns:
            ContentItem instance
        """
        # Parse timestamps
        created_at = None
        updated_at = None

        if data.get("createdAt"):
            created_at = datetime.fromisoformat(
                data["createdAt"].replace("Z", "+00:00")
            )
        if data.get("updatedAt"):
            updated_at = datetime.fromisoformat(
                data["updatedAt"].replace("Z", "+00:00")
            )

        # Map Strapi status to lowercase
        status = (data.get("status") or "draft").lower()

        return ContentItem(
            content_id=data.get("documentId"),
            content_type=content_type,
            title=data.get("title", ""),
            body=data.get("content", ""),
            status=status,
            locale=data.get("locale", "en"),
            created_at=created_at,
            updated_at=updated_at
        )

    def _check_for_errors(self, response: Dict[str, Any]) -> None:
        """Check response for GraphQL errors.

        Args:
            response: The GraphQL response

        Raises:
            StrapiQueryError: If errors are present
        """
        if "errors" in response:
            errors = response["errors"]
            error_messages = [e.get("message", "Unknown error") for e in errors]
            raise StrapiQueryError("; ".join(error_messages))

    @strapi_error_handler
    async def fetch_content(
        self,
        tenant_id: str,
        content_type: str,
        document_id: str,
        status: Optional[str] = None
    ) -> ContentItem:
        """Fetch content by documentId.

        Args:
            tenant_id: The tenant identifier
            content_type: The content type (e.g., "article")
            document_id: The Strapi 5.x documentId
            status: Optional status filter (DRAFT, PUBLISHED)

        Returns:
            ContentItem with the content data

        Raises:
            StrapiContentNotFoundError: If content not found
        """
        query = self._build_fetch_query(content_type, document_id, status)

        response = await self._call_mcp_tool(
            tenant_id=tenant_id,
            tool_name="strapi_graphql",
            arguments={"query": query}
        )

        self._check_for_errors(response)

        data = response.get("data", {}).get(content_type)
        if not data:
            raise StrapiContentNotFoundError(
                f"Content not found: {content_type}/{document_id}"
            )

        return self._parse_response_to_content_item(data, content_type)

    @strapi_error_handler
    async def push_content(
        self,
        tenant_id: str,
        content: ContentItem
    ) -> str:
        """Push new content to Strapi.

        Args:
            tenant_id: The tenant identifier
            content: The content to create

        Returns:
            The documentId of created content
        """
        mutation = self._build_create_mutation(content)

        response = await self._call_mcp_tool(
            tenant_id=tenant_id,
            tool_name="strapi_graphql",
            arguments={"query": mutation}
        )

        self._check_for_errors(response)

        type_name = content.content_type.capitalize()
        mutation_key = f"create{type_name}"

        result = response.get("data", {}).get(mutation_key, {})
        return result.get("documentId", "")

    @strapi_error_handler
    async def update_content(
        self,
        tenant_id: str,
        document_id: str,
        content: ContentItem
    ) -> bool:
        """Update existing content.

        Args:
            tenant_id: The tenant identifier
            document_id: The Strapi 5.x documentId
            content: The updated content

        Returns:
            True if updated, False if not found
        """
        mutation = self._build_update_mutation(document_id, content)

        response = await self._call_mcp_tool(
            tenant_id=tenant_id,
            tool_name="strapi_graphql",
            arguments={"query": mutation}
        )

        self._check_for_errors(response)

        type_name = content.content_type.capitalize()
        mutation_key = f"update{type_name}"

        result = response.get("data", {}).get(mutation_key)
        return result is not None

    @strapi_error_handler
    async def list_content(
        self,
        tenant_id: str,
        content_type: str,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[ContentItem]:
        """List content of a type.

        Args:
            tenant_id: The tenant identifier
            content_type: The content type
            limit: Maximum number of items
            offset: Number of items to skip
            status: Optional status filter

        Returns:
            List of ContentItems
        """
        query = self._build_list_query(content_type, limit, offset, status)

        response = await self._call_mcp_tool(
            tenant_id=tenant_id,
            tool_name="strapi_graphql",
            arguments={"query": query}
        )

        self._check_for_errors(response)

        plural_type = f"{content_type}s"
        items_data = response.get("data", {}).get(plural_type, [])

        return [
            self._parse_response_to_content_item(item, content_type)
            for item in items_data
        ]

    @strapi_error_handler
    async def get_schema(
        self,
        tenant_id: str,
        content_type: str
    ) -> ContentSchema:
        """Get schema for a content type via introspection.

        Args:
            tenant_id: The tenant identifier
            content_type: The content type

        Returns:
            ContentSchema with field definitions
        """
        type_name = content_type.capitalize()
        query = f'''
            query {{
                __type(name: "{type_name}") {{
                    name
                    fields {{
                        name
                        type {{
                            name
                            kind
                        }}
                    }}
                }}
            }}
        '''

        response = await self._call_mcp_tool(
            tenant_id=tenant_id,
            tool_name="strapi_graphql",
            arguments={"query": query}
        )

        self._check_for_errors(response)

        type_info = response.get("data", {}).get("__type", {})
        fields_data = type_info.get("fields", [])

        fields = []
        for f in fields_data:
            field_type = self._map_graphql_type(f.get("type", {}))
            fields.append(ContentField(
                name=f.get("name", ""),
                field_type=field_type,
                required=False  # Would need nullable info for accuracy
            ))

        return ContentSchema(
            content_type=content_type,
            fields=fields
        )

    def _map_graphql_type(self, type_info: Dict[str, Any]) -> FieldType:
        """Map GraphQL type to FieldType.

        Args:
            type_info: GraphQL type information

        Returns:
            FieldType enum value
        """
        kind = type_info.get("kind", "")
        name = type_info.get("name", "")

        if kind == "LIST":
            return FieldType.ARRAY
        elif name in ("String", "ID"):
            return FieldType.STRING
        elif name == "Int" or name == "Float":
            return FieldType.NUMBER
        elif name == "Boolean":
            return FieldType.BOOLEAN
        elif name in ("DateTime", "Date"):
            return FieldType.DATETIME
        else:
            return FieldType.OBJECT

    @strapi_error_handler
    async def list_content_types(self, tenant_id: str) -> List[str]:
        """List available content types via introspection.

        Args:
            tenant_id: The tenant identifier

        Returns:
            List of content type names
        """
        query = '''
            query {
                __schema {
                    types {
                        name
                        kind
                    }
                }
            }
        '''

        response = await self._call_mcp_tool(
            tenant_id=tenant_id,
            tool_name="strapi_graphql",
            arguments={"query": query}
        )

        self._check_for_errors(response)

        types = response.get("data", {}).get("__schema", {}).get("types", [])

        # Filter to only content types (OBJECT, not Query/Mutation/Scalar)
        excluded = {
            "Query", "Mutation", "Subscription",
            "String", "Int", "Float", "Boolean", "ID", "DateTime"
        }

        return [
            t.get("name", "")
            for t in types
            if t.get("kind") == "OBJECT"
            and t.get("name", "") not in excluded
            and not t.get("name", "").startswith("__")
        ]
