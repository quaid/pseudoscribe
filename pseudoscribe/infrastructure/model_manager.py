"""Service for managing AI models"""

from typing import List, Dict, Any
from fastapi import HTTPException
import httpx
from pydantic import BaseModel

class ModelStatus(BaseModel):
    """Model status response"""
    loaded: bool
    size: int
    type: str

class ModelManager:
    """Service for managing AI models"""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 30.0):
        """Initialize ModelManager

        Args:
            base_url: Base URL for Ollama service
            timeout: Timeout for requests in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """List available models

        Returns:
            List of model dictionaries
        """
        try:
            response = await self.client.request(
                "GET",
                "/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

    async def load_model(self, model_name: str) -> bool:
        """Load a model into Ollama

        Args:
            model_name: Name of the model to load

        Returns:
            True if model was loaded successfully
        """
        try:
            # Create the model directly
            create_response = await self.client.request(
                "POST",
                "/api/create",
                json={
                    "name": model_name,
                    "from": f"{model_name}:latest"
                },
                timeout=self.timeout
            )
            create_response.raise_for_status()

            return True
        except httpx.HTTPError as e:
            raise HTTPException(status_code=e.status_code, detail=f"Failed to load model {model_name}: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load model {model_name}: {str(e)}")

    async def unload_model(self, model_name: str) -> bool:
        """Unload a model from Ollama

        Args:
            model_name: Name of the model to unload

        Returns:
            True if model was unloaded successfully
        """
        try:
            # Delete the model using the correct endpoint
            delete_response = await self.client.request(
                "DELETE",
                "/api/delete",
                json={"model": model_name},
                timeout=self.timeout
            )
            delete_response.raise_for_status()

            return True
        except httpx.HTTPError as e:
            raise HTTPException(status_code=e.status_code, detail=f"Failed to unload model {model_name}: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to unload model {model_name}: {str(e)}")

    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """Get information about a model

        Args:
            model_name: Name of the model to get info for

        Returns:
            Dictionary containing model status
        """
        try:
            # First get the model tags
            response = await self.client.request(
                "GET",
                "/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Find the model in the list
            for model in data.get("models", []):
                if model["name"] == model_name:
                    return {
                        "loaded": True,
                        "size": model.get("size", 0),
                        "type": model.get("details", {}).get("family", "unknown")
                    }
            
            return {
                "loaded": False,
                "size": 0,
                "type": "unknown"
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=e.status_code, detail=f"Failed to get model status: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")
