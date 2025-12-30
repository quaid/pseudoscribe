"""Test suite for StylePersistence class.

This module tests the persistent storage of style profiles using ZeroDB,
ensuring proper CRUD operations, semantic search, and tenant isolation.

Following TDD workflow: Red (failing tests) -> Green (minimal implementation) -> Refactor
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
import uuid

from pseudoscribe.infrastructure.style_persistence import StylePersistence
from pseudoscribe.infrastructure.zerodb_service import ZeroDBService


class TestStylePersistence:
    """Test suite for StylePersistence class."""

    @pytest.fixture
    def mock_zerodb_service(self):
        """Create a mock ZeroDB service for testing."""
        service = MagicMock(spec=ZeroDBService)
        service.create_nosql_table = AsyncMock(return_value={"success": True, "table_id": "style_profiles"})
        service.insert_rows = AsyncMock(return_value={"row_ids": ["row-123"]})
        service.query_rows = AsyncMock(return_value={"rows": []})
        service.upsert_vector = AsyncMock(return_value="vector-123")
        service.search_vectors = AsyncMock(return_value=[])
        service.semantic_search = AsyncMock(return_value=[])
        service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3] * 128])  # 384-dim vector
        return service

    @pytest.fixture
    def style_persistence(self, mock_zerodb_service):
        """Create a StylePersistence instance for testing."""
        return StylePersistence(zerodb_service=mock_zerodb_service, tenant_id="test-tenant")

    @pytest.fixture
    def sample_profile(self):
        """Create a sample style profile for testing."""
        return {
            "id": str(uuid.uuid4()),
            "name": "Academic Writing Style",
            "description": "Formal academic writing with technical language",
            "text_sample": "The methodology employed in this study demonstrates rigorous empirical analysis.",
            "characteristics": {
                "complexity": 0.8,
                "formality": 0.9,
                "tone": 0.5,
                "readability": 0.6
            },
            "vector": np.random.rand(384).tolist(),
            "metadata": {
                "author": "test-user",
                "domain": "academic",
                "language": "en"
            },
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat()
        }

    # RED Phase Test 1: Table creation
    @pytest.mark.asyncio
    async def test_create_table_schema(self, style_persistence, mock_zerodb_service):
        """Test creating the style_profiles NoSQL table with proper schema."""
        # Act
        result = await style_persistence.create_table()

        # Assert
        assert result["success"] is True
        mock_zerodb_service.create_nosql_table.assert_called_once()

        # Verify schema structure
        call_args = mock_zerodb_service.create_nosql_table.call_args
        assert call_args.kwargs["table_name"] == "style_profiles"
        schema = call_args.kwargs["schema"]

        # Verify required fields in schema
        assert "fields" in schema
        fields = schema["fields"]
        assert "id" in fields
        assert "name" in fields
        assert "description" in fields
        assert "text_sample" in fields
        assert "characteristics" in fields
        assert "metadata" in fields
        assert "created_at" in fields
        assert "updated_at" in fields

    # RED Phase Test 2: Store profile with metadata and embedding
    @pytest.mark.asyncio
    async def test_save_profile_stores_data_and_embedding(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test storing a profile with metadata and vector embedding in ZeroDB."""
        # Act
        profile_id = await style_persistence.save_profile(sample_profile)

        # Assert
        assert profile_id is not None

        # Verify NoSQL table insert was called
        mock_zerodb_service.insert_rows.assert_called_once()
        insert_call = mock_zerodb_service.insert_rows.call_args
        assert insert_call.kwargs["table_id"] == "style_profiles"

        # Verify profile data structure
        rows = insert_call.kwargs["rows"]
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == sample_profile["id"]
        assert row["name"] == sample_profile["name"]
        assert row["characteristics"] == sample_profile["characteristics"]

        # Verify vector was stored separately
        mock_zerodb_service.upsert_vector.assert_called_once()
        vector_call = mock_zerodb_service.upsert_vector.call_args
        assert vector_call.kwargs["namespace"] == "test-tenant"
        assert "style_profile" in vector_call.kwargs["metadata"]

    # RED Phase Test 3: Retrieve profile by ID
    @pytest.mark.asyncio
    async def test_get_profile_by_id(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test retrieving a style profile by its ID."""
        # Arrange
        mock_zerodb_service.query_rows.return_value = {
            "rows": [sample_profile]
        }

        # Act
        profile = await style_persistence.get_profile(sample_profile["id"])

        # Assert
        assert profile is not None
        assert profile["id"] == sample_profile["id"]
        assert profile["name"] == sample_profile["name"]
        assert profile["characteristics"] == sample_profile["characteristics"]

        # Verify query was called correctly
        mock_zerodb_service.query_rows.assert_called_once()
        query_call = mock_zerodb_service.query_rows.call_args
        assert query_call.kwargs["table_id"] == "style_profiles"
        assert query_call.kwargs["filter"]["id"] == sample_profile["id"]

    # RED Phase Test 4: Semantic search for similar styles
    @pytest.mark.asyncio
    async def test_find_similar_styles_semantic_search(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test finding similar style profiles using semantic search."""
        # Arrange
        query_vector = np.random.rand(384).tolist()
        similar_profiles = [
            {
                "id": "profile-1",
                "name": "Similar Academic Style",
                "score": 0.92,
                "document": sample_profile["text_sample"]
            },
            {
                "id": "profile-2",
                "name": "Technical Writing",
                "score": 0.85,
                "document": "Technical specifications require precise terminology."
            }
        ]
        mock_zerodb_service.search_vectors.return_value = similar_profiles

        # Act
        results = await style_persistence.find_similar_styles(query_vector, limit=5, threshold=0.7)

        # Assert
        assert len(results) == 2
        assert results[0]["score"] >= 0.7
        assert results[1]["score"] >= 0.7

        # Verify search was called with correct parameters
        mock_zerodb_service.search_vectors.assert_called_once()
        search_call = mock_zerodb_service.search_vectors.call_args
        assert search_call.kwargs["query_vector"] == query_vector
        assert search_call.kwargs["limit"] == 5
        assert search_call.kwargs["threshold"] == 0.7
        assert search_call.kwargs["namespace"] == "test-tenant"

    # RED Phase Test 5: Update profile
    @pytest.mark.asyncio
    async def test_update_profile(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test updating an existing style profile."""
        # Arrange
        updated_profile = sample_profile.copy()
        updated_profile["name"] = "Updated Academic Style"
        updated_profile["characteristics"]["complexity"] = 0.9

        mock_zerodb_service.query_rows.return_value = {
            "rows": [sample_profile]
        }

        # Act
        result = await style_persistence.update_profile(sample_profile["id"], updated_profile)

        # Assert
        assert result is True

        # Verify update was called on NoSQL table
        # Note: update_rows should be called, not insert_rows
        # This will be implemented in the GREEN phase

    # RED Phase Test 6: Delete profile
    @pytest.mark.asyncio
    async def test_delete_profile(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test deleting a style profile."""
        # Arrange
        mock_zerodb_service.query_rows.return_value = {
            "rows": [sample_profile]
        }

        # Act
        result = await style_persistence.delete_profile(sample_profile["id"])

        # Assert
        assert result is True

        # Verify deletion from NoSQL table
        # This will be verified when we implement the method

    # RED Phase Test 7: Tenant isolation via namespace
    @pytest.mark.asyncio
    async def test_tenant_isolation_with_namespace(self, mock_zerodb_service):
        """Test that tenant isolation works correctly via namespace."""
        # Arrange
        tenant1_persistence = StylePersistence(zerodb_service=mock_zerodb_service, tenant_id="tenant-1")
        tenant2_persistence = StylePersistence(zerodb_service=mock_zerodb_service, tenant_id="tenant-2")

        profile1 = {
            "id": str(uuid.uuid4()),
            "name": "Tenant 1 Style",
            "text_sample": "Sample text for tenant 1",
            "characteristics": {"complexity": 0.5, "formality": 0.5, "tone": 0.5, "readability": 0.5},
            "vector": np.random.rand(384).tolist(),
            "metadata": {}
        }

        # Act
        await tenant1_persistence.save_profile(profile1)

        # Verify first call used tenant-1 namespace
        first_call = mock_zerodb_service.upsert_vector.call_args
        assert first_call.kwargs["namespace"] == "tenant-1"

        # Reset mock to verify next call
        mock_zerodb_service.upsert_vector.reset_mock()

        profile2 = profile1.copy()
        profile2["id"] = str(uuid.uuid4())
        profile2["name"] = "Tenant 2 Style"

        await tenant2_persistence.save_profile(profile2)

        # Assert - verify second call used tenant-2 namespace
        second_call = mock_zerodb_service.upsert_vector.call_args
        assert second_call.kwargs["namespace"] == "tenant-2"

    # RED Phase Test 8: List all profiles for a tenant
    @pytest.mark.asyncio
    async def test_list_profiles_for_tenant(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test listing all style profiles for a specific tenant."""
        # Arrange
        profiles = [
            sample_profile,
            {
                "id": str(uuid.uuid4()),
                "name": "Another Style",
                "characteristics": {"complexity": 0.4, "formality": 0.5, "tone": 0.6, "readability": 0.7}
            }
        ]
        mock_zerodb_service.query_rows.return_value = {
            "rows": profiles,
            "total": 2
        }

        # Act
        result = await style_persistence.list_profiles(limit=10, offset=0)

        # Assert
        assert len(result["rows"]) == 2
        assert result["total"] == 2

        # Verify query was called
        mock_zerodb_service.query_rows.assert_called_once()
        query_call = mock_zerodb_service.query_rows.call_args
        assert query_call.kwargs["table_id"] == "style_profiles"
        assert query_call.kwargs["limit"] == 10
        assert query_call.kwargs["offset"] == 0

    # RED Phase Test 9: Profile exists check
    @pytest.mark.asyncio
    async def test_profile_exists(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test checking if a profile exists by ID."""
        # Arrange - profile exists
        mock_zerodb_service.query_rows.return_value = {
            "rows": [sample_profile]
        }

        # Act
        exists = await style_persistence.profile_exists(sample_profile["id"])

        # Assert
        assert exists is True

        # Arrange - profile does not exist
        mock_zerodb_service.query_rows.return_value = {
            "rows": []
        }

        # Act
        exists = await style_persistence.profile_exists("non-existent-id")

        # Assert
        assert exists is False

    # RED Phase Test 10: Handle errors gracefully
    @pytest.mark.asyncio
    async def test_save_profile_handles_errors(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test that save_profile handles errors gracefully."""
        # Arrange - simulate database error
        from pseudoscribe.infrastructure.zerodb_service import ZeroDBError
        mock_zerodb_service.insert_rows.side_effect = ZeroDBError("Database connection failed")

        # Act & Assert
        with pytest.raises(ZeroDBError):
            await style_persistence.save_profile(sample_profile)

    # RED Phase Test 11: Validate profile before saving
    @pytest.mark.asyncio
    async def test_validate_profile_before_saving(self, style_persistence):
        """Test that profiles are validated before saving."""
        # Arrange - invalid profile missing required fields
        invalid_profile = {
            "id": str(uuid.uuid4()),
            "name": "Invalid Profile"
            # Missing characteristics, vector, etc.
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Profile must contain"):
            await style_persistence.save_profile(invalid_profile)

    # RED Phase Test 12: Search by text query (not just vector)
    @pytest.mark.asyncio
    async def test_semantic_search_by_text_query(self, style_persistence, mock_zerodb_service, sample_profile):
        """Test semantic search using text query instead of vector."""
        # Arrange
        query_text = "formal academic writing style"
        similar_profiles = [
            {
                "id": sample_profile["id"],
                "score": 0.88,
                "document": sample_profile["text_sample"]
            }
        ]
        mock_zerodb_service.semantic_search.return_value = similar_profiles

        # Act
        results = await style_persistence.search_by_text(query_text, limit=10)

        # Assert
        assert len(results) == 1
        assert results[0]["score"] > 0.7

        # Verify semantic search was called
        mock_zerodb_service.semantic_search.assert_called_once()
        search_call = mock_zerodb_service.semantic_search.call_args
        assert search_call.kwargs["query_text"] == query_text
        assert search_call.kwargs["namespace"] == "test-tenant"
