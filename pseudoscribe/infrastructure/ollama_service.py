"""Ollama service integration for local AI model management"""

from typing import AsyncGenerator, Dict, List, Optional, Any
import httpx
from fastapi import HTTPException
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Model information response"""
    name: str
    size: int
    type: str


class GenerationResponse(BaseModel):
    """Generation response"""
    model: str
    response: str
    token_count: int
    duration: int


class OllamaService:
    """Service for interacting with Ollama AI service"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 30.0):
        """Initialize Ollama service
        
        Args:
            base_url: URL where Ollama is running
            timeout: Timeout for requests in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models
        
        Returns:
            List of model dictionaries
        """
        try:
            response = await self.client.get("/api/tags", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to list models: {e.response.text}")

    async def load_model(self, model_name: str) -> bool:
        """Load a model into Ollama
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            True if model was loaded successfully
        """
        try:
            # First try to pull the model
            pull_response = await self.client.post("/api/pull", json={"name": model_name}, timeout=self.timeout)
            pull_response.raise_for_status()

            # Then create the model
            create_response = await self.client.post("/api/create", json={
                "name": model_name,
                "path": f"{model_name}:latest"
            }, timeout=self.timeout)
            create_response.raise_for_status()

            return True
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to load model: {e.response.text}")

    async def generate(self, model_name: str, prompt: str, **kwargs) -> GenerationResponse:
        """Generate text using a model
        
        Args:
            model_name: Name of the model to use
            prompt: Input prompt for generation
            kwargs: Additional generation parameters
            
        Returns:
            GenerationResponse containing the generated text
        """
        try:
            response = await self.client.post("/api/generate", json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return GenerationResponse(
                model=model_name,
                response=data.get("response", ""),
                token_count=data.get("token_count", 0),
                duration=data.get("duration", 0)
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Generation failed: {e.response.text}")

    async def stream_generate(self, model_name: str, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream generate text using a model
        
        Args:
            model_name: Name of the model to use
            prompt: Input prompt for generation
            kwargs: Additional generation parameters
            
        Yields:
            Dictionary containing chunks of generated text
        """
        try:
            async with self.client.stream("POST", "/api/generate", json={
                "model": model_name,
                "prompt": prompt,
                "stream": True,
                **kwargs
            }, timeout=self.timeout) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    if chunk.strip():  # Only yield non-empty chunks
                        yield {"text": chunk}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Stream generation failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Stream generation failed: {e.response.text}")

    async def model_info(self, model_name: str) -> ModelInfo:
        """Get information about a model
        
        Args:
            model_name: Name of the model to get info for
            
        Returns:
            ModelInfo containing model metadata
        """
        try:
            # First get the model tags
            response = await self.client.get("/api/tags", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # Find the model in the list
            for model in data.get("models", []):
                if model["name"] == model_name:
                    return ModelInfo(
                        name=model.get("name", ""),
                        size=model.get("size", 0),
                        type="llama"  # Ollama only supports llama models currently
                    )
            
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to get model info: {e.response.text}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
