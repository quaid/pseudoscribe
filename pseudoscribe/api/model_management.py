"""
AI-002: Model Management API

This module provides comprehensive model management capabilities including:
- Model loading and unloading
- Version management and validation
- Resource allocation tracking
- Model availability monitoring

Performance Requirements:
- Model loading: <5s for typical models
- API response time: <200ms
- Memory usage: Tracked and limited
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

from ..infrastructure.model_manager import ModelManager
from ..infrastructure.ollama_service import OllamaService
from .dependencies import get_model_manager, get_ollama_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["Model Management"])

# Request/Response Models
class ModelLoadRequest(BaseModel):
    name: str = Field(..., description="Model name to load")
    version: Optional[str] = Field(None, description="Specific version to load")
    
class ModelInfo(BaseModel):
    name: str
    version: str
    status: str
    size_gb: Optional[float] = None
    loaded_at: Optional[datetime] = None
    
class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    total_count: int
    
class ResourceUsage(BaseModel):
    memory_mb: float
    cpu_percent: float
    models_loaded: int
    
class ModelStatusResponse(BaseModel):
    name: str
    status: str
    version: Optional[str] = None
    available: bool
    resource_usage: Optional[ResourceUsage] = None

@router.post("/load", response_model=ModelStatusResponse)
async def load_model(
    request: ModelLoadRequest,
    model_manager: ModelManager = Depends(get_model_manager),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """
    Load a specific AI model
    
    - **name**: Model name (e.g., 'llama2', 'mistral')
    - **version**: Optional specific version to load
    
    Returns model status and resource information
    """
    try:
        logger.info(f"Loading model: {request.name}")
        
        # Check if model is available in Ollama
        available_models = await ollama_service.list_models()
        model_names = [model.get('name', '') for model in available_models]
        
        if request.name not in model_names:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{request.name}' not found in available models"
            )
        
        # Load the model
        result = await model_manager.load_model(request.name, request.version)
        
        # Get resource usage
        resource_usage = await model_manager.get_resource_usage()
        
        return ModelStatusResponse(
            name=request.name,
            status="loaded",
            version=result.get('version'),
            available=True,
            resource_usage=ResourceUsage(
                memory_mb=resource_usage.get('memory_mb', 0),
                cpu_percent=resource_usage.get('cpu_percent', 0),
                models_loaded=resource_usage.get('models_loaded', 0)
            )
        )
        
    except Exception as e:
        logger.error(f"Error loading model {request.name}: {str(e)}")
        # Check if it's a "not found" error
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}"
        )

@router.delete("/{model_name}/unload")
async def unload_model(
    model_name: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Unload a specific AI model to free resources
    
    - **model_name**: Name of the model to unload
    
    Returns confirmation of unloading
    """
    try:
        logger.info(f"Unloading model: {model_name}")
        
        result = await model_manager.unload_model(model_name)
        
        return {
            "message": f"Model '{model_name}' unloaded successfully",
            "status": "unloaded",
            "resources_freed": result.get('resources_freed', {})
        }
        
    except Exception as e:
        logger.error(f"Error unloading model {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}"
        )

@router.get("/list", response_model=ModelListResponse)
async def list_models(
    model_manager: ModelManager = Depends(get_model_manager),
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """
    List all available and loaded models
    
    Returns comprehensive list of models with their status
    """
    try:
        # Get available models from Ollama
        available_models = await ollama_service.list_models()
        
        # Get loaded models from model manager
        loaded_models = await model_manager.get_loaded_models()
        
        models = []
        for model in available_models:
            model_name = model.get('name', '')
            is_loaded = model_name in loaded_models
            
            models.append(ModelInfo(
                name=model_name,
                version=model.get('version', 'unknown'),
                status="loaded" if is_loaded else "available",
                size_gb=model.get('size', 0) / (1024**3) if model.get('size') else None,
                loaded_at=loaded_models.get(model_name, {}).get('loaded_at') if is_loaded else None
            ))
        
        return ModelListResponse(
            models=models,
            total_count=len(models)
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )

@router.get("/{model_name}/status", response_model=ModelStatusResponse)
async def get_model_status(
    model_name: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Get detailed status of a specific model
    
    - **model_name**: Name of the model to check
    
    Returns detailed model status and resource usage
    """
    try:
        status_info = await model_manager.get_model_status(model_name)
        resource_usage = await model_manager.get_resource_usage()
        
        return ModelStatusResponse(
            name=model_name,
            status=status_info.get('status', 'unknown'),
            version=status_info.get('version'),
            available=status_info.get('available', False),
            resource_usage=ResourceUsage(
                memory_mb=resource_usage.get('memory_mb', 0),
                cpu_percent=resource_usage.get('cpu_percent', 0),
                models_loaded=resource_usage.get('models_loaded', 0)
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting model status for {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )

@router.get("/resources", response_model=ResourceUsage)
async def get_resource_usage(
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Get current resource usage for all loaded models
    
    Returns memory, CPU, and model count information
    """
    try:
        resource_usage = await model_manager.get_resource_usage()
        
        return ResourceUsage(
            memory_mb=resource_usage.get('memory_mb', 0),
            cpu_percent=resource_usage.get('cpu_percent', 0),
            models_loaded=resource_usage.get('models_loaded', 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting resource usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource usage: {str(e)}"
        )

@router.post("/{model_name}/validate-version")
async def validate_model_version(
    model_name: str,
    version: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Validate model version format and compatibility
    
    - **model_name**: Name of the model
    - **version**: Version string to validate
    
    Returns validation result and compatibility information
    """
    try:
        validation_result = await model_manager.validate_version(model_name, version)
        
        return {
            "model_name": model_name,
            "version": version,
            "valid": validation_result.get('valid', False),
            "format_valid": validation_result.get('format_valid', False),
            "compatible": validation_result.get('compatible', False),
            "message": validation_result.get('message', '')
        }
        
    except Exception as e:
        logger.error(f"Error validating version for {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate version: {str(e)}"
        )
