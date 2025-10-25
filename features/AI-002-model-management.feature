Feature: Model Management
  As an admin, I need model management capabilities
  As a dev, I need version control for AI models
  
  Background:
    Given the Ollama service is running
    And the model management system is initialized
  
  Scenario Outline: Loading models
    Given I have model "<name>"
    When I load the model
    Then it should be available
    And properly versioned
    
    Examples:
      | name      |
      | llama2    |
      | mistral   |
  
  Scenario: Model version management
    Given I have a model "llama2:7b"
    When I check the model version
    Then I should see version information
    And version format should be valid
  
  Scenario: Model resource allocation
    Given I have multiple models loaded
    When I check resource usage
    Then memory usage should be within limits
    And CPU allocation should be tracked
  
  Scenario: Model availability check
    Given I have loaded model "llama2"
    When I check model availability
    Then the model should be listed as available
    And status should be "loaded"
  
  Scenario: Model unloading
    Given I have a loaded model "mistral"
    When I unload the model
    Then the model should not be available
    And resources should be freed
