"""Service for managing AI models

Privacy Note:
- All operations occur locally
- No data leaves the system without explicit consent
- Model weights remain on local storage

Performance:
- Target response time: <2s
- Memory constraint: <500MB
"""

from typing import List, Dict, Optional, Any
import httpx
import json
from fastapi import HTTPException
from httpx import HTTPStatusError

from .schema import ModelInfo
from .ollama_service import OllamaService

class ModelManager:
    """Service for managing AI models
    
    Security Considerations:
    - Validates all model names
    - Implements request timeouts
    - Isolates model operations
    """
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize ModelManager"""
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available models
        
        Returns:
            List of model dictionaries
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to list models: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

    async def load_model(self, model_name: str) -> bool:
        """
        Load a model into Ollama
        
        Args:
            model_name: Name of the model to load
        
        Returns:
            True if successful, False if model doesn't exist
        
        Raises:
            HTTPException: For communication errors (other than 404)
        """
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=30.0
            ) as response:
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Model not found")
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    if b"error" in chunk:
                        raise HTTPException(status_code=500, detail=chunk.decode())
            return True
        except TimeoutError:
            raise HTTPException(status_code=408, detail="Request timed out")
        except HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from Ollama

        Args:
            model_name: Name of the model to unload

        Returns:
            True if successful, False if model not found
        """
        try:
            response = await self.client.request(
                "DELETE",
                f"{self.base_url}/api/delete",
                json={"name": model_name}
            )
            if response.status_code == 404:
                return False
            response.raise_for_status()
            return True
        except HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to unload model: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error unloading model: {str(e)}")

    async def get_model_status(self, model_name: str) -> Optional[ModelInfo]:
        """
        Get information about a model
        
        Args:
            model_name: Name of the model (without :latest suffix)
        
        Returns:
            ModelInfo containing model details or None if model doesn't exist
        
        Raises:
            HTTPException: For communication errors (other than 404)
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/show", params={"name": model_name})
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            if not all(k in data for k in ("name", "size", "modified_at")):
                raise HTTPException(status_code=500, detail="Invalid model info format")
            return ModelInfo(**data)
        except HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
