"""BDD-style tests for Ollama service integration"""

import pytest
from fastapi.testclient import TestClient

from pseudoscribe.api.app import app
from pseudoscribe.infrastructure.ollama_service import OllamaService

client = TestClient(app)

@pytest.mark.asyncio
async def test_list_models():
    """
    Scenario: List available Ollama models
    Given the Ollama service is running
    When listing models
    Then the list of available models is returned
    """
    # Given
    service = OllamaService()
    
    # When
    models = await service.list_models()
    
    # Then
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(model, dict) for model in models)
    assert all("name" in model for model in models)

@pytest.mark.asyncio
async def test_load_model():
    """
    Scenario: Load a model into Ollama
    Given a valid model name
    When loading the model
    Then the model is successfully loaded
    """
    # Given
    service = OllamaService()
    model_name = "llama2"
    
    # When
    result = await service.load_model(model_name)
    
    # Then
    assert result is True

@pytest.mark.asyncio
async def test_generate():
    """
    Scenario: Generate text using a model
    Given a loaded model
    When generating text with a prompt
    Then the generated text is returned
    """
    # Given
    service = OllamaService()
    model_name = "llama2"
    prompt = "Write a short story about a magical forest."
    
    # When
    response = await service.generate(model_name, prompt)
    
    # Then
    assert isinstance(response, dict)
    assert "text" in response
    assert isinstance(response["text"], str)
    assert len(response["text"]) > 0

@pytest.mark.asyncio
async def test_stream_generate():
    """
    Scenario: Stream generate text using a model
    Given a loaded model
    When streaming generation with a prompt
    Then text is streamed back in chunks
    """
    # Given
    service = OllamaService()
    model_name = "llama2"
    prompt = "Write a short story about a magical forest."
    
    # When
    async for chunk in service.stream_generate(model_name, prompt):
        # Then
        assert isinstance(chunk, dict)
        assert "text" in chunk
        assert isinstance(chunk["text"], str)

@pytest.mark.asyncio
async def test_model_info():
    """
    Scenario: Get model information
    Given a loaded model
    When getting model info
    Then the model's metadata is returned
    """
    # Given
    service = OllamaService()
    model_name = "llama2"
    
    # When
    info = await service.model_info(model_name)
    
    # Then
    assert isinstance(info, dict)
    assert "name" in info
    assert "size" in info
    assert "type" in info
