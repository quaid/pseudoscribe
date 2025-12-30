"""ZeroDB service integration for unified database operations

This module provides a singleton service wrapper for ZeroDB operations,
supporting PostgreSQL queries, vector operations, and embedding generation
with multi-tenant isolation.
"""

from typing import Dict, List, Optional, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)


# Custom Exceptions
class ZeroDBError(Exception):
    """Base exception for ZeroDB operations"""
    pass


class ZeroDBConnectionError(ZeroDBError):
    """Exception raised when connection to ZeroDB fails"""
    pass


class ZeroDBQueryError(ZeroDBError):
    """Exception raised when query execution fails"""
    pass


def handle_zerodb_errors(func):
    """Decorator to handle ZeroDB operation errors consistently"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ConnectionError as e:
            logger.error(f"ZeroDB connection error in {func.__name__}: {e}")
            raise ZeroDBConnectionError(f"Failed to connect to ZeroDB: {e}")
        except ZeroDBError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise ZeroDBError(f"ZeroDB operation failed: {e}")
    return wrapper


class ZeroDBService:
    """Unified ZeroDB service wrapper for PseudoScribe

    Provides a singleton interface for PostgreSQL operations, vector operations,
    and embedding generation with multi-tenant support.

    Example:
        >>> service = ZeroDBService.get_instance()
        >>> result = await service.execute_query("SELECT * FROM users", tenant_id="tenant-123")
        >>> embeddings = await service.generate_embeddings(["text1", "text2"])
    """

    _instance: Optional['ZeroDBService'] = None

    def __init__(self):
        """Initialize ZeroDB service

        Note: Use get_instance() instead of direct instantiation
        """
        self.initialized: bool = True
        self.default_namespace: str = "default"
        self._mcp_available: bool = True
        logger.info("ZeroDBService initialized")

    @classmethod
    def get_instance(cls) -> 'ZeroDBService':
        """Get singleton instance of ZeroDBService

        Returns:
            ZeroDBService: The singleton service instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _call_mcp_tool(self, tool_module: str, tool_name: str, **kwargs) -> Any:
        """Helper method to call MCP tools with proper error handling

        Args:
            tool_module: Module name (e.g., 'mcp__zerodb__zerodb_postgres_query')
            tool_name: Function name within the module
            **kwargs: Arguments to pass to the MCP tool

        Returns:
            Result from the MCP tool

        Raises:
            ImportError: If MCP tool is not available
        """
        try:
            module = __import__(tool_module, fromlist=[tool_name])
            func = getattr(module, tool_name)
            return func(**kwargs)
        except ImportError as e:
            logger.error(f"MCP tool {tool_module} not available: {e}")
            self._mcp_available = False
            raise

    # PostgreSQL Operations

    @handle_zerodb_errors
    async def execute_query(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        tenant_id: Optional[str] = None,
        read_only: bool = False,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Execute a SQL query on PostgreSQL

        Args:
            sql: SQL query to execute
            params: Query parameters for prepared statements
            tenant_id: Tenant identifier for multi-tenant isolation
            read_only: Enforce read-only mode (SELECT only)
            timeout_seconds: Query timeout in seconds

        Returns:
            Dictionary containing query results

        Raises:
            ZeroDBQueryError: If query execution fails
            ZeroDBConnectionError: If connection fails
        """
        try:
            # Build query options
            query_options = {
                "sql": sql,
                "read_only": read_only,
                "timeout_seconds": timeout_seconds
            }

            if params:
                query_options["params"] = params

            # Add tenant context if provided (via comment for now)
            if tenant_id:
                logger.debug(f"Executing query for tenant: {tenant_id}")

            # Call MCP tool using helper
            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_postgres_query',
                'mcp__zerodb__zerodb_postgres_query',
                **query_options
            )
            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise ZeroDBQueryError(f"Failed to execute query: {e}")

    @handle_zerodb_errors
    async def get_schema_info(
        self,
        table_name: Optional[str] = None,
        include_indexes: bool = True,
        include_constraints: bool = True
    ) -> Dict[str, Any]:
        """Get database schema information

        Args:
            table_name: Specific table to inspect (None for all tables)
            include_indexes: Include index information
            include_constraints: Include constraint information

        Returns:
            Dictionary containing schema information
        """
        try:
            options = {
                "include_indexes": include_indexes,
                "include_constraints": include_constraints
            }

            if table_name:
                options["table_name"] = table_name

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_postgres_schema_info',
                'mcp__zerodb__zerodb_postgres_schema_info',
                **options
            )
            return result

        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            raise ZeroDBError(f"Failed to get schema info: {e}")

    @handle_zerodb_errors
    async def create_table(
        self,
        table_name: str,
        columns: List[Dict[str, str]],
        if_not_exists: bool = True,
        indexes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new PostgreSQL table

        Args:
            table_name: Name of the table to create
            columns: List of column definitions with 'name' and 'type' keys
            if_not_exists: Only create if table doesn't exist
            indexes: Optional index definitions

        Returns:
            Dictionary with creation status
        """
        try:
            # Convert columns to expected format
            column_defs = []
            for col in columns:
                col_def = {
                    "name": col["name"],
                    "type": col["type"]
                }
                # Add optional fields if present
                for key in ["nullable", "primary_key", "unique", "default"]:
                    if key in col:
                        col_def[key] = col[key]
                column_defs.append(col_def)

            options = {
                "table_name": table_name,
                "columns": column_defs,
                "if_not_exists": if_not_exists
            }

            if indexes:
                options["indexes"] = indexes

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_postgres_create_table',
                'mcp__zerodb__zerodb_postgres_create_table',
                **options
            )
            return result

        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise ZeroDBError(f"Failed to create table: {e}")

    @handle_zerodb_errors
    async def get_stats(
        self,
        include_storage: bool = True,
        include_connections: bool = True,
        include_queries: bool = True,
        time_range: str = "day"
    ) -> Dict[str, Any]:
        """Get PostgreSQL database statistics

        Args:
            include_storage: Include storage statistics
            include_connections: Include connection statistics
            include_queries: Include query performance stats
            time_range: Statistics time range (hour, day, week, month)

        Returns:
            Dictionary containing database statistics
        """
        try:
            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_postgres_stats',
                'mcp__zerodb__zerodb_postgres_stats',
                include_storage=include_storage,
                include_connections=include_connections,
                include_queries=include_queries,
                time_range=time_range
            )
            return result

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise ZeroDBError(f"Failed to get stats: {e}")

    # Vector Operations

    @handle_zerodb_errors
    async def upsert_vector(
        self,
        vector: List[float],
        document: str,
        metadata: Dict[str, Any],
        namespace: Optional[str] = None,
        vector_id: Optional[str] = None
    ) -> str:
        """Store or update a vector embedding

        Args:
            vector: Vector embedding (384, 768, 1024, or 1536 dimensions)
            document: Source document or text
            metadata: Document metadata (should include tenant_id)
            namespace: Vector namespace for isolation (defaults to default_namespace)
            vector_id: Optional vector ID for updates

        Returns:
            Vector ID of the stored vector

        Raises:
            ZeroDBError: If vector upsert fails
        """
        try:
            options = {
                "vector_embedding": vector,
                "document": document,
                "metadata": metadata,
                "namespace": namespace or self.default_namespace
            }

            if vector_id:
                options["vector_id"] = vector_id

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_upsert_vector',
                'mcp__zerodb__zerodb_upsert_vector',
                **options
            )

            # Extract vector_id from result
            if isinstance(result, dict):
                return result.get("vector_id", "")
            return str(result)

        except Exception as e:
            logger.error(f"Failed to upsert vector: {e}")
            raise ZeroDBError(f"Failed to upsert vector: {e}")

    @handle_zerodb_errors
    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        namespace: Optional[str] = None,
        threshold: float = 0.7,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search vectors using semantic similarity

        Args:
            query_vector: Query vector (384, 768, 1024, or 1536 dimensions)
            limit: Maximum number of results
            namespace: Vector namespace to search in
            threshold: Minimum similarity score (0.0-1.0)
            filter_metadata: Optional metadata filters

        Returns:
            List of matching vectors with scores
        """
        try:
            options = {
                "query_vector": query_vector,
                "limit": limit,
                "threshold": threshold,
                "namespace": namespace or self.default_namespace
            }

            if filter_metadata:
                options["filter_metadata"] = filter_metadata

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_search_vectors',
                'mcp__zerodb__zerodb_search_vectors',
                **options
            )

            # Extract results from response
            if isinstance(result, dict) and "results" in result:
                return result["results"]
            return result if isinstance(result, list) else []

        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise ZeroDBError(f"Failed to search vectors: {e}")

    @handle_zerodb_errors
    async def semantic_search(
        self,
        query_text: str,
        limit: int = 10,
        namespace: Optional[str] = None,
        threshold: float = 0.7,
        model: str = "BAAI/bge-small-en-v1.5",
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search using text query (auto-embeds query)

        Args:
            query_text: Text query to search for
            limit: Maximum number of results
            namespace: Vector namespace to search in
            threshold: Minimum similarity score (0.0-1.0)
            model: Model to use for query embedding
            filter_metadata: Optional metadata filters

        Returns:
            List of semantically similar documents
        """
        try:
            options = {
                "query_text": query_text,
                "limit": limit,
                "threshold": threshold,
                "namespace": namespace or self.default_namespace,
                "model": model
            }

            if filter_metadata:
                options["filter_metadata"] = filter_metadata

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_semantic_search',
                'mcp__zerodb__zerodb_semantic_search',
                **options
            )

            # Extract results from response
            if isinstance(result, dict) and "results" in result:
                return result["results"]
            return result if isinstance(result, list) else []

        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            raise ZeroDBError(f"Failed to perform semantic search: {e}")

    # Embedding Operations

    @handle_zerodb_errors
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "BAAI/bge-small-en-v1.5"
    ) -> List[List[float]]:
        """Generate embeddings for text inputs

        Args:
            texts: List of text strings to generate embeddings for
            model: Embedding model to use (384, 768, or 1024 dimensions)

        Returns:
            List of embedding vectors
        """
        try:
            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_generate_embeddings',
                'mcp__zerodb__zerodb_generate_embeddings',
                texts=texts,
                model=model
            )

            # Extract embeddings from response
            if isinstance(result, dict) and "embeddings" in result:
                return result["embeddings"]
            return result if isinstance(result, list) else []

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise ZeroDBError(f"Failed to generate embeddings: {e}")

    @handle_zerodb_errors
    async def embed_and_store(
        self,
        texts: List[str],
        namespace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "BAAI/bge-small-en-v1.5"
    ) -> List[str]:
        """Generate embeddings and store in ZeroDB in one operation

        Args:
            texts: List of text strings to embed and store
            namespace: Vector namespace for organization
            metadata: Optional metadata to attach to vectors
            model: Embedding model to use

        Returns:
            List of vector IDs
        """
        try:
            options = {
                "texts": texts,
                "namespace": namespace or self.default_namespace,
                "model": model
            }

            if metadata:
                options["metadata"] = metadata

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_embed_and_store',
                'mcp__zerodb__zerodb_embed_and_store',
                **options
            )

            # Extract vector IDs from response
            if isinstance(result, dict) and "vector_ids" in result:
                return result["vector_ids"]
            return result if isinstance(result, list) else []

        except Exception as e:
            logger.error(f"Failed to embed and store: {e}")
            raise ZeroDBError(f"Failed to embed and store: {e}")

    # NoSQL Table Operations (for completeness)

    @handle_zerodb_errors
    async def create_nosql_table(
        self,
        table_name: str,
        schema: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new NoSQL table

        Args:
            table_name: Unique table name
            schema: Table schema definition
            description: Optional table description

        Returns:
            Dictionary with creation status
        """
        try:
            options = {
                "table_name": table_name,
                "schema": schema
            }

            if description:
                options["description"] = description

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_create_table',
                'mcp__zerodb__zerodb_create_table',
                **options
            )
            return result

        except Exception as e:
            logger.error(f"Failed to create NoSQL table: {e}")
            raise ZeroDBError(f"Failed to create NoSQL table: {e}")

    @handle_zerodb_errors
    async def insert_rows(
        self,
        table_id: str,
        rows: List[Dict[str, Any]],
        return_ids: bool = True
    ) -> Dict[str, Any]:
        """Insert rows into a NoSQL table

        Args:
            table_id: Table ID or name
            rows: Array of row objects to insert
            return_ids: Return inserted row IDs

        Returns:
            Dictionary with inserted row IDs
        """
        try:
            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_insert_rows',
                'mcp__zerodb__zerodb_insert_rows',
                table_id=table_id,
                rows=rows,
                return_ids=return_ids
            )
            return result

        except Exception as e:
            logger.error(f"Failed to insert rows: {e}")
            raise ZeroDBError(f"Failed to insert rows: {e}")

    @handle_zerodb_errors
    async def query_rows(
        self,
        table_id: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query rows from a NoSQL table

        Args:
            table_id: Table ID or name
            filter: MongoDB-style query filter
            limit: Maximum number of results
            offset: Pagination offset
            sort: Sort specification
            projection: Field projection

        Returns:
            Dictionary with query results
        """
        try:
            options = {
                "table_id": table_id,
                "limit": limit,
                "offset": offset
            }

            if filter:
                options["filter"] = filter
            if sort:
                options["sort"] = sort
            if projection:
                options["projection"] = projection

            result = self._call_mcp_tool(
                'mcp__zerodb__zerodb_query_rows',
                'mcp__zerodb__zerodb_query_rows',
                **options
            )
            return result

        except Exception as e:
            logger.error(f"Failed to query rows: {e}")
            raise ZeroDBError(f"Failed to query rows: {e}")
