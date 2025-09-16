"""Shared fixtures for API tests."""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from pseudoscribe.api.app import app
from pseudoscribe.api.dependencies import get_db, get_model_manager
from pseudoscribe.infrastructure.model_manager import ModelManager


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with overridden dependencies for API tests.
    """
    # Mock the ModelManager
    mock_model_manager = MagicMock(spec=ModelManager)
    mock_model_manager.generate_vectors = AsyncMock(return_value=np.array([0.1, 0.2, 0.3] * 256))
    mock_model_manager.generate_text = AsyncMock(return_value="This is some adapted text.")

    # Override dependencies
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_model_manager] = lambda: mock_model_manager
    
    yield TestClient(app)
    
    # Clear overrides after tests
    app.dependency_overrides.clear()
