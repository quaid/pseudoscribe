Feature: VSC-005 Live Suggestions
  As a content creator using VSCode
  I want real-time suggestions while typing
  So that I can improve my writing as I work without interrupting my flow

  Background:
    Given the PseudoScribe extension is installed and activated
    And the backend API is running and accessible
    And I have a document open in VSCode
    And live suggestions are enabled

  Scenario: Real-time content analysis while typing
    Given I am typing in a document
    When I add new content to my document
    Then the content should be analyzed within 500ms
    And the analysis should not block my typing
    And the analysis should run in the background
    And I should see no performance degradation

  Scenario: Display non-intrusive style suggestions
    Given I have typed text that doesn't match my style profile
    When the analysis detects style inconsistencies
    Then I should see subtle visual indicators (underlines or margin hints)
    And the suggestions should not interrupt my typing flow
    And the indicators should be visually distinct from spell check
    And I should be able to continue typing without distraction

  Scenario: Accept suggestions with single click
    Given I have style suggestions displayed
    When I click on a suggestion indicator
    Then I should see the suggested improvement
    And I should be able to accept it with one click
    And the text should be updated immediately
    And the suggestion indicator should disappear
    And my cursor should remain in a logical position

  Scenario: Dismiss suggestions without workflow interruption
    Given I have style suggestions displayed
    When I choose to dismiss a suggestion
    Then the suggestion should disappear immediately
    And no further suggestions should appear for that text segment
    And my typing workflow should remain uninterrupted
    And I should be able to continue writing normally

  Scenario: Contextual suggestions based on document type
    Given I am writing in a document tagged as "technical documentation"
    When I type content that doesn't match technical writing style
    Then I should receive suggestions appropriate for technical writing
    And the suggestions should focus on clarity and precision
    And informal language should be flagged for improvement
    And technical terminology should be validated

  Scenario: Performance requirements for live suggestions
    Given I am typing continuously in a document
    When live suggestions are active
    Then content analysis should complete within 500ms
    And UI updates should be smooth and non-blocking
    And memory usage should not increase beyond 50MB
    And CPU usage should remain under 10% during typing
    And there should be no typing lag or delays

  Scenario: Suggestion priority and relevance
    Given I have multiple potential style improvements
    When suggestions are displayed
    Then the most important suggestions should be prioritized
    And minor stylistic preferences should be de-emphasized
    And suggestions should be contextually relevant
    And I should not be overwhelmed with too many indicators

  Scenario: Integration with existing VSCode features
    Given I am using VSCode with spell check and other extensions
    When PseudoScribe live suggestions are active
    Then suggestions should not conflict with spell check underlines
    And different types of indicators should be visually distinct
    And performance should not be impacted by other extensions
    And all features should work harmoniously together

  Scenario: Adaptive suggestion frequency
    Given I am in a focused writing session
    When I consistently dismiss certain types of suggestions
    Then the system should learn my preferences
    And similar suggestions should appear less frequently
    And the adaptation should be session-specific
    And I should maintain control over suggestion types

  Scenario: Offline graceful degradation
    Given the backend API becomes unavailable
    When I continue typing in my document
    Then basic cached suggestions should still work
    And I should see a subtle indicator that full features are unavailable
    And the extension should not show error messages during typing
    And functionality should restore automatically when connection returns
