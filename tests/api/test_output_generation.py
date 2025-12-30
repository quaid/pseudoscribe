"""Test suite for output generation API endpoints

Tests that the REST API endpoints for multi-format content generation exist and are accessible.
The business logic is thoroughly tested in tests/generators/test_output_generator.py.
"""

import pytest
from fastapi.testclient import TestClient

from pseudoscribe.api.app import app


@pytest.fixture
def client():
    """Create test client with tenant header"""
    client = TestClient(app)
    client.headers = {"X-Tenant-ID": "test-tenant"}
    return client


class TestEndpointExistence:
    """Test that all output generation endpoints exist"""

    def test_blog_post_endpoint_exists(self, client):
        """Blog post endpoint should exist and not return 404"""
        response = client.post("/api/v1/generate/blog", json={
            "topic": "Test Topic"
        })
        assert response.status_code != 404

    def test_whitepaper_endpoint_exists(self, client):
        """Whitepaper endpoint should exist and not return 404"""
        response = client.post("/api/v1/generate/whitepaper", json={
            "topic": "Test Topic"
        })
        assert response.status_code != 404

    def test_social_endpoint_exists(self, client):
        """Social media endpoint should exist and not return 404"""
        response = client.post("/api/v1/generate/social", json={
            "topic": "Test",
            "platform": "twitter"
        })
        assert response.status_code != 404

    def test_generic_generate_endpoint_exists(self, client):
        """Generic generate endpoint should exist and not return 404"""
        response = client.post("/api/v1/generate", json={
            "topic": "Test",
            "format": "blog_post"
        })
        assert response.status_code != 404


class TestRequestValidation:
    """Test that endpoints validate request parameters"""

    def test_empty_topic_returns_error(self, client):
        """Empty topic should return validation error"""
        response = client.post("/api/v1/generate/blog", json={
            "topic": ""
        })
        # Should return error (400 or 422)
        assert response.status_code in [400, 422]

    def test_missing_topic_returns_error(self, client):
        """Missing topic should return validation error"""
        response = client.post("/api/v1/generate/blog", json={})
        # Should return error (400 or 422)
        assert response.status_code in [400, 422]

    def test_negative_length_returns_error(self, client):
        """Negative length should return validation error"""
        response = client.post("/api/v1/generate/blog", json={
            "topic": "Test",
            "target_length": -100
        })
        # Should return error (400 or 422)
        assert response.status_code in [400, 422]

    def test_invalid_platform_returns_error(self, client):
        """Invalid social platform should return error"""
        response = client.post("/api/v1/generate/social", json={
            "topic": "Test",
            "platform": "invalid_platform"
        })
        # Should return error
        assert response.status_code in [400, 422, 500]

    def test_invalid_format_returns_error(self, client):
        """Invalid format should return validation error"""
        response = client.post("/api/v1/generate", json={
            "topic": "Test",
            "format": "invalid_format"
        })
        # Should return error (400 or 422)
        assert response.status_code in [400, 422]
