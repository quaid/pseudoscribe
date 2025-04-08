import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock
from pseudoscribe.infrastructure.model_manager import ModelManager, ModelInfo

@pytest.fixture
def model_manager():
    """Fixture providing a ModelManager instance"""
    manager = ModelManager()
    manager.client = AsyncMock()
    return manager

class TestModelVersions:
    @pytest.mark.asyncio
    async def test_get_versions_empty(self, model_manager):
        """New models should have no versions"""
        model_manager.get_model_status = AsyncMock(return_value=None)
        versions = await model_manager.get_model_versions("new_model")
        assert versions == []

    @pytest.mark.asyncio
    async def test_load_version_validation(self, model_manager):
        """Invalid versions should raise HTTPException"""
        with pytest.raises(HTTPException):
            await model_manager.validate_version_compatibility("test_model", "invalid_version")

    @pytest.mark.asyncio
    async def test_version_schema_validation(self, model_manager):
        """Test version schema compliance (BDD Style)"""
        # Given - invalid version format
        invalid_version = "1.0.0.0.0"
        
        # When - validating version
        with pytest.raises(HTTPException) as exc:
            await model_manager.validate_version_compatibility("test_model", invalid_version)
        
        # Then - should reject
        assert exc.value.status_code == 422
        assert "must follow semver format" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_version_lifecycle(self, model_manager):
        """Test full version lifecycle (BDD Style)"""
        # Mock
        model_manager.get_model_status = AsyncMock(
            return_value=ModelInfo(
                name="test_model",
                size="4GB",
                modified_at="2025-04-08",
                details={"versions": ["1.0.0"]}
            ))
        model_manager.unload_model = AsyncMock(return_value=True)
        
        # Test
        versions = await model_manager.get_model_versions("test_model")
        assert "1.0.0" in versions
        assert await model_manager.delete_model_version("test_model", "1.0.0")
