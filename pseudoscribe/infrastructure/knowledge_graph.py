"""Knowledge Graph Implementation using ZeroDB

This module provides a ZeroDB-backed knowledge graph for managing
relationships between documents in an Obsidian vault. It supports:
- Parsing markdown links and relationships
- Storing documents with vector embeddings
- Semantic search for related content
- Cross-reference suggestions

Author: PseudoScribe Team
Date: 2025-12-30
"""

import re
import logging
from typing import Dict, List, Set, Optional, Any
from pathlib import Path

from pseudoscribe.infrastructure.zerodb_service import ZeroDBService

logger = logging.getLogger(__name__)


def parse_markdown_links(content: str) -> Set[str]:
    """Parse wiki-style and markdown links from content

    Extracts both [[wiki links]] and [text](link.md) style links,
    filtering out external URLs.

    Args:
        content: Markdown content to parse

    Returns:
        Set of link targets found in the content

    Example:
        >>> content = "See [[Note 1]] and [guide](./guide.md)"
        >>> links = parse_markdown_links(content)
        >>> "Note 1" in links
        True
    """
    links = set()

    # Extract wiki-style links [[link]] or [[link|alias]]
    wiki_pattern = r'\[\[(.*?)(?:\|.*?)?\]\]'
    wiki_links = re.findall(wiki_pattern, content)
    links.update(wiki_links)

    # Extract markdown-style links [text](link)
    # Filter out HTTP/HTTPS links
    markdown_pattern = r'\[.*?\]\(((?!https?://)[^)]+)\)'
    markdown_links = re.findall(markdown_pattern, content)

    # Clean up markdown links (remove .md extension, handle relative paths)
    for link in markdown_links:
        link = link.strip()
        # Remove leading ./
        if link.startswith('./'):
            link = link[2:]
        # Keep the link even with .md extension
        links.add(link)

    # Clean up .md extensions if present
    cleaned_links = set()
    for link in links:
        if link.endswith('.md'):
            link = link[:-3]
        cleaned_links.add(link)

    return cleaned_links


class KnowledgeGraph:
    """ZeroDB-backed knowledge graph for document relationships

    Manages a graph of documents with semantic embeddings and
    explicit link relationships stored in ZeroDB.

    Attributes:
        tenant_id: Tenant identifier for multi-tenant isolation
        namespace: Namespace for organizing vectors (includes tenant_id)
        zerodb: ZeroDB service instance
        embedding_model: Model used for generating embeddings

    Example:
        >>> kg = KnowledgeGraph(tenant_id="my-tenant")
        >>> await kg.store_document(
        ...     doc_path="notes/idea.md",
        ...     content="# My Idea\\n\\nSee [[Related]]",
        ...     links={"Related"},
        ...     metadata={"title": "My Idea"}
        ... )
        'vec_12345'
    """

    def __init__(
        self,
        tenant_id: str,
        namespace: Optional[str] = None,
        embedding_model: str = "BAAI/bge-small-en-v1.5"
    ):
        """Initialize knowledge graph

        Args:
            tenant_id: Tenant identifier for isolation
            namespace: Custom namespace (defaults to kg-{tenant_id})
            embedding_model: Model for embedding generation
        """
        self.tenant_id = tenant_id
        self.namespace = namespace or f"kg-{tenant_id}"
        self.embedding_model = embedding_model
        self.zerodb = ZeroDBService.get_instance()

        logger.info(
            f"Initialized KnowledgeGraph for tenant={tenant_id}, "
            f"namespace={self.namespace}"
        )

    async def store_document(
        self,
        doc_path: str,
        content: str,
        links: Set[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store document with embeddings and metadata

        Generates embeddings for the document content and stores
        it in ZeroDB with metadata including path, links, and tenant.

        Args:
            doc_path: Path to the document (relative to vault)
            content: Document content (markdown)
            links: Set of link targets from the document
            metadata: Additional metadata (title, tags, etc.)

        Returns:
            Vector ID of the stored document

        Raises:
            ZeroDBError: If storage fails
        """
        logger.debug(f"Storing document: {doc_path}")

        # Generate embedding for content
        embeddings = await self.zerodb.generate_embeddings(
            texts=[content],
            model=self.embedding_model
        )

        if not embeddings or len(embeddings) == 0:
            raise ValueError(f"Failed to generate embedding for {doc_path}")

        embedding = embeddings[0]

        # Prepare metadata
        doc_metadata = {
            "doc_path": doc_path,
            "tenant_id": self.tenant_id,
            "links": list(links),  # Convert set to list for JSON
            **(metadata or {})
        }

        # Store vector with metadata
        vector_id = await self.zerodb.upsert_vector(
            vector=embedding,
            document=content,
            metadata=doc_metadata,
            namespace=self.namespace
        )

        logger.info(f"Stored document {doc_path} with vector_id={vector_id}")
        return vector_id

    async def find_related(
        self,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find semantically related documents

        Uses semantic search to find documents similar to the query text.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of related documents with metadata and scores

        Example:
            >>> results = await kg.find_related("machine learning", limit=5)
            >>> results[0]["title"]
            'Introduction to ML'
        """
        logger.debug(f"Finding related documents for query: {query_text[:50]}...")

        # Perform semantic search
        results = await self.zerodb.semantic_search(
            query_text=query_text,
            limit=limit,
            namespace=self.namespace,
            threshold=threshold,
            model=self.embedding_model
        )

        # Extract and format results
        formatted_results = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted_results.append({
                "vector_id": result.get("vector_id"),
                "score": result.get("score", 0.0),
                "doc_path": metadata.get("doc_path", ""),
                "title": metadata.get("title", ""),
                "links": metadata.get("links", []),
                "metadata": metadata
            })

        logger.info(f"Found {len(formatted_results)} related documents")
        return formatted_results

    async def suggest_references(
        self,
        content: str,
        current_doc_path: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """Suggest relevant cross-references for content

        Finds semantically similar documents that could be referenced,
        excluding the current document.

        Args:
            content: Content to find references for
            current_doc_path: Path of current document (to exclude from results)
            limit: Maximum number of suggestions
            threshold: Minimum similarity score

        Returns:
            List of suggested documents with relevance scores

        Example:
            >>> suggestions = await kg.suggest_references(
            ...     "Writing about neural networks",
            ...     current_doc_path="ml/my-note.md"
            ... )
            >>> suggestions[0]["title"]
            'Neural Network Basics'
        """
        logger.debug(f"Suggesting references for content (len={len(content)})")

        # Find related documents
        results = await self.find_related(
            query_text=content,
            limit=limit + 1,  # Get extra in case we need to filter current doc
            threshold=threshold
        )

        # Filter out current document if specified
        suggestions = []
        for result in results:
            if current_doc_path and result["doc_path"] == current_doc_path:
                continue
            suggestions.append(result)

        # Limit to requested number
        suggestions = suggestions[:limit]

        logger.info(
            f"Generated {len(suggestions)} reference suggestions "
            f"(excluded current: {current_doc_path})"
        )
        return suggestions

    async def build_graph_from_vault(
        self,
        vault_sync
    ) -> Dict[str, Dict[str, Any]]:
        """Build knowledge graph from entire vault

        Scans all documents in the vault, extracts links, generates
        embeddings, and stores everything in ZeroDB.

        Args:
            vault_sync: VaultSync instance for the vault

        Returns:
            Dictionary mapping doc paths to metadata

        Example:
            >>> from pseudoscribe.infrastructure.vault_sync import VaultSync
            >>> vault = VaultSync("/path/to/vault")
            >>> graph_data = await kg.build_graph_from_vault(vault)
            >>> len(graph_data)
            42
        """
        logger.info(f"Building graph from vault: {vault_sync.vault_path}")

        # Scan vault for all markdown files
        files = await vault_sync.scan_vault()
        graph_data = {}

        # Process each file
        for file_path in files:
            try:
                # Read content
                content = await vault_sync.read_note(file_path)

                # Extract links
                links = parse_markdown_links(content)

                # Extract title from first heading or use filename
                title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else Path(file_path).stem

                # Get relative path
                relative_path = str(Path(file_path).relative_to(vault_sync.vault_path))

                # Store document
                vector_id = await self.store_document(
                    doc_path=relative_path,
                    content=content,
                    links=links,
                    metadata={"title": title}
                )

                # Track in graph data
                graph_data[relative_path] = {
                    "vector_id": vector_id,
                    "title": title,
                    "links": list(links),
                    "path": relative_path
                }

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        logger.info(f"Built graph with {len(graph_data)} documents")
        return graph_data

    async def sync_vault_changes(
        self,
        vault_sync
    ) -> Dict[str, List[str]]:
        """Sync vault changes to knowledge graph

        Detects added, modified, and deleted documents and updates
        the knowledge graph accordingly.

        Args:
            vault_sync: VaultSync instance for the vault

        Returns:
            Dictionary with lists of added, modified, and deleted files

        Example:
            >>> changes = await kg.sync_vault_changes(vault)
            >>> changes["added"]
            ['notes/new-idea.md']
        """
        logger.info("Syncing vault changes to knowledge graph")

        # Get changes from vault
        changes = await vault_sync.sync_changes()

        # Process added files
        for relative_path in changes["added"]:
            try:
                file_path = str(Path(vault_sync.vault_path) / relative_path)
                content = await vault_sync.read_note(file_path)
                links = parse_markdown_links(content)

                # Extract title
                title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else Path(relative_path).stem

                # Store new document
                await self.store_document(
                    doc_path=relative_path,
                    content=content,
                    links=links,
                    metadata={"title": title}
                )
                logger.debug(f"Added document to graph: {relative_path}")

            except Exception as e:
                logger.error(f"Error adding {relative_path}: {e}")

        # Process modified files
        for relative_path in changes["modified"]:
            try:
                file_path = str(Path(vault_sync.vault_path) / relative_path)
                content = await vault_sync.read_note(file_path)
                links = parse_markdown_links(content)

                # Extract title
                title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else Path(relative_path).stem

                # Update document (upsert will replace)
                await self.store_document(
                    doc_path=relative_path,
                    content=content,
                    links=links,
                    metadata={"title": title}
                )
                logger.debug(f"Updated document in graph: {relative_path}")

            except Exception as e:
                logger.error(f"Error updating {relative_path}: {e}")

        # Note: Deleted files remain in ZeroDB for now
        # Could implement deletion via delete_vector in future
        if changes["deleted"]:
            logger.info(f"Tracked {len(changes['deleted'])} deleted files")

        logger.info(
            f"Sync complete: {len(changes['added'])} added, "
            f"{len(changes['modified'])} modified, "
            f"{len(changes['deleted'])} deleted"
        )

        return changes
