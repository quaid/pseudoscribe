"""Tests for model management"""

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from pytest_asyncio import fixture
import asyncio

from pseudoscribe.infrastructure.model_manager import ModelManager

@fixture(scope="function")
async def model_manager():
    """Fixture for model manager instance"""
    manager = ModelManager()
    yield manager
    await manager.client.aclose()

@fixture(scope="function")
async def check_ollama_running():
    """Fixture to check if Ollama service is running"""
    try:
        async with AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            return True
    except Exception:
        return False

@pytest.mark.asyncio
async def test_list_available_models(model_manager, check_ollama_running):
    """
    Scenario: List available models
    Given the Ollama service is running
    When listing available models
    Then the list of available models is returned
    """
    if not check_ollama_running:
        pytest.skip("Ollama service is not running")
    
    # Given
    manager = model_manager
    
    # When
    models = await manager.list_available_models()
    
    # Then
    assert isinstance(models, list)
    assert all(isinstance(m, dict) for m in models)
    assert all("name" in m for m in models)

@pytest.mark.asyncio
async def test_load_model(model_manager, check_ollama_running):
    """
    Scenario: Load a model into Ollama
    Given a valid model name
    When loading the model
    Then the model is successfully loaded
    """
    if not check_ollama_running:
        pytest.skip("Ollama service is not running")
    
    # Given
    manager = model_manager
    model_name = "llama2"
    
    # When
    result = await manager.load_model(model_name)
    
    # Then
    assert result is True

    # Wait for the model to be fully loaded
    await asyncio.sleep(5)

    # Verify the model was loaded
    models = await manager.list_available_models()
    assert any(m["name"] == f"{model_name}:latest" for m in models)

@pytest.mark.asyncio
async def test_unload_model(model_manager, check_ollama_running):
    """
    Scenario: Unload a model from Ollama
    Given a loaded model
    When unloading the model
    Then the model is successfully unloaded
    """
    if not check_ollama_running:
        pytest.skip("Ollama service is not running")
    
    # Given
    manager = model_manager
    model_name = "llama2"
    
    # First load the model
    await manager.load_model(model_name)

    # When
    result = await manager.unload_model(model_name)
    
    # Then
    assert result is True

    # Wait for the model to be fully unloaded
    await asyncio.sleep(2)

    # Verify the model was unloaded
    models = await manager.list_available_models()
    assert not any(m["name"] == f"{model_name}:latest" for m in models)

@pytest.mark.asyncio
async def test_get_model_status(model_manager, check_ollama_running):
    """
    Scenario: Get model status
    Given a model name
    When getting model status
    Then the model's status is returned
    """
    if not check_ollama_running:
        pytest.skip("Ollama service is not running")
    
    # Given
    manager = model_manager
    model_name = "llama2"
    
    # First load the model
    await manager.load_model(model_name)

    # Wait for the model to be fully loaded
    await asyncio.sleep(5)

    # When
    status = await manager.get_model_status(f"{model_name}:latest")
    
    # Then
    assert isinstance(status, dict)
    assert "loaded" in status
    assert isinstance(status["loaded"], bool)
    assert "size" in status
    assert isinstance(status["size"], int)
    assert "type" in status
    assert isinstance(status["type"], str)
