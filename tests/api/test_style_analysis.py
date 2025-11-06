"""
BDD-style tests for VSC-004 Advanced Extension Features - Style Analysis.

Following TDD workflow: Red Tests → Green Tests → Refactor
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from pseudoscribe.api.app import app

TENANT_HEADER = {"X-Tenant-ID": "test-tenant"}

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture(scope="function")
def create_test_tenant(client):
    """Fixture to create a test tenant for the style API tests."""
    tenant_data = {
        "tenant_id": "test-tenant",
        "schema_name": "test_tenant_schema",
        "display_name": "Test Tenant for VSC-004"
    }
    response = client.post("/tenants", json=tenant_data)
    assert response.status_code in [200, 400]  # 400 if it already exists
    return response

class TestRealTimeStyleAnalysis:
    """
    BDD Scenario: Real-time style analysis of selected text
    Given I have selected a paragraph of text in my document
    When I trigger the "Analyze Style" command
    Then I should see a style analysis panel appear within 2 seconds
    And the panel should display complexity, formality, tone, and readability scores
    And each score should be between 0.0 and 1.0
    And the analysis should complete without blocking the editor
    """
    
    def test_style_analysis_endpoint_exists(self, client, test_tenant):
        """RED TEST: Style analysis endpoint should exist."""
        response = client.post(
            "/api/v1/style/analyze", 
            json={"text": "Sample text for analysis"},
            headers=TENANT_HEADER
        )
        # This should fail initially (RED)
        assert response.status_code != 404, "Style analysis endpoint should exist"
    
    def test_style_analysis_returns_required_scores(self, client, test_tenant):
        """RED TEST: Analysis should return complexity, formality, tone, readability."""
        sample_text = "This is a sample paragraph for style analysis. It contains multiple sentences with varying complexity."
        
        response = client.post(
            "/api/v1/style/analyze",
            json={"text": sample_text},
            headers=TENANT_HEADER
        )
        
        # This should fail initially (RED)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        assert "complexity" in data
        assert "formality" in data  
        assert "tone" in data
        assert "readability" in data
        
        # Check scores are between 0.0 and 1.0
        assert 0.0 <= data["complexity"] <= 1.0
        assert 0.0 <= data["formality"] <= 1.0
        assert 0.0 <= data["tone"] <= 1.0
        assert 0.0 <= data["readability"] <= 1.0
    
    def test_style_analysis_performance_requirement(self, client, test_tenant):
        """RED TEST: Analysis should complete within 2 seconds."""
        sample_text = "This is a longer sample paragraph for performance testing. " * 10
        
        start_time = time.time()
        response = client.post(
            "/api/v1/style/analyze",
            json={"text": sample_text},
            headers=TENANT_HEADER
        )
        end_time = time.time()
        
        # This should fail initially (RED)
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0, "Analysis should complete within 2 seconds"
    
    def test_style_analysis_handles_empty_text(self, client, test_tenant):
        """RED TEST: Should handle edge cases gracefully."""
        response = client.post(
            "/api/v1/style/analyze",
            json={"text": ""},
            headers=TENANT_HEADER
        )
        
        # Should return appropriate error or default values
        assert response.status_code in [400, 422], "Should handle empty text appropriately"

class TestStyleBasedTransformation:
    """
    BDD Scenario: Style-based text transformation
    Given I have selected text with a formal writing style
    When I choose "Transform to Casual Style" from the command palette
    Then the selected text should be replaced with a more casual version
    And the transformation should preserve the original meaning
    And the operation should complete within 3 seconds
    And I should be able to undo the transformation
    """
    
    def test_style_transformation_endpoint_exists(self, client, test_tenant):
        """RED TEST: Style transformation endpoint should exist."""
        response = client.post(
            "/api/v1/style/transform",
            json={
                "text": "This is a formal document requiring transformation.",
                "target_style": "casual",
                "preserve_meaning": True
            },
            headers=TENANT_HEADER
        )
        # This should fail initially (RED)
        assert response.status_code != 404, "Style transformation endpoint should exist"
    
    def test_style_transformation_returns_modified_text(self, client, test_tenant):
        """RED TEST: Should return transformed text."""
        formal_text = "I am writing to formally request your assistance in this matter."
        
        response = client.post(
            "/api/v1/style/transform",
            json={
                "text": formal_text,
                "target_style": "casual",
                "preserve_meaning": True
            },
            headers=TENANT_HEADER
        )
        
        # This should fail initially (RED)
        assert response.status_code == 200
        data = response.json()
        
        assert "transformed_text" in data
        assert "original_text" in data
        assert data["original_text"] == formal_text
        assert data["transformed_text"] != formal_text  # Should be different
        assert len(data["transformed_text"]) > 0
    
    def test_style_transformation_performance_requirement(self, client, test_tenant):
        """RED TEST: Transformation should complete within 3 seconds."""
        text = "This is a formal business communication that requires style transformation. " * 5
        
        start_time = time.time()
        response = client.post(
            "/api/v1/style/transform",
            json={
                "text": text,
                "target_style": "casual",
                "preserve_meaning": True
            },
            headers=TENANT_HEADER
        )
        end_time = time.time()
        
        # This should fail initially (RED)
        assert response.status_code == 200
        assert (end_time - start_time) < 3.0, "Transformation should complete within 3 seconds"

class TestBatchStyleConsistencyChecking:
    """
    BDD Scenario: Batch style consistency checking
    Given I have a document with multiple paragraphs
    When I run "Check Style Consistency" on the entire document
    Then I should see a report highlighting inconsistent sections
    And each inconsistency should show the conflicting style characteristics
    And I should get actionable suggestions for each issue
    And the report should be navigable with click-to-jump functionality
    """
    
    def test_batch_consistency_check_endpoint_exists(self, client, test_tenant):
        """RED TEST: Batch consistency check endpoint should exist."""
        document_text = [
            "This is a formal paragraph written in professional style.",
            "Hey, this is totally casual and relaxed, you know?",
            "Furthermore, we must consider the implications of this decision."
        ]
        
        response = client.post(
            "/api/v1/style/check-consistency",
            json={"paragraphs": document_text},
            headers=TENANT_HEADER
        )
        
        # This should fail initially (RED)
        assert response.status_code != 404, "Batch consistency check endpoint should exist"
    
    def test_consistency_check_identifies_inconsistencies(self, client, test_tenant):
        """RED TEST: Should identify style inconsistencies."""
        mixed_style_paragraphs = [
            "This is a formal academic paragraph with sophisticated vocabulary and complex sentence structures.",
            "Yo, this is super casual and uses slang!",
            "The aforementioned considerations necessitate a comprehensive analysis of the underlying factors."
        ]
        
        response = client.post(
            "/api/v1/style/check-consistency",
            json={"paragraphs": mixed_style_paragraphs},
            headers=TENANT_HEADER
        )
        
        # This should fail initially (RED)
        assert response.status_code == 200
        data = response.json()
        
        assert "inconsistencies" in data
        assert len(data["inconsistencies"]) > 0
        
        # Check each inconsistency has required fields
        for inconsistency in data["inconsistencies"]:
            assert "paragraph_index" in inconsistency
            assert "style_conflicts" in inconsistency
            assert "suggestions" in inconsistency
            assert "severity" in inconsistency
