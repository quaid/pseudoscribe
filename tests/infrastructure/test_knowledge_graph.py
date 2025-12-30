"""
Tests for Knowledge Graph functionality

These tests verify the ZeroDB-backed knowledge graph implementation
for parsing Obsidian markdown files, extracting links and relationships,
and providing semantic search capabilities.

Following TDD methodology: Red -> Green -> Refactor
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Set, Any


class TestMarkdownLinkParsing:
    """Test parsing of markdown links and relationships"""

    @pytest.mark.asyncio
    async def test_parse_wiki_links(self):
        """
        Scenario: Parse wiki-style links from markdown
        Given a markdown document with [[wiki links]]
        When parsing the document
        Then all wiki links are extracted
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import parse_markdown_links

        content = """
        # My Note

        This links to [[Another Note]] and [[Yet Another Note|with alias]].
        Also see [[folder/Nested Note]].
        """

        # When
        links = parse_markdown_links(content)

        # Then
        assert "Another Note" in links
        assert "Yet Another Note" in links
        assert "folder/Nested Note" in links
        assert len(links) == 3

    @pytest.mark.asyncio
    async def test_parse_markdown_style_links(self):
        """
        Scenario: Parse markdown-style links
        Given a markdown document with [text](link) style links
        When parsing the document
        Then markdown links to .md files are extracted
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import parse_markdown_links

        content = """
        # Documentation

        See [the guide](./guides/tutorial.md) for more info.
        External link: [Google](https://google.com)
        """

        # When
        links = parse_markdown_links(content)

        # Then
        assert "./guides/tutorial.md" in links or "guides/tutorial.md" in links
        # External links should be filtered out
        assert "https://google.com" not in links

    @pytest.mark.asyncio
    async def test_parse_links_with_special_characters(self):
        """
        Scenario: Handle links with special characters
        Given markdown with links containing spaces and special chars
        When parsing the document
        Then links are correctly extracted
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import parse_markdown_links

        content = """
        Links to [[Project Ideas - 2024]] and [[Research/AI & ML]].
        """

        # When
        links = parse_markdown_links(content)

        # Then
        assert "Project Ideas - 2024" in links
        assert "Research/AI & ML" in links


class TestKnowledgeGraphStorage:
    """Test storing documents and relationships in ZeroDB"""

    @pytest.fixture
    def mock_zerodb_service(self):
        """Mock ZeroDBService for testing"""
        with patch('pseudoscribe.infrastructure.knowledge_graph.ZeroDBService') as mock:
            mock_instance = MagicMock()
            mock_instance.generate_embeddings = AsyncMock(return_value=[[0.1] * 384])
            mock_instance.upsert_vector = AsyncMock(return_value="vec_12345")
            mock_instance.semantic_search = AsyncMock(return_value=[])
            mock.get_instance.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_store_document_with_metadata(self, mock_zerodb_service):
        """
        Scenario: Store document with metadata in ZeroDB
        Given a document with title, content, and links
        When storing the document
        Then document is embedded and stored with metadata
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant", namespace="test-vault")

        doc_path = "notes/my-note.md"
        content = "# My Note\n\nSome content about [[Related Topic]]."
        links = {"Related Topic"}

        # When
        vector_id = await kg.store_document(
            doc_path=doc_path,
            content=content,
            links=links,
            metadata={"title": "My Note"}
        )

        # Then
        assert vector_id == "vec_12345"
        mock_zerodb_service.generate_embeddings.assert_called_once()
        mock_zerodb_service.upsert_vector.assert_called_once()

        # Verify metadata includes links and path
        call_args = mock_zerodb_service.upsert_vector.call_args
        metadata = call_args[0][2]  # Third argument is metadata
        assert "doc_path" in metadata
        assert "links" in metadata
        assert "tenant_id" in metadata

    @pytest.mark.asyncio
    async def test_store_document_generates_embedding(self, mock_zerodb_service):
        """
        Scenario: Generate embedding when storing document
        Given a document
        When storing the document
        Then content is embedded using the default model
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant")
        content = "Test content for embedding"

        # When
        await kg.store_document(
            doc_path="test.md",
            content=content,
            links=set(),
            metadata={}
        )

        # Then
        mock_zerodb_service.generate_embeddings.assert_called_once()
        call_args = mock_zerodb_service.generate_embeddings.call_args
        assert content in call_args[0][0]  # First arg is texts list

    @pytest.mark.asyncio
    async def test_store_document_tenant_isolation(self, mock_zerodb_service):
        """
        Scenario: Ensure tenant isolation when storing documents
        Given a tenant_id
        When storing documents
        Then namespace includes tenant_id for isolation
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        tenant_id = "tenant-123"
        kg = KnowledgeGraph(tenant_id=tenant_id)

        # When
        await kg.store_document(
            doc_path="test.md",
            content="Content",
            links=set(),
            metadata={}
        )

        # Then
        call_args = mock_zerodb_service.upsert_vector.call_args
        namespace = call_args[1].get("namespace")  # Get namespace from kwargs
        assert tenant_id in namespace


class TestSemanticSearch:
    """Test semantic search for related content"""

    @pytest.fixture
    def mock_zerodb_service(self):
        """Mock ZeroDBService with search results"""
        with patch('pseudoscribe.infrastructure.knowledge_graph.ZeroDBService') as mock:
            mock_instance = MagicMock()
            mock_instance.semantic_search = AsyncMock(return_value=[
                {
                    "vector_id": "vec_1",
                    "score": 0.92,
                    "document": "# Related Doc 1\n\nContent about topic",
                    "metadata": {
                        "doc_path": "notes/related1.md",
                        "links": ["Topic A", "Topic B"],
                        "title": "Related Doc 1"
                    }
                },
                {
                    "vector_id": "vec_2",
                    "score": 0.85,
                    "document": "# Related Doc 2\n\nMore content",
                    "metadata": {
                        "doc_path": "notes/related2.md",
                        "links": ["Topic B"],
                        "title": "Related Doc 2"
                    }
                }
            ])
            mock.get_instance.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_find_related_by_content(self, mock_zerodb_service):
        """
        Scenario: Find related documents by semantic similarity
        Given a query text
        When searching for related documents
        Then semantically similar documents are returned
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant")
        query_text = "machine learning algorithms"

        # When
        results = await kg.find_related(query_text, limit=5)

        # Then
        assert len(results) == 2
        assert results[0]["score"] == 0.92
        assert results[0]["doc_path"] == "notes/related1.md"
        mock_zerodb_service.semantic_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_related_with_threshold(self, mock_zerodb_service):
        """
        Scenario: Filter results by similarity threshold
        Given a similarity threshold
        When searching for related documents
        Then only documents above threshold are returned
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant")

        # When
        results = await kg.find_related("test query", threshold=0.9, limit=10)

        # Then
        mock_zerodb_service.semantic_search.assert_called_once()
        call_kwargs = mock_zerodb_service.semantic_search.call_args.kwargs
        assert call_kwargs["threshold"] == 0.9

    @pytest.mark.asyncio
    async def test_find_related_returns_metadata(self, mock_zerodb_service):
        """
        Scenario: Return document metadata with search results
        Given a search query
        When finding related documents
        Then results include path, title, and links
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant")

        # When
        results = await kg.find_related("test query")

        # Then
        for result in results:
            assert "doc_path" in result
            assert "title" in result
            assert "links" in result
            assert "score" in result


class TestCrossReferenceSuggestions:
    """Test suggesting cross-references based on content"""

    @pytest.fixture
    def mock_zerodb_service(self):
        """Mock ZeroDBService for cross-reference suggestions"""
        with patch('pseudoscribe.infrastructure.knowledge_graph.ZeroDBService') as mock:
            mock_instance = MagicMock()
            mock_instance.semantic_search = AsyncMock(return_value=[
                {
                    "vector_id": "vec_1",
                    "score": 0.88,
                    "document": "# Machine Learning Basics\n\nIntroduction to ML",
                    "metadata": {
                        "doc_path": "ml/basics.md",
                        "title": "Machine Learning Basics",
                        "links": []
                    }
                },
                {
                    "vector_id": "vec_2",
                    "score": 0.82,
                    "document": "# Neural Networks\n\nDeep learning concepts",
                    "metadata": {
                        "doc_path": "ml/neural-nets.md",
                        "title": "Neural Networks",
                        "links": ["Machine Learning Basics"]
                    }
                }
            ])
            mock.get_instance.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_suggest_references_for_content(self, mock_zerodb_service):
        """
        Scenario: Suggest relevant references for content
        Given current document content
        When requesting suggestions
        Then relevant documents are suggested as references
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant")
        content = "I'm writing about deep learning and neural network architectures."

        # When
        suggestions = await kg.suggest_references(content, limit=3)

        # Then
        assert len(suggestions) == 2
        assert suggestions[0]["title"] == "Machine Learning Basics"
        assert "doc_path" in suggestions[0]

    @pytest.mark.asyncio
    async def test_suggest_references_excludes_current_doc(self, mock_zerodb_service):
        """
        Scenario: Exclude current document from suggestions
        Given current document path
        When requesting suggestions
        Then current document is not included in results
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        # Mock with current doc included
        mock_zerodb_service.semantic_search.return_value = [
            {
                "vector_id": "vec_current",
                "score": 1.0,
                "document": "Current doc",
                "metadata": {
                    "doc_path": "current.md",
                    "title": "Current Doc",
                    "links": []
                }
            },
            {
                "vector_id": "vec_1",
                "score": 0.88,
                "document": "Other doc",
                "metadata": {
                    "doc_path": "other.md",
                    "title": "Other Doc",
                    "links": []
                }
            }
        ]

        kg = KnowledgeGraph(tenant_id="test-tenant")
        content = "Test content"

        # When
        suggestions = await kg.suggest_references(
            content,
            current_doc_path="current.md",
            limit=5
        )

        # Then
        assert len(suggestions) == 1
        assert suggestions[0]["doc_path"] == "other.md"

    @pytest.mark.asyncio
    async def test_suggest_references_with_minimum_score(self, mock_zerodb_service):
        """
        Scenario: Only suggest high-quality references
        Given a minimum score threshold
        When requesting suggestions
        Then only suggestions above threshold are returned
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(tenant_id="test-tenant")

        # When
        suggestions = await kg.suggest_references(
            "test content",
            threshold=0.85,
            limit=10
        )

        # Then
        for suggestion in suggestions:
            assert suggestion["score"] >= 0.85


class TestGraphStructure:
    """Test building and maintaining graph structure"""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_zerodb_service(self):
        """Mock ZeroDBService for graph operations"""
        with patch('pseudoscribe.infrastructure.knowledge_graph.ZeroDBService') as mock:
            mock_instance = MagicMock()
            mock_instance.generate_embeddings = AsyncMock(
                side_effect=lambda texts, model: [[0.1] * 384 for _ in texts]
            )
            mock_instance.upsert_vector = AsyncMock(
                side_effect=lambda *args, **kwargs: f"vec_{hash(args[1])}"
            )
            mock.get_instance.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_build_graph_from_vault(self, temp_vault, mock_zerodb_service):
        """
        Scenario: Build knowledge graph from vault
        Given a vault with markdown files
        When building the graph
        Then all documents are stored with relationships
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph
        from pseudoscribe.infrastructure.vault_sync import VaultSync

        # Create test files
        os.makedirs(os.path.join(temp_vault, "notes"), exist_ok=True)

        with open(os.path.join(temp_vault, "notes", "doc1.md"), "w") as f:
            f.write("# Doc 1\n\nLinks to [[Doc 2]].")

        with open(os.path.join(temp_vault, "notes", "doc2.md"), "w") as f:
            f.write("# Doc 2\n\nContent here.")

        vault = VaultSync(vault_path=temp_vault)
        kg = KnowledgeGraph(tenant_id="test-tenant", namespace="test-vault")

        # When
        graph_data = await kg.build_graph_from_vault(vault)

        # Then
        assert len(graph_data) == 2
        assert mock_zerodb_service.upsert_vector.call_count == 2

    @pytest.mark.asyncio
    async def test_build_graph_extracts_relationships(self, temp_vault, mock_zerodb_service):
        """
        Scenario: Extract and store document relationships
        Given documents with wiki links
        When building the graph
        Then relationships are captured in metadata
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph
        from pseudoscribe.infrastructure.vault_sync import VaultSync

        # Create linked documents
        with open(os.path.join(temp_vault, "page1.md"), "w") as f:
            f.write("# Page 1\n\nSee [[Page 2]] and [[Page 3]].")

        vault = VaultSync(vault_path=temp_vault)
        kg = KnowledgeGraph(tenant_id="test-tenant")

        # When
        await kg.build_graph_from_vault(vault)

        # Then
        # Verify that upsert was called with link metadata
        calls = mock_zerodb_service.upsert_vector.call_args_list
        found_links = False
        for call in calls:
            metadata = call[0][2]  # Third positional argument
            if "links" in metadata and len(metadata["links"]) > 0:
                found_links = True
                assert "Page 2" in metadata["links"] or "Page 3" in metadata["links"]

        assert found_links, "Expected to find documents with links in metadata"


class TestVaultSyncIntegration:
    """Test integration with VaultSync for real-time updates"""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_zerodb_service(self):
        """Mock ZeroDBService"""
        with patch('pseudoscribe.infrastructure.knowledge_graph.ZeroDBService') as mock:
            mock_instance = MagicMock()
            mock_instance.generate_embeddings = AsyncMock(return_value=[[0.1] * 384])
            mock_instance.upsert_vector = AsyncMock(return_value="vec_123")
            mock.get_instance.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_sync_vault_updates_graph(self, temp_vault, mock_zerodb_service):
        """
        Scenario: Sync vault changes to knowledge graph
        Given a vault with changes
        When syncing the vault
        Then added/modified documents update the graph
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph
        from pseudoscribe.infrastructure.vault_sync import VaultSync

        vault = VaultSync(vault_path=temp_vault)
        kg = KnowledgeGraph(tenant_id="test-tenant")

        # Create initial file
        with open(os.path.join(temp_vault, "initial.md"), "w") as f:
            f.write("# Initial\n\nContent")

        # When
        result = await kg.sync_vault_changes(vault)

        # Then
        assert "added" in result
        assert "modified" in result
        assert len(result["added"]) > 0

    @pytest.mark.asyncio
    async def test_sync_handles_deleted_documents(self, temp_vault, mock_zerodb_service):
        """
        Scenario: Handle deleted documents during sync
        Given documents that were deleted
        When syncing the vault
        Then deleted documents are tracked
        """
        # Given
        from pseudoscribe.infrastructure.knowledge_graph import KnowledgeGraph
        from pseudoscribe.infrastructure.vault_sync import VaultSync

        vault = VaultSync(vault_path=temp_vault)
        kg = KnowledgeGraph(tenant_id="test-tenant")

        # Create and then delete a file
        test_file = os.path.join(temp_vault, "temp.md")
        with open(test_file, "w") as f:
            f.write("# Temp\n\nWill be deleted")

        await vault.read_note(test_file)  # Cache it
        os.remove(test_file)

        # When
        result = await kg.sync_vault_changes(vault)

        # Then
        assert "deleted" in result
