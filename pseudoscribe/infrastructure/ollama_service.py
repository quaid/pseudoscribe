"""Ollama service integration for local AI model management"""

from typing import AsyncGenerator, Dict, List, Optional
import httpx
from fastapi import HTTPException
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Model information response"""
    name: str
    size: str
    type: str
    description: Optional[str]
    parameters: Optional[Dict[str, any]]


class GenerationResponse(BaseModel):
    """Text generation response"""
    text: str
    token_count: Optional[int]


class OllamaService:
    """Service for interacting with Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama service
        
        Args:
            base_url: URL where Ollama is running
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def list_models(self) -> List[Dict[str, any]]:
        """List all available models
        
        Returns:
            List of model dictionaries
        """
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Ollama: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Ollama error: {e.response.text}")

    async def load_model(self, model_name: str) -> bool:
        """Load a model into Ollama
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            True if model was loaded successfully
        """
        try:
            response = await self.client.post(
                "/api/pull",
                json={"name": model_name}
            )
            response.raise_for_status()
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
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    **kwargs
                }
            )
            response.raise_for_status()
            return GenerationResponse(**response.json())
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Generation failed: {e.response.text}")

    async def stream_generate(self, model_name: str, prompt: str, **kwargs) -> AsyncGenerator[Dict[str, str], None]:
        """Stream generate text using a model
        
        Args:
            model_name: Name of the model to use
            prompt: Input prompt for generation
            kwargs: Additional generation parameters
            
        Yields:
            Dictionary containing the generated text chunk
        """
        try:
            async with self.client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": True,
                    **kwargs
                }
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
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
            response = await self.client.get(f"/api/show?name={model_name}")
            response.raise_for_status()
            return ModelInfo(**response.json())
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to get model info: {e.response.text}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
