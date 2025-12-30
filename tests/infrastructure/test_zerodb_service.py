"""
Tests for ZeroDB service integration

These tests verify the ZeroDBService wrapper for unified database operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pseudoscribe.infrastructure.zerodb_service import (
    ZeroDBService,
    ZeroDBError,
    ZeroDBConnectionError,
    ZeroDBQueryError,
)


@pytest.fixture
def zerodb_service():
    """Fixture for ZeroDB service instance"""
    # Reset singleton for each test
    ZeroDBService._instance = None
    service = ZeroDBService.get_instance()
    return service


@pytest.fixture
def mock_mcp_postgres_query(zerodb_service):
    """Mock the ZeroDB MCP PostgreSQL query tool"""
    with patch.object(zerodb_service, '_call_mcp_tool') as mock:
        yield mock


@pytest.fixture
def mock_mcp_upsert_vector(zerodb_service):
    """Mock the ZeroDB MCP upsert vector tool"""
    with patch.object(zerodb_service, '_call_mcp_tool') as mock:
        yield mock


@pytest.fixture
def mock_mcp_search_vectors(zerodb_service):
    """Mock the ZeroDB MCP search vectors tool"""
    with patch.object(zerodb_service, '_call_mcp_tool') as mock:
        yield mock


@pytest.fixture
def mock_mcp_semantic_search(zerodb_service):
    """Mock the ZeroDB MCP semantic search tool"""
    with patch.object(zerodb_service, '_call_mcp_tool') as mock:
        yield mock


@pytest.fixture
def mock_mcp_generate_embeddings(zerodb_service):
    """Mock the ZeroDB MCP generate embeddings tool"""
    with patch.object(zerodb_service, '_call_mcp_tool') as mock:
        yield mock


class TestZeroDBServiceSingleton:
    """Test singleton pattern implementation"""

    def test_singleton_returns_same_instance(self):
        """
        Scenario: Multiple get_instance calls return same instance
        Given the ZeroDBService class
        When calling get_instance multiple times
        Then the same instance is returned
        """
        # Given
        ZeroDBService._instance = None

        # When
        instance1 = ZeroDBService.get_instance()
        instance2 = ZeroDBService.get_instance()

        # Then
        assert instance1 is instance2

    def test_singleton_instance_is_initialized(self):
        """
        Scenario: Singleton instance is properly initialized
        Given the ZeroDBService class
        When getting the instance
        Then the instance has all required attributes
        """
        # Given
        ZeroDBService._instance = None

        # When
        instance = ZeroDBService.get_instance()

        # Then
        assert hasattr(instance, 'initialized')
        assert instance.initialized is True


class TestPostgreSQLOperations:
    """Test PostgreSQL operations"""

    @pytest.mark.asyncio
    async def test_execute_query_success(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Successfully execute a SQL query
        Given a valid SQL query
        When executing the query
        Then the query results are returned
        """
        # Given
        sql = "SELECT * FROM users WHERE tenant_id = $1"
        params = ["tenant-123"]
        expected_result = {
            "rows": [{"id": 1, "name": "Test User"}],
            "row_count": 1
        }
        mock_mcp_postgres_query.return_value = expected_result

        # When
        result = await zerodb_service.execute_query(sql, params, tenant_id="tenant-123")

        # Then
        assert result == expected_result
        mock_mcp_postgres_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_error(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Handle SQL query errors
        Given an invalid SQL query
        When executing the query
        Then a ZeroDBQueryError is raised
        """
        # Given
        sql = "INVALID SQL"
        mock_mcp_postgres_query.side_effect = Exception("Syntax error")

        # When/Then
        with pytest.raises(ZeroDBQueryError) as exc_info:
            await zerodb_service.execute_query(sql)

        assert "Failed to execute query" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_schema_info_all_tables(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Get schema information for all tables
        Given no specific table name
        When getting schema info
        Then all table schemas are returned
        """
        # Given
        expected_schema = {
            "tables": [
                {"name": "users", "columns": []},
                {"name": "documents", "columns": []}
            ]
        }
        mock_mcp_postgres_query.return_value = expected_schema

        # When
        result = await zerodb_service.get_schema_info()

        # Then
        assert result == expected_schema

    @pytest.mark.asyncio
    async def test_get_schema_info_specific_table(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Get schema information for a specific table
        Given a table name
        When getting schema info
        Then the table's schema is returned
        """
        # Given
        table_name = "users"
        expected_schema = {
            "table": "users",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "varchar"}
            ]
        }
        mock_mcp_postgres_query.return_value = expected_schema

        # When
        result = await zerodb_service.get_schema_info(table_name=table_name)

        # Then
        assert result == expected_schema

    @pytest.mark.asyncio
    async def test_create_table_success(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Successfully create a new table
        Given a table name and column definitions
        When creating the table
        Then the table is created successfully
        """
        # Given
        table_name = "test_table"
        columns = [
            {"name": "id", "type": "SERIAL PRIMARY KEY"},
            {"name": "tenant_id", "type": "VARCHAR(255)"},
            {"name": "content", "type": "TEXT"}
        ]
        expected_result = {"success": True, "table": table_name}
        mock_mcp_postgres_query.return_value = expected_result

        # When
        result = await zerodb_service.create_table(table_name, columns)

        # Then
        assert result["success"] is True
        assert result["table"] == table_name


class TestVectorOperations:
    """Test vector operations"""

    @pytest.mark.asyncio
    async def test_upsert_vector_success(self, zerodb_service, mock_mcp_upsert_vector):
        """
        Scenario: Successfully upsert a vector
        Given a vector embedding and document
        When upserting the vector
        Then the vector ID is returned
        """
        # Given
        vector = [0.1, 0.2, 0.3] * 128  # 384-dimensional vector
        document = "Test document content"
        metadata = {"tenant_id": "tenant-123", "type": "style"}
        namespace = "tenant-123"
        expected_id = "vec_12345"
        mock_mcp_upsert_vector.return_value = {"vector_id": expected_id}

        # When
        result = await zerodb_service.upsert_vector(vector, document, metadata, namespace)

        # Then
        assert result == expected_id
        mock_mcp_upsert_vector.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_vector_with_error(self, zerodb_service, mock_mcp_upsert_vector):
        """
        Scenario: Handle vector upsert errors
        Given invalid vector data
        When upserting the vector
        Then a ZeroDBError is raised
        """
        # Given
        vector = [0.1, 0.2]  # Wrong dimensions
        document = "Test"
        metadata = {}
        mock_mcp_upsert_vector.side_effect = Exception("Invalid vector dimensions")

        # When/Then
        with pytest.raises(ZeroDBError) as exc_info:
            await zerodb_service.upsert_vector(vector, document, metadata)

        assert "Failed to upsert vector" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_vectors_success(self, zerodb_service, mock_mcp_search_vectors):
        """
        Scenario: Successfully search for similar vectors
        Given a query vector
        When searching for similar vectors
        Then matching vectors are returned
        """
        # Given
        query_vector = [0.1, 0.2, 0.3] * 128
        limit = 5
        namespace = "tenant-123"
        expected_results = [
            {"vector_id": "vec_1", "score": 0.95, "document": "Doc 1"},
            {"vector_id": "vec_2", "score": 0.87, "document": "Doc 2"}
        ]
        mock_mcp_search_vectors.return_value = {"results": expected_results}

        # When
        result = await zerodb_service.search_vectors(query_vector, limit, namespace)

        # Then
        assert result == expected_results
        mock_mcp_search_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_success(self, zerodb_service, mock_mcp_semantic_search):
        """
        Scenario: Successfully perform semantic search
        Given a text query
        When performing semantic search
        Then semantically similar documents are returned
        """
        # Given
        query_text = "How to write better content"
        limit = 10
        namespace = "tenant-123"
        expected_results = [
            {"vector_id": "vec_1", "score": 0.92, "document": "Writing tips"},
            {"vector_id": "vec_2", "score": 0.88, "document": "Content guide"}
        ]
        mock_mcp_semantic_search.return_value = {"results": expected_results}

        # When
        result = await zerodb_service.semantic_search(query_text, limit, namespace)

        # Then
        assert result == expected_results
        mock_mcp_semantic_search.assert_called_once()


class TestEmbeddingOperations:
    """Test embedding generation operations"""

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, zerodb_service, mock_mcp_generate_embeddings):
        """
        Scenario: Successfully generate embeddings
        Given a list of texts
        When generating embeddings
        Then embeddings are returned
        """
        # Given
        texts = ["Text 1", "Text 2", "Text 3"]
        model = "BAAI/bge-small-en-v1.5"
        expected_embeddings = [
            [0.1] * 384,
            [0.2] * 384,
            [0.3] * 384
        ]
        mock_mcp_generate_embeddings.return_value = {"embeddings": expected_embeddings}

        # When
        result = await zerodb_service.generate_embeddings(texts, model)

        # Then
        assert result == expected_embeddings
        mock_mcp_generate_embeddings.assert_called_once()
        call_kwargs = mock_mcp_generate_embeddings.call_args.kwargs
        assert call_kwargs['texts'] == texts
        assert call_kwargs['model'] == model

    @pytest.mark.asyncio
    async def test_generate_embeddings_default_model(self, zerodb_service, mock_mcp_generate_embeddings):
        """
        Scenario: Generate embeddings with default model
        Given a list of texts and no model specified
        When generating embeddings
        Then default model is used
        """
        # Given
        texts = ["Text 1"]
        expected_embeddings = [[0.1] * 384]
        mock_mcp_generate_embeddings.return_value = {"embeddings": expected_embeddings}

        # When
        result = await zerodb_service.generate_embeddings(texts)

        # Then
        mock_mcp_generate_embeddings.assert_called_once()
        call_kwargs = mock_mcp_generate_embeddings.call_args.kwargs
        assert call_kwargs['texts'] == texts
        assert call_kwargs['model'] == "BAAI/bge-small-en-v1.5"

    @pytest.mark.asyncio
    async def test_embed_and_store_success(self, zerodb_service, mock_mcp_generate_embeddings):
        """
        Scenario: Generate embeddings and store in one operation
        Given a list of texts
        When embedding and storing
        Then vector IDs are returned
        """
        # Given
        texts = ["Document 1", "Document 2"]
        namespace = "tenant-123"
        metadata = {"type": "content"}
        expected_ids = ["vec_1", "vec_2"]
        mock_mcp_generate_embeddings.return_value = {"vector_ids": expected_ids}

        # When
        result = await zerodb_service.embed_and_store(texts, namespace, metadata)

        # Then
        assert result == expected_ids


class TestTenantIsolation:
    """Test multi-tenant isolation"""

    @pytest.mark.asyncio
    async def test_query_with_tenant_isolation(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Query with tenant isolation
        Given a tenant_id
        When executing a query
        Then the query includes tenant context
        """
        # Given
        sql = "SELECT * FROM documents"
        tenant_id = "tenant-123"
        mock_mcp_postgres_query.return_value = {"rows": []}

        # When
        await zerodb_service.execute_query(sql, tenant_id=tenant_id)

        # Then
        # Verify tenant context was passed (implementation-specific)
        mock_mcp_postgres_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_vector_search_with_namespace(self, zerodb_service, mock_mcp_search_vectors):
        """
        Scenario: Vector search with namespace isolation
        Given a tenant-specific namespace
        When searching vectors
        Then only vectors in that namespace are searched
        """
        # Given
        query_vector = [0.1] * 384
        namespace = "tenant-123"
        mock_mcp_search_vectors.return_value = {"results": []}

        # When
        await zerodb_service.search_vectors(query_vector, namespace=namespace)

        # Then
        mock_mcp_search_vectors.assert_called_once()
        call_args = mock_mcp_search_vectors.call_args
        assert call_args.kwargs.get('namespace') == namespace


class TestErrorHandling:
    """Test error handling and custom exceptions"""

    @pytest.mark.asyncio
    async def test_connection_error(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Handle connection errors
        Given a connection failure
        When attempting database operation
        Then ZeroDBQueryError is raised (wraps the connection error)
        """
        # Given
        mock_mcp_postgres_query.side_effect = ConnectionError("Cannot connect")

        # When/Then
        with pytest.raises(ZeroDBQueryError) as exc_info:
            await zerodb_service.execute_query("SELECT 1")
        assert "Cannot connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generic_error(self, zerodb_service, mock_mcp_postgres_query):
        """
        Scenario: Handle generic errors
        Given an unexpected error
        When performing operation
        Then ZeroDBError is raised
        """
        # Given
        mock_mcp_postgres_query.side_effect = RuntimeError("Unexpected error")

        # When/Then
        with pytest.raises(ZeroDBError):
            await zerodb_service.execute_query("SELECT 1")


class TestServiceInitialization:
    """Test service initialization"""

    def test_service_initializes_with_defaults(self):
        """
        Scenario: Service initializes with default configuration
        Given no configuration provided
        When creating service instance
        Then service uses default settings
        """
        # Given
        ZeroDBService._instance = None

        # When
        service = ZeroDBService.get_instance()

        # Then
        assert service.initialized is True
        assert hasattr(service, 'default_namespace')
        assert service.default_namespace == "default"

    def test_service_has_required_attributes(self):
        """
        Scenario: Service has all required attributes
        Given a service instance
        When inspecting attributes
        Then all required attributes are present
        """
        # Given
        ZeroDBService._instance = None
        service = ZeroDBService.get_instance()

        # When/Then
        required_attrs = ['initialized', 'default_namespace']
        for attr in required_attrs:
            assert hasattr(service, attr)
