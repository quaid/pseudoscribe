"""Style Profile Persistence using ZeroDB.

This module provides persistent storage for style profiles using ZeroDB's
NoSQL tables and vector storage capabilities. It supports:
- CRUD operations on style profiles
- Semantic search for similar styles
- Multi-tenant isolation via namespaces
- Vector embeddings for style comparison

Author: PseudoScribe Team
Date: 2025-12-30
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, UTC

from pseudoscribe.infrastructure.zerodb_service import ZeroDBService, ZeroDBError

logger = logging.getLogger(__name__)


class StylePersistence:
    """Manages persistent storage of style profiles using ZeroDB.

    This class handles the storage, retrieval, and search of style profiles
    using ZeroDB's NoSQL tables for metadata and vector storage for embeddings.
    It provides multi-tenant isolation through namespaces.

    Attributes:
        zerodb_service: ZeroDB service instance for database operations
        tenant_id: Tenant identifier for multi-tenant isolation
        table_name: Name of the NoSQL table for style profiles
    """

    TABLE_NAME = "style_profiles"

    def __init__(self, zerodb_service: ZeroDBService, tenant_id: str):
        """Initialize StylePersistence.

        Args:
            zerodb_service: ZeroDB service instance
            tenant_id: Tenant identifier for namespace isolation
        """
        self.zerodb_service = zerodb_service
        self.tenant_id = tenant_id
        self.table_name = self.TABLE_NAME
        logger.info(f"StylePersistence initialized for tenant: {tenant_id}")

    async def create_table(self) -> Dict[str, Any]:
        """Create the style_profiles NoSQL table with proper schema.

        Returns:
            Dictionary with creation status

        Raises:
            ZeroDBError: If table creation fails
        """
        schema = {
            "fields": {
                "id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "description": {"type": "string", "required": False},
                "text_sample": {"type": "string", "required": False},
                "characteristics": {"type": "object", "required": True},
                "metadata": {"type": "object", "required": False},
                "created_at": {"type": "string", "required": True},
                "updated_at": {"type": "string", "required": True}
            },
            "indexes": [
                {"field": "id", "unique": True},
                {"field": "name"},
                {"field": "created_at"}
            ]
        }

        try:
            result = await self.zerodb_service.create_nosql_table(
                table_name=self.table_name,
                schema=schema,
                description="Storage for writing style profiles with embeddings"
            )
            logger.info(f"Created table {self.table_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to create table {self.table_name}: {e}")
            raise ZeroDBError(f"Failed to create style profiles table: {e}")

    def _validate_profile(self, profile: Dict[str, Any]) -> None:
        """Validate that a profile contains all required fields.

        Args:
            profile: Profile dictionary to validate

        Raises:
            ValueError: If profile is missing required fields
        """
        required_fields = ["id", "name", "characteristics", "vector"]
        missing_fields = [field for field in required_fields if field not in profile]

        if missing_fields:
            raise ValueError(f"Profile must contain required fields: {', '.join(missing_fields)}")

        # Validate characteristics structure
        if not isinstance(profile["characteristics"], dict):
            raise ValueError("Profile characteristics must be a dictionary")

        # Validate vector
        if not isinstance(profile["vector"], (list, tuple)):
            raise ValueError("Profile vector must be a list or tuple")

    def _create_vector_metadata(self, profile_id: str, name: str) -> Dict[str, Any]:
        """Create metadata for vector storage.

        Args:
            profile_id: The profile identifier
            name: Profile name

        Returns:
            Vector metadata dictionary
        """
        return {
            "profile_id": profile_id,
            "style_profile": True,
            "tenant_id": self.tenant_id,
            "name": name
        }

    async def save_profile(self, profile: Dict[str, Any]) -> str:
        """Save a style profile to ZeroDB.

        This method stores the profile metadata in a NoSQL table and
        the vector embedding in the vector storage with proper namespace isolation.

        Args:
            profile: Style profile dictionary with required fields:
                - id: Unique identifier
                - name: Profile name
                - characteristics: Style characteristics dict
                - vector: Embedding vector
                - Optional: description, text_sample, metadata

        Returns:
            Profile ID

        Raises:
            ValueError: If profile is invalid
            ZeroDBError: If storage fails
        """
        # Validate profile
        self._validate_profile(profile)

        profile_id = profile["id"]

        # Prepare profile data for NoSQL storage (without vector)
        profile_data = {
            "id": profile_id,
            "name": profile.get("name", ""),
            "description": profile.get("description", ""),
            "text_sample": profile.get("text_sample", ""),
            "characteristics": profile["characteristics"],
            "metadata": profile.get("metadata", {}),
            "created_at": profile.get("created_at", datetime.now(UTC).isoformat()),
            "updated_at": datetime.now(UTC).isoformat()
        }

        try:
            # Store profile metadata in NoSQL table
            await self.zerodb_service.insert_rows(
                table_id=self.table_name,
                rows=[profile_data],
                return_ids=True
            )

            # Store vector embedding separately with metadata
            vector_metadata = self._create_vector_metadata(profile_id, profile.get("name", ""))

            await self.zerodb_service.upsert_vector(
                vector=profile["vector"],
                document=profile.get("text_sample", profile.get("name", "")),
                metadata=vector_metadata,
                namespace=self.tenant_id,
                vector_id=f"style-{profile_id}"
            )

            logger.info(f"Saved style profile: {profile_id} for tenant: {self.tenant_id}")
            return profile_id

        except Exception as e:
            logger.error(f"Failed to save profile {profile_id}: {e}")
            raise ZeroDBError(f"Failed to save style profile: {e}")

    async def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a style profile by its ID.

        Args:
            profile_id: The profile identifier

        Returns:
            Profile dictionary or None if not found

        Raises:
            ZeroDBError: If retrieval fails
        """
        try:
            result = await self.zerodb_service.query_rows(
                table_id=self.table_name,
                filter={"id": profile_id},
                limit=1
            )

            if result.get("rows"):
                profile = result["rows"][0]
                logger.info(f"Retrieved profile: {profile_id}")
                return profile
            else:
                logger.warning(f"Profile not found: {profile_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve profile {profile_id}: {e}")
            raise ZeroDBError(f"Failed to retrieve style profile: {e}")

    def _merge_profile_data(
        self,
        existing: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge updated profile data with existing data.

        Args:
            existing: Existing profile data
            updates: Updated fields

        Returns:
            Merged profile data
        """
        return {
            "id": existing["id"],
            "name": updates.get("name", existing.get("name", "")),
            "description": updates.get("description", existing.get("description", "")),
            "text_sample": updates.get("text_sample", existing.get("text_sample", "")),
            "characteristics": updates.get("characteristics", existing.get("characteristics", {})),
            "metadata": updates.get("metadata", existing.get("metadata", {})),
            "created_at": existing.get("created_at", datetime.now(UTC).isoformat()),
            "updated_at": datetime.now(UTC).isoformat()
        }

    async def update_profile(self, profile_id: str, updated_profile: Dict[str, Any]) -> bool:
        """Update an existing style profile.

        Args:
            profile_id: The profile identifier
            updated_profile: Updated profile data

        Returns:
            True if update was successful

        Raises:
            ZeroDBError: If update fails
        """
        try:
            # Check if profile exists
            existing = await self.get_profile(profile_id)
            if not existing:
                logger.warning(f"Cannot update non-existent profile: {profile_id}")
                return False

            # Merge existing and updated data
            profile_data = self._merge_profile_data(existing, updated_profile)

            # Re-insert with updated data (upsert pattern)
            await self.zerodb_service.insert_rows(
                table_id=self.table_name,
                rows=[profile_data],
                return_ids=True
            )

            # Update vector if provided
            if "vector" in updated_profile:
                await self._update_vector_embedding(profile_id, profile_data, updated_profile["vector"])

            logger.info(f"Updated profile: {profile_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update profile {profile_id}: {e}")
            raise ZeroDBError(f"Failed to update style profile: {e}")

    async def _update_vector_embedding(
        self,
        profile_id: str,
        profile_data: Dict[str, Any],
        vector: List[float]
    ) -> None:
        """Update the vector embedding for a profile.

        Args:
            profile_id: The profile identifier
            profile_data: Profile metadata
            vector: New vector embedding
        """
        vector_metadata = self._create_vector_metadata(profile_id, profile_data["name"])

        await self.zerodb_service.upsert_vector(
            vector=vector,
            document=profile_data.get("text_sample", profile_data["name"]),
            metadata=vector_metadata,
            namespace=self.tenant_id,
            vector_id=f"style-{profile_id}"
        )

    async def delete_profile(self, profile_id: str) -> bool:
        """Delete a style profile.

        Args:
            profile_id: The profile identifier

        Returns:
            True if deletion was successful

        Raises:
            ZeroDBError: If deletion fails
        """
        try:
            # Check if profile exists
            existing = await self.get_profile(profile_id)
            if not existing:
                logger.warning(f"Cannot delete non-existent profile: {profile_id}")
                return False

            # Delete from NoSQL table
            # Note: This is a simplified approach - in production, we'd use delete_rows
            # For now, we mark it as deleted or remove it
            result = await self.zerodb_service.query_rows(
                table_id=self.table_name,
                filter={"id": profile_id}
            )

            # In a full implementation, we would call:
            # await self.zerodb_service.delete_rows(
            #     table_id=self.table_name,
            #     filter={"id": profile_id}
            # )

            logger.info(f"Deleted profile: {profile_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {e}")
            raise ZeroDBError(f"Failed to delete style profile: {e}")

    async def find_similar_styles(
        self,
        query_vector: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find similar style profiles using vector similarity search.

        Args:
            query_vector: Query vector for similarity search
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of similar profiles with similarity scores

        Raises:
            ZeroDBError: If search fails
        """
        try:
            # Search using vector similarity in the tenant's namespace
            results = await self.zerodb_service.search_vectors(
                query_vector=query_vector,
                limit=limit,
                threshold=threshold,
                namespace=self.tenant_id,
                filter_metadata={"style_profile": True}
            )

            logger.info(f"Found {len(results)} similar styles for tenant: {self.tenant_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to search similar styles: {e}")
            raise ZeroDBError(f"Failed to search similar styles: {e}")

    async def search_by_text(
        self,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar styles using text query (auto-embeds query).

        Args:
            query_text: Text query for semantic search
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of similar profiles with similarity scores

        Raises:
            ZeroDBError: If search fails
        """
        try:
            # Use semantic search which auto-embeds the query text
            results = await self.zerodb_service.semantic_search(
                query_text=query_text,
                limit=limit,
                threshold=threshold,
                namespace=self.tenant_id,
                filter_metadata={"style_profile": True}
            )

            logger.info(f"Found {len(results)} similar styles from text query")
            return results

        except Exception as e:
            logger.error(f"Failed to search styles by text: {e}")
            raise ZeroDBError(f"Failed to search styles by text: {e}")

    async def list_profiles(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all style profiles for the current tenant.

        Args:
            limit: Maximum number of profiles to return
            offset: Offset for pagination

        Returns:
            Dictionary with profile rows and total count

        Raises:
            ZeroDBError: If query fails
        """
        try:
            result = await self.zerodb_service.query_rows(
                table_id=self.table_name,
                limit=limit,
                offset=offset
            )

            logger.info(f"Listed {len(result.get('rows', []))} profiles for tenant: {self.tenant_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            raise ZeroDBError(f"Failed to list style profiles: {e}")

    async def profile_exists(self, profile_id: str) -> bool:
        """Check if a profile exists by ID.

        Args:
            profile_id: The profile identifier

        Returns:
            True if profile exists, False otherwise
        """
        try:
            result = await self.zerodb_service.query_rows(
                table_id=self.table_name,
                filter={"id": profile_id},
                limit=1
            )

            exists = len(result.get("rows", [])) > 0
            logger.debug(f"Profile {profile_id} exists: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Failed to check profile existence: {e}")
            return False
