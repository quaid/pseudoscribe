"""FastAPI dependency injection"""

import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from fastapi import Depends

from pseudoscribe.infrastructure.model_manager import ModelManager
from pseudoscribe.infrastructure.role_manager import RoleManager
from pseudoscribe.infrastructure.style_adapter import StyleAdapter
from pseudoscribe.infrastructure.style_checker import StyleChecker
from pseudoscribe.infrastructure.style_profiler import StyleProfiler
from pseudoscribe.infrastructure.tenant_config import TenantConfigManager
from pseudoscribe.infrastructure.ollama_service import OllamaService
from pseudoscribe.infrastructure.audio_processor import AudioProcessor
from pseudoscribe.infrastructure.research_processor import ResearchProcessor
from pseudoscribe.infrastructure.zerodb_service import ZeroDBService

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/pseudoscribe")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_role_manager() -> RoleManager:
    """Get role manager instance"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in the environment")
    return RoleManager(database_url=db_url)


@lru_cache()
def get_tenant_config_manager() -> TenantConfigManager:
    """Get tenant config manager instance"""
    return TenantConfigManager()


@lru_cache()
def get_ollama_service() -> OllamaService:
    """Get Ollama service instance"""
    return OllamaService()


@lru_cache()
def get_model_manager() -> ModelManager:
    """Get model manager instance"""
    return ModelManager()


@lru_cache()
def get_style_profiler(model_manager: ModelManager = Depends(get_model_manager)) -> StyleProfiler:
    """Get style profiler instance"""
    return StyleProfiler(model_manager=model_manager)


@lru_cache()
def get_style_checker(style_profiler: StyleProfiler = Depends(get_style_profiler)) -> StyleChecker:
    """Get style checker instance"""
    return StyleChecker(style_profiler=style_profiler)


@lru_cache()
def get_style_adapter(
    style_profiler: StyleProfiler = Depends(get_style_profiler),
    style_checker: StyleChecker = Depends(get_style_checker),
    model_manager: ModelManager = Depends(get_model_manager),
) -> StyleAdapter:
    """Get style adapter instance"""
    return StyleAdapter(
        style_profiler=style_profiler,
        style_checker=style_checker,
        model_manager=model_manager,
    )


@lru_cache()
def get_audio_processor() -> AudioProcessor:
    """Get audio processor instance"""
    return AudioProcessor()


@lru_cache()
def get_zerodb_service() -> ZeroDBService:
    """Get ZeroDB service instance"""
    return ZeroDBService.get_instance()


@lru_cache()
def get_research_processor(
    zerodb_service: ZeroDBService = Depends(get_zerodb_service)
) -> ResearchProcessor:
    """Get research processor instance"""
    return ResearchProcessor(zerodb_service=zerodb_service)
