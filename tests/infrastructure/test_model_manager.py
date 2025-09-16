"""Tests for ModelManager"""

import pytest
import os
from fastapi import HTTPException
from httpx import HTTPStatusError
import asyncio
from pytest_asyncio import fixture as pytest_asyncio_fixture
from unittest.mock import MagicMock, AsyncMock
import pytest_mock

from pseudoscribe.infrastructure.model_manager import ModelManager, ModelInfo

class AsyncContextManagerMock:
    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, *args):
        pass

@pytest_asyncio_fixture
async def model_manager():
    """Fixture for ModelManager"""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return ModelManager(ollama_url)

@pytest.mark.asyncio
async def test_list_available_models(model_manager, mocker):
    """Verify list of available models"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "llama2"}]}
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    
    models = await model_manager.list_available_models()
    assert models == [{"name": "llama2"}]

@pytest.mark.asyncio
async def test_load_model(model_manager, mocker):
    """Verify model loading"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mocker.patch("httpx.AsyncClient.stream",
               return_value=AsyncContextManagerMock(mock_response))
    
    loaded = await model_manager.load_model("llama2", "latest")
    assert loaded is True

@pytest.mark.asyncio
async def test_unload_model(model_manager, mocker):
    """Verify model unloading"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mocker.patch("httpx.AsyncClient.request", return_value=mock_response)
    
    unloaded = await model_manager.unload_model("llama2")
    assert unloaded

@pytest.mark.asyncio
async def test_get_model_status(model_manager, mocker):
    """Verify ModelInfo is returned for valid models"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"name": "llama2", "size": "7B", "modified_at": "2023-01-01"}
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    
    status = await model_manager.get_model_status("llama2")
    assert isinstance(status, ModelInfo)
    assert status.name == "llama2"

@pytest.mark.asyncio
async def test_get_nonexistent_model_status(model_manager, mocker):
    """Verify None is returned for missing models"""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    
    status = await model_manager.get_model_status("nonexistent_model")
    assert status is None

@pytest.mark.asyncio
async def test_load_model_failure(model_manager, mocker):
    """Verify HTTPException is raised for invalid models"""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mocker.patch("httpx.AsyncClient.stream",
               return_value=AsyncContextManagerMock(mock_response))
    
    with pytest.raises(HTTPException) as exc:
        await model_manager.load_model("invalid_model_123", "latest")
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_unload_nonexistent_model(model_manager, mocker):
    """Verify False is returned for missing models"""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mocker.patch("httpx.AsyncClient.request", return_value=mock_response)
    
    unloaded = await model_manager.unload_model("nonexistent_model")
    assert not unloaded

@pytest.mark.asyncio
async def test_model_streaming_performance(model_manager, mocker):
    """Verify streaming performance"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mocker.patch("httpx.AsyncClient.stream", 
               return_value=AsyncContextManagerMock(mock_response))
    
    start = asyncio.get_event_loop().time()
    await model_manager.load_model("llama2", "latest")
    duration = asyncio.get_event_loop().time() - start
    assert duration < 5.0

@pytest.mark.asyncio
async def test_concurrent_model_access(model_manager, mocker):
    """Verify concurrent model access"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mocker.patch("httpx.AsyncClient.stream", 
               return_value=AsyncContextManagerMock(mock_response))
    
    # Simulate concurrent access
    results = await asyncio.gather(
        model_manager.load_model("llama2", "latest"),
        model_manager.load_model("llama2", "latest")
    )
    assert all(results)

@pytest.mark.asyncio
async def test_get_model_status_validation_error(model_manager, mocker):
    """Test handling of invalid model status response"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"invalid": "data"}
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    
    with pytest.raises(HTTPException):
        await model_manager.get_model_status("invalid-model")

@pytest.mark.asyncio
async def test_load_model_streaming(model_manager, mocker):
    """Test streaming model loading"""
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [b'{"status":"success"}']
    mock_client = AsyncMock()
    mock_client.stream.return_value.__aenter__.return_value = mock_stream
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    
    loaded = await model_manager.load_model("llama2", "latest")
    assert loaded

@pytest.mark.asyncio
async def test_unload_model_error_handling(model_manager, mocker):
    """Test error handling during model unloading"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = HTTPStatusError("Server error", request=None, response=mock_response)
    mocker.patch("httpx.AsyncClient.request", return_value=mock_response)
    
    with pytest.raises(HTTPException) as exc:
        await model_manager.unload_model("error-model")
    assert exc.value.status_code == 500

@pytest.mark.asyncio
async def test_get_model_status_server_error(model_manager, mocker):
    """Test 500 error handling"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
    
    with pytest.raises(HTTPException) as exc:
        await model_manager.get_model_status("error-model")
    assert exc.value.status_code == 500

@pytest.mark.asyncio
async def test_load_model_timeout(model_manager, mocker):
    """Test timeout handling"""
    mocker.patch("httpx.AsyncClient.stream", side_effect=TimeoutError)
    
    with pytest.raises(HTTPException) as exc:
        await model_manager.load_model("timeout-model", "latest")
    assert exc.value.status_code == 408
    assert "timed out" in str(exc.value.detail).lower()
