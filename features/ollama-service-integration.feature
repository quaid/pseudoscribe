Feature: Ollama Service Integration
  As a developer and SRE
  I need Ollama service integration with health monitoring
  So that I can provide reliable AI capabilities with proper observability

  Background:
    Given I have access to the PseudoScribe API
    And I have proper authentication headers

  Scenario: Service configuration and setup
    Given I have Ollama installed and configured
    When I check the Ollama service configuration
    Then the service should be properly configured
    And basic operations should work
    And configuration should be validated

  Scenario: Health check endpoints
    Given the Ollama service is running
    When I check the health status via API
    Then I should receive a health status response
    And the response should include service availability
    And the response should include basic metrics
    And the response should be under 200ms

  Scenario: Service monitoring integration
    Given the Ollama service is running
    When I request monitoring metrics
    Then I should see Ollama-specific health metrics
    And I should see resource utilization data
    And metrics should integrate with performance monitoring
    And SLA compliance should be tracked

  Scenario: Model availability check
    Given the Ollama service is configured
    When I check available models
    Then I should get a list of available models
    And each model should have metadata
    And the response should be properly formatted

  Scenario: Service error handling
    Given the Ollama service is unavailable
    When I make API requests to Ollama endpoints
    Then I should receive appropriate error responses
    And errors should be properly logged
    And fallback behavior should be triggered

  Scenario: Performance SLA monitoring
    Given the Ollama service is running
    When I monitor service performance
    Then response times should be tracked
    And SLA violations should be detected
    And alerts should be generated for degradation
    And metrics should be stored for analysis
