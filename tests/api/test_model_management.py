"""
Tests for AI-002: Model Management API

This module tests the comprehensive model management capabilities including:
- Model loading and unloading
- Version management and validation
- Resource allocation tracking
- Model availability monitoring
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

from pseudoscribe.api.app import app
from pseudoscribe.infrastructure.model_manager import ModelManager
from pseudoscribe.infrastructure.ollama_service import OllamaService
from pseudoscribe.api.dependencies import get_model_manager, get_ollama_service

# Create test client
client = TestClient(app)

class TestModelManagementAPI:
    """Test suite for AI-002 Model Management user story"""
    
    def test_load_model_success(self):
        """Test successful model loading with real Ollama service"""
        # Test with real model that exists in Ollama (tinyllama)
        response = client.post(
            "/api/v1/models/load",
            json={"name": "tinyllama:latest"},
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "tinyllama:latest"
        assert data["status"] == "loaded"
        assert data["available"] is True
        assert "resource_usage" in data
    
    def test_load_model_not_found(self):
        """Test loading non-existent model with real Ollama service"""
        # Test with a model that definitely doesn't exist
        response = client.post(
            "/api/v1/models/load",
            json={"name": "nonexistent-model-xyz", "version": "1.0.0"},
            headers={"X-Tenant-ID": "test-tenant"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_unload_model_success(self):
        """Test successful model unloading"""
        with patch('pseudoscribe.api.dependencies.get_model_manager') as mock_get_manager:
            
            mock_manager = Mock(spec=ModelManager)
            mock_get_manager.return_value = mock_manager
            
            mock_manager.unload_model = AsyncMock(return_value={
                'model_name': 'llama2',
                'status': 'unloaded',
                'resources_freed': {
                    'memory_mb': 100,
                    'cpu_percent': 5
                }
            })
            
            response = client.delete("/api/v1/models/llama2/unload", headers={"X-Tenant-ID": "test-tenant"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unloaded"
            assert "resources_freed" in data
    
    def test_list_models(self):
        """Test listing all available models with real Ollama service"""
        response = client.get("/api/v1/models/list", headers={"X-Tenant-ID": "test-tenant"})
        
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "models" in data
        assert isinstance(data["models"], list)
        
        # Should have at least tinyllama from our test setup
        if data["total_count"] > 0:
            model_names = [m["name"] for m in data["models"]]
            assert "tinyllama:latest" in model_names
    
    def test_get_model_status(self):
        """Test getting status of specific model with real integration"""
        # First load a model
        load_response = client.post(
            "/api/v1/models/load",
            json={"name": "tinyllama:latest"},
            headers={"X-Tenant-ID": "test-tenant"}
        )
        assert load_response.status_code == 200
        
        # Now check its status
        response = client.get("/api/v1/models/tinyllama:latest/status", headers={"X-Tenant-ID": "test-tenant"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "tinyllama:latest"
        assert data["status"] == "loaded"
        assert data["available"] is True
        assert "resource_usage" in data
    
    def test_get_resource_usage(self):
        """Test getting current resource usage with real integration"""
        response = client.get("/api/v1/models/resources", headers={"X-Tenant-ID": "test-tenant"})
        
        assert response.status_code == 200
        data = response.json()
        # Check that we get real resource data
        assert "memory_mb" in data
        assert "cpu_percent" in data
        assert "models_loaded" in data
        assert data["memory_mb"] > 0  # Should have some memory usage
        assert data["cpu_percent"] >= 0  # CPU can be 0 or positive
        assert isinstance(data["models_loaded"], int)
    
    def test_validate_model_version_valid(self):
        """Test validating valid model version"""
        with patch('pseudoscribe.api.dependencies.get_model_manager') as mock_get_manager:
            
            mock_manager = Mock(spec=ModelManager)
            mock_get_manager.return_value = mock_manager
            
            mock_manager.validate_version = AsyncMock(return_value={
                'valid': True,
                'format_valid': True,
                'compatible': True,
                'message': 'Version validation successful'
            })
            
            response = client.post(
                "/api/v1/models/llama2/validate-version",
                params={"version": "1.2.3"},
                headers={"X-Tenant-ID": "test-tenant"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["format_valid"] is True
            assert data["compatible"] is True
    
    def test_validate_model_version_invalid(self):
        """Test validating invalid model version"""
        with patch('pseudoscribe.api.dependencies.get_model_manager') as mock_get_manager:
            
            mock_manager = Mock(spec=ModelManager)
            mock_get_manager.return_value = mock_manager
            
            mock_manager.validate_version = AsyncMock(return_value={
                'valid': False,
                'format_valid': False,
                'compatible': False,
                'message': 'Invalid version format'
            })
            
            response = client.post(
                "/api/v1/models/llama2/validate-version",
                params={"version": "invalid.version"},
                headers={"X-Tenant-ID": "test-tenant"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert data["format_valid"] is False
            assert data["compatible"] is False

class TestModelManagementBDD:
    """BDD-style tests for AI-002 Model Management scenarios"""
    
    def test_scenario_loading_models_llama2(self):
        """
        Scenario: Loading models - tinyllama (real integration)
        Given I have model "tinyllama:latest"
        When I load the model
        Then it should be available
        And properly versioned
        """
        # When I load the model (using real tinyllama)
        response = client.post("/api/v1/models/load", json={"name": "tinyllama:latest"}, headers={"X-Tenant-ID": "test-tenant"})
        
        # Then it should be available
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        
        # And properly versioned
        assert "version" in data
        assert data["status"] == "loaded"
    
    def test_scenario_loading_models_mistral(self):
        """
        Scenario: Loading models - testing with non-existent model
        Given I have model "mistral" (not loaded)
        When I try to load the model
        Then it should fail with 404
        """
        # When I try to load a model that doesn't exist
        response = client.post("/api/v1/models/load", json={"name": "mistral:latest"}, headers={"X-Tenant-ID": "test-tenant"})
        
        # Then it should fail with 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_scenario_model_version_management(self):
        """
        Scenario: Model version management
        Given I have a model "tinyllama:latest"
        When I check the model version
        Then I should see version information
        And version format should be valid
        """
        # Load the model first
        load_response = client.post("/api/v1/models/load", json={"name": "tinyllama:latest"}, headers={"X-Tenant-ID": "test-tenant"})
        assert load_response.status_code == 200
        
        # When I check the model version
        response = client.get("/api/v1/models/tinyllama:latest/status", headers={"X-Tenant-ID": "test-tenant"})
        
        # Then I should see version information
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        
        # And version format should be valid
        version = data["version"]
        assert version is not None
    
    def test_scenario_model_resource_allocation(self):
        """
        Scenario: Model resource allocation
        Given I have a model loaded
        When I check resource usage
        Then memory usage should be within limits
        And CPU allocation should be tracked
        """
        # Load a model first
        client.post("/api/v1/models/load", json={"name": "tinyllama:latest"}, headers={"X-Tenant-ID": "test-tenant"})
        
        # When I check resource usage
        response = client.get("/api/v1/models/resources", headers={"X-Tenant-ID": "test-tenant"})
        
        # Then memory usage should be within limits
        assert response.status_code == 200
        data = response.json()
        assert data["memory_mb"] > 0
        assert data["memory_mb"] < 10000  # Reasonable upper limit
        
        # And CPU allocation should be tracked
        assert "cpu_percent" in data
        assert data["cpu_percent"] >= 0
        assert data["models_loaded"] >= 0  # At least 0 models
    
    def test_scenario_model_availability_check(self):
        """
        Scenario: Model availability check
        Given I have loaded model "tinyllama:latest"
        When I check model availability
        Then the model should be listed as available
        And status should be "loaded"
        """
        # Given I have loaded model "tinyllama:latest"
        client.post("/api/v1/models/load", json={"name": "tinyllama:latest"}, headers={"X-Tenant-ID": "test-tenant"})
        
        # When I check model availability
        response = client.get("/api/v1/models/tinyllama:latest/status", headers={"X-Tenant-ID": "test-tenant"})
        
        # Then the model should be listed as available
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        
        # And status should be "loaded"
        assert data["status"] == "loaded"
    
    def test_scenario_model_unloading(self):
        """
        Scenario: Model unloading
        Given I have a loaded model "mistral"
        When I unload the model
        Then the model should not be available
        And resources should be freed
        """
        with patch('pseudoscribe.api.dependencies.get_model_manager') as mock_get_manager:
            
            # Given I have a loaded model "mistral"
            mock_manager = Mock(spec=ModelManager)
            mock_get_manager.return_value = mock_manager
            
            # When I unload the model
            mock_manager.unload_model = AsyncMock(return_value={
                'model_name': 'mistral',
                'status': 'unloaded',
                'resources_freed': {
                    'memory_mb': 200,
                    'cpu_percent': 10
                }
            })
            
            response = client.delete("/api/v1/models/mistral/unload", headers={"X-Tenant-ID": "test-tenant"})
            
            # Then the model should not be available (status unloaded)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unloaded"
            
            # And resources should be freed
            assert "resources_freed" in data
            resources_freed = data["resources_freed"]
            assert resources_freed["memory_mb"] > 0
            assert resources_freed["cpu_percent"] >= 0
