#!/usr/bin/env python3
"""
Model Loading Script for Testing and Production

This script ensures consistent model availability across environments:
- Test environment: Loads lightweight models for fast testing
- Production environment: Loads production-ready models
- Development environment: Configurable model sets

Follows semantic versioning and TDD standards.
"""

import asyncio
import httpx
import json
import logging
import os
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types for model loading"""
    TEST = "test"
    DEVELOPMENT = "development" 
    PRODUCTION = "production"

@dataclass
class ModelConfig:
    """Configuration for a model to be loaded"""
    name: str
    size_mb: int
    description: str
    required_for_tests: bool = False
    production_ready: bool = False

class ModelLoader:
    """Handles loading models into Ollama service"""
    
    def __init__(self, ollama_url: str = "http://ollama-svc:11434"):
        self.ollama_url = ollama_url
        self.timeout = httpx.Timeout(300.0)  # 5 minutes for model downloads
        
    async def check_ollama_health(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """List currently available models in Ollama"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get('models', [])
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            logger.info(f"Pulling model: {model_name}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully pulled model: {model_name}")
                    return True
                else:
                    logger.error(f"Failed to pull model {model_name}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        models = await self.list_available_models()
        return any(model.get('name') == model_name for model in models)

class TestModelManager:
    """Manages model loading for different environments"""
    
    # Test models - small, fast to download
    TEST_MODELS = [
        ModelConfig(
            name="tinyllama:latest",
            size_mb=637,
            description="Tiny LLaMA model for fast testing",
            required_for_tests=True,
            production_ready=False
        ),
    ]
    
    # Development models - balance of size and capability
    DEVELOPMENT_MODELS = [
        ModelConfig(
            name="tinyllama:latest", 
            size_mb=637,
            description="Tiny LLaMA for development",
            required_for_tests=True,
            production_ready=False
        ),
        ModelConfig(
            name="llama2:7b",
            size_mb=3800,
            description="LLaMA 2 7B for development testing",
            required_for_tests=False,
            production_ready=True
        ),
    ]
    
    # Production models - full capability
    PRODUCTION_MODELS = [
        ModelConfig(
            name="llama2:7b",
            size_mb=3800,
            description="LLaMA 2 7B production model",
            required_for_tests=False,
            production_ready=True
        ),
        ModelConfig(
            name="mistral:7b",
            size_mb=4100,
            description="Mistral 7B production model", 
            required_for_tests=False,
            production_ready=True
        ),
    ]
    
    def __init__(self, loader: ModelLoader):
        self.loader = loader
    
    def get_models_for_environment(self, env: Environment) -> List[ModelConfig]:
        """Get appropriate models for the given environment"""
        if env == Environment.TEST:
            return self.TEST_MODELS
        elif env == Environment.DEVELOPMENT:
            return self.DEVELOPMENT_MODELS
        elif env == Environment.PRODUCTION:
            return self.PRODUCTION_MODELS
        else:
            return self.TEST_MODELS
    
    async def setup_environment(self, env: Environment, force_reload: bool = False) -> bool:
        """Set up models for the specified environment"""
        logger.info(f"Setting up {env.value} environment")
        
        # Check Ollama health
        if not await self.loader.check_ollama_health():
            logger.error("Ollama service is not available")
            return False
        
        models_to_load = self.get_models_for_environment(env)
        success_count = 0
        
        for model_config in models_to_load:
            # Check if model already exists
            if not force_reload and await self.loader.is_model_available(model_config.name):
                logger.info(f"Model {model_config.name} already available")
                success_count += 1
                continue
            
            # Pull the model
            logger.info(f"Loading {model_config.name} ({model_config.size_mb}MB) - {model_config.description}")
            if await self.loader.pull_model(model_config.name):
                success_count += 1
            else:
                logger.error(f"Failed to load {model_config.name}")
                
                # If this is a required test model, fail fast
                if model_config.required_for_tests and env == Environment.TEST:
                    logger.error("Required test model failed to load - aborting")
                    return False
        
        logger.info(f"Successfully loaded {success_count}/{len(models_to_load)} models")
        return success_count > 0
    
    async def validate_test_environment(self) -> bool:
        """Validate that test environment has required models"""
        logger.info("Validating test environment")
        
        required_models = [m for m in self.TEST_MODELS if m.required_for_tests]
        available_models = await self.loader.list_available_models()
        available_names = [m.get('name') for m in available_models]
        
        missing_models = []
        for model in required_models:
            if model.name not in available_names:
                missing_models.append(model.name)
        
        if missing_models:
            logger.error(f"Missing required test models: {missing_models}")
            return False
        
        logger.info("Test environment validation passed")
        return True

async def main():
    """Main entry point for model loading script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load models for PseudoScribe testing/production")
    parser.add_argument("--env", choices=["test", "development", "production"], 
                       default="test", help="Environment to set up")
    parser.add_argument("--ollama-url", default="http://ollama-svc:11434",
                       help="Ollama service URL")
    parser.add_argument("--force-reload", action="store_true",
                       help="Force reload models even if they exist")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate existing models, don't load new ones")
    
    args = parser.parse_args()
    
    # Create loader and manager
    loader = ModelLoader(args.ollama_url)
    manager = TestModelManager(loader)
    
    env = Environment(args.env)
    
    try:
        if args.validate_only:
            if env == Environment.TEST:
                success = await manager.validate_test_environment()
            else:
                logger.info("Validation only supported for test environment")
                success = True
        else:
            success = await manager.setup_environment(env, args.force_reload)
        
        if success:
            logger.info(f"✅ {env.value} environment setup completed successfully")
            
            # Show available models
            models = await loader.list_available_models()
            logger.info(f"Available models: {len(models)}")
            for model in models:
                size_gb = model.get('size', 0) / (1024**3)
                logger.info(f"  - {model.get('name')}: {size_gb:.2f}GB")
            
            sys.exit(0)
        else:
            logger.error(f"❌ {env.value} environment setup failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
