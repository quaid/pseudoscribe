import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from pseudoscribe.infrastructure.model_manager import ModelManager, ModelInfo
import httpx

class AsyncStreamMock:
    def __init__(self, status_code=200):
        self.status_code = status_code
    
    async def __aenter__(self):
        mock_response = MagicMock()
        mock_response.status_code = self.status_code
        return mock_response
    
    async def __aexit__(self, *args):
        pass
    
    async def iter_bytes(self):
        yield b""

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

    @pytest.mark.asyncio
    async def test_malicious_model_name(self, model_manager):
        """Reject potentially malicious model names"""
        with pytest.raises(HTTPException) as exc:
            await model_manager.validate_version_compatibility("../../../etc/passwd", "1.0.0")
        assert exc.value.status_code == 422
        assert "Invalid model name" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_model_chars(self, model_manager):
        """Reject model names with special chars"""
        for bad_name in ["model@1", "model#1", "model/1"]:
            with pytest.raises(HTTPException) as exc:
                await model_manager.validate_version_compatibility(bad_name, "1.0.0")
            assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_http_error_propagation(self, model_manager):
        """Verify HTTP errors are properly wrapped"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_error = True
        mock_response.request = MagicMock()
        
        http_error = httpx.HTTPStatusError(
            "Not Found",
            request=mock_response.request,
            response=mock_response
        )
        
        model_manager.client.get = AsyncMock(side_effect=http_error)
        
        with pytest.raises(HTTPException) as exc:
            await model_manager.get_model_versions("test_model")
            
        assert exc.value.status_code == 404
        assert "Not Found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_timeout_handling(self, model_manager):
        """Verify timeout errors are properly handled"""
        model_manager.client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        with pytest.raises(HTTPException) as exc:
            await model_manager.get_model_versions("test_model")
        assert exc.value.status_code == 408

    @pytest.mark.asyncio
    async def test_timeout_propagation(self, model_manager):
        """Should properly wrap timeout errors"""
        model_manager.client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        
        with pytest.raises(HTTPException) as exc:
            await model_manager.get_model_status("test_model")
            
        assert exc.value.status_code == 408
        assert "Model service timeout" in exc.value.detail

    @pytest.mark.asyncio
    async def test_invalid_model_info_format(self, model_manager):
        """Should raise HTTPException when model info is malformed"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test"}  # Missing required fields
        model_manager.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(HTTPException) as exc:
            await model_manager.get_model_status("test_model")
            
        assert exc.value.status_code == 500
        assert "Invalid model info format" in exc.value.detail

    @pytest.mark.asyncio
    async def test_get_model_status_success(self, model_manager):
        """Should return ModelInfo when response is valid"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test_model",
            "size": "1024",
            "modified_at": "2025-01-01",
            "details": {"versions": ["1.0", "2.0"]}
        }
        model_manager.client.get = AsyncMock(return_value=mock_response)
        
        result = await model_manager.get_model_status("test_model")
        
        assert result.name == "test_model"
        assert result.size == "1024"

    @pytest.mark.asyncio
    async def test_invalid_version_format(self, model_manager):
        """Should reject invalid version formats"""
        with pytest.raises(HTTPException) as exc:
            await model_manager.validate_version_compatibility("valid_model", "1.0-beta")
        assert exc.value.status_code == 422
        assert "semver format" in exc.value.detail

    @pytest.mark.asyncio
    async def test_valid_version_format(self, model_manager):
        """Should accept valid semver versions"""
        result = await model_manager.validate_version_compatibility("valid_model", "1.0.0")
        assert result is True

    @pytest.mark.asyncio
    async def test_load_model_success(self, model_manager):
        """Verify successful model loading"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create a mock async context manager
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        model_manager.client.stream = MagicMock(return_value=mock_stream)
        
        loaded = await model_manager.load_model("valid_model", "1.0.0")
        assert loaded is True

    @pytest.mark.asyncio
    async def test_load_model_failure(self, model_manager):
        """Verify failed model loading"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        # Create a mock async context manager
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        model_manager.client.stream = MagicMock(return_value=mock_stream)
        
        with pytest.raises(HTTPException) as exc:
            await model_manager.load_model("invalid_model", "1.0.0")
        assert exc.value.status_code == 404
