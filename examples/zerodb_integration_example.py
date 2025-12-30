"""
ZeroDB Service Integration Example

This example demonstrates how to use the ZeroDBService for various operations
in PseudoScribe, including PostgreSQL queries, vector operations, and embeddings.
"""

import asyncio
import logging
from typing import List, Dict, Any

from pseudoscribe.infrastructure.zerodb_service import (
    ZeroDBService,
    ZeroDBError,
    ZeroDBConnectionError,
    ZeroDBQueryError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_postgresql_operations():
    """Example PostgreSQL operations"""
    logger.info("=== PostgreSQL Operations Example ===")

    service = ZeroDBService.get_instance()

    try:
        # 1. Get schema information
        logger.info("Fetching schema information...")
        schema = await service.get_schema_info()
        logger.info(f"Schema info: {schema}")

        # 2. Create a table
        logger.info("Creating a table...")
        columns = [
            {"name": "id", "type": "SERIAL PRIMARY KEY"},
            {"name": "tenant_id", "type": "VARCHAR(255)", "nullable": False},
            {"name": "title", "type": "VARCHAR(500)"},
            {"name": "content", "type": "TEXT"},
            {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
        ]

        result = await service.create_table(
            "sample_documents",
            columns,
            if_not_exists=True,
            indexes=[{"columns": ["tenant_id"]}]
        )
        logger.info(f"Table created: {result}")

        # 3. Execute a query
        logger.info("Executing a query...")
        query_result = await service.execute_query(
            "SELECT COUNT(*) FROM sample_documents WHERE tenant_id = $1",
            params=["tenant-123"],
            tenant_id="tenant-123",
            read_only=True
        )
        logger.info(f"Query result: {query_result}")

        # 4. Get database statistics
        logger.info("Fetching database statistics...")
        stats = await service.get_stats(time_range="day")
        logger.info(f"Database stats: {stats}")

    except ZeroDBQueryError as e:
        logger.error(f"Query error: {e}")
    except ZeroDBConnectionError as e:
        logger.error(f"Connection error: {e}")
    except ZeroDBError as e:
        logger.error(f"ZeroDB error: {e}")


async def example_vector_operations():
    """Example vector operations"""
    logger.info("=== Vector Operations Example ===")

    service = ZeroDBService.get_instance()

    try:
        # Sample documents
        documents = [
            "Write clear and concise introductions.",
            "Use active voice for better engagement.",
            "Keep paragraphs short and focused.",
            "Include relevant examples to illustrate points.",
            "End with a strong conclusion."
        ]

        # 1. Generate embeddings for documents
        logger.info("Generating embeddings...")
        embeddings = await service.generate_embeddings(
            texts=documents,
            model="BAAI/bge-small-en-v1.5"
        )
        logger.info(f"Generated {len(embeddings)} embeddings")

        # 2. Store vectors with metadata
        logger.info("Storing vectors...")
        vector_ids = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            vector_id = await service.upsert_vector(
                vector=embedding,
                document=doc,
                metadata={
                    "tenant_id": "tenant-123",
                    "document_type": "writing_tip",
                    "index": i,
                    "category": "style_guide"
                },
                namespace="tenant-123"
            )
            vector_ids.append(vector_id)
            logger.info(f"Stored vector {i}: {vector_id}")

        # 3. Search for similar vectors
        logger.info("Searching for similar vectors...")
        query = "How to create engaging content?"
        query_embeddings = await service.generate_embeddings([query])

        results = await service.search_vectors(
            query_vector=query_embeddings[0],
            limit=3,
            namespace="tenant-123",
            threshold=0.5,
            filter_metadata={"document_type": "writing_tip"}
        )

        logger.info(f"Found {len(results)} similar documents:")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. Score: {result.get('score', 0):.3f}")
            logger.info(f"     Document: {result.get('document', 'N/A')}")

        # 4. Semantic search (text-to-text)
        logger.info("Performing semantic search...")
        semantic_results = await service.semantic_search(
            query_text=query,
            limit=3,
            namespace="tenant-123",
            threshold=0.5,
            model="BAAI/bge-small-en-v1.5"
        )

        logger.info(f"Semantic search found {len(semantic_results)} results")

    except ZeroDBError as e:
        logger.error(f"Vector operation error: {e}")


async def example_embed_and_store():
    """Example: embed and store in one operation"""
    logger.info("=== Embed and Store Example ===")

    service = ZeroDBService.get_instance()

    try:
        # Documents to process
        writing_tips = [
            "Start with an outline to organize your thoughts.",
            "Read your work aloud to catch awkward phrasing.",
            "Use transitions to connect ideas smoothly.",
            "Vary sentence length for better rhythm.",
            "Revise for clarity, not just grammar."
        ]

        # Embed and store in one operation
        logger.info("Embedding and storing documents...")
        vector_ids = await service.embed_and_store(
            texts=writing_tips,
            namespace="tenant-123",
            metadata={
                "tenant_id": "tenant-123",
                "category": "writing_tips",
                "source": "style_guide_v2"
            },
            model="BAAI/bge-small-en-v1.5"
        )

        logger.info(f"Stored {len(vector_ids)} vectors:")
        for i, vector_id in enumerate(vector_ids):
            logger.info(f"  {i+1}. {vector_id}: {writing_tips[i][:50]}...")

    except ZeroDBError as e:
        logger.error(f"Embed and store error: {e}")


async def example_nosql_operations():
    """Example NoSQL table operations"""
    logger.info("=== NoSQL Operations Example ===")

    service = ZeroDBService.get_instance()

    try:
        # 1. Create a NoSQL table
        logger.info("Creating NoSQL table...")
        schema = {
            "fields": {
                "user_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "preferences": {"type": "object"},
                "settings": {"type": "object"},
                "created_at": {"type": "timestamp"}
            },
            "indexes": ["user_id", "tenant_id"]
        }

        result = await service.create_nosql_table(
            table_name="user_preferences",
            schema=schema,
            description="User preferences and settings"
        )
        logger.info(f"Table created: {result}")

        # 2. Insert rows
        logger.info("Inserting rows...")
        rows = [
            {
                "user_id": "user-123",
                "tenant_id": "tenant-123",
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "notifications": True
                },
                "settings": {
                    "auto_save": True,
                    "spell_check": True
                }
            },
            {
                "user_id": "user-456",
                "tenant_id": "tenant-123",
                "preferences": {
                    "theme": "light",
                    "language": "en",
                    "notifications": False
                },
                "settings": {
                    "auto_save": False,
                    "spell_check": True
                }
            }
        ]

        insert_result = await service.insert_rows(
            table_id="user_preferences",
            rows=rows,
            return_ids=True
        )
        logger.info(f"Inserted rows: {insert_result}")

        # 3. Query rows
        logger.info("Querying rows...")
        query_result = await service.query_rows(
            table_id="user_preferences",
            filter={"tenant_id": "tenant-123"},
            limit=10,
            sort={"created_at": -1},
            projection={"preferences": 1, "settings": 1}
        )
        logger.info(f"Query result: {query_result}")

    except ZeroDBError as e:
        logger.error(f"NoSQL operation error: {e}")


async def example_tenant_isolation():
    """Example: Multi-tenant isolation"""
    logger.info("=== Multi-Tenant Isolation Example ===")

    service = ZeroDBService.get_instance()

    try:
        # Tenant 1: Store documents
        tenant1_docs = ["Tenant 1 document A", "Tenant 1 document B"]
        logger.info("Storing documents for Tenant 1...")
        tenant1_ids = await service.embed_and_store(
            texts=tenant1_docs,
            namespace="tenant-1",
            metadata={"tenant_id": "tenant-1", "source": "tenant1_db"}
        )
        logger.info(f"Tenant 1 stored {len(tenant1_ids)} vectors")

        # Tenant 2: Store documents
        tenant2_docs = ["Tenant 2 document X", "Tenant 2 document Y"]
        logger.info("Storing documents for Tenant 2...")
        tenant2_ids = await service.embed_and_store(
            texts=tenant2_docs,
            namespace="tenant-2",
            metadata={"tenant_id": "tenant-2", "source": "tenant2_db"}
        )
        logger.info(f"Tenant 2 stored {len(tenant2_ids)} vectors")

        # Search within Tenant 1 namespace only
        logger.info("Searching within Tenant 1 namespace...")
        results = await service.semantic_search(
            query_text="document",
            namespace="tenant-1",  # Only searches tenant-1 data
            limit=10
        )
        logger.info(f"Tenant 1 search found {len(results)} results")
        for result in results:
            logger.info(f"  - {result.get('document', 'N/A')}")

        # Search within Tenant 2 namespace only
        logger.info("Searching within Tenant 2 namespace...")
        results = await service.semantic_search(
            query_text="document",
            namespace="tenant-2",  # Only searches tenant-2 data
            limit=10
        )
        logger.info(f"Tenant 2 search found {len(results)} results")
        for result in results:
            logger.info(f"  - {result.get('document', 'N/A')}")

    except ZeroDBError as e:
        logger.error(f"Tenant isolation error: {e}")


async def main():
    """Run all examples"""
    logger.info("Starting ZeroDB Service Integration Examples")
    logger.info("=" * 60)

    # Run examples
    await example_postgresql_operations()
    print()

    await example_vector_operations()
    print()

    await example_embed_and_store()
    print()

    await example_nosql_operations()
    print()

    await example_tenant_isolation()
    print()

    logger.info("=" * 60)
    logger.info("Examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
