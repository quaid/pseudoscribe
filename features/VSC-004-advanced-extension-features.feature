Feature: VSC-004 Advanced Extension Features
  As a content creator using VSCode
  I want advanced text transformation and style analysis capabilities
  So that I can efficiently create high-quality, consistent content

  Background:
    Given the PseudoScribe extension is installed and activated
    And the backend API is running and accessible
    And I have a document open in VSCode

  Scenario: Real-time style analysis of selected text
    Given I have selected a paragraph of text in my document
    When I trigger the "Analyze Style" command
    Then I should see a style analysis panel appear within 2 seconds
    And the panel should display complexity, formality, tone, and readability scores
    And each score should be between 0.0 and 1.0
    And the analysis should complete without blocking the editor

  Scenario: Style-based text transformation
    Given I have selected text with a formal writing style
    When I choose "Transform to Casual Style" from the command palette
    Then the selected text should be replaced with a more casual version
    And the transformation should preserve the original meaning
    And the operation should complete within 3 seconds
    And I should be able to undo the transformation

  Scenario: Batch style consistency checking
    Given I have a document with multiple paragraphs
    When I run "Check Style Consistency" on the entire document
    Then I should see a report highlighting inconsistent sections
    And each inconsistency should show the conflicting style characteristics
    And I should get actionable suggestions for each issue
    And the report should be navigable with click-to-jump functionality

  Scenario: Style profile comparison between documents
    Given I have two documents open in different tabs
    When I select "Compare Document Styles" from the extension menu
    Then I should see a side-by-side style comparison
    And the comparison should show overall similarity score
    And it should highlight specific differences in complexity, formality, tone
    And I should be able to apply one document's style to the other

  Scenario: Custom style template creation
    Given I have analyzed text that represents my desired style
    When I choose "Save as Style Template" 
    And I provide a template name "Technical Blog Post"
    Then the style profile should be saved for future use
    And I should be able to apply this template to other text
    And the template should appear in my style template library

  Scenario: Contextual style suggestions
    Given I am writing in a document tagged as "professional email"
    When I type text that doesn't match the expected style
    Then I should see inline suggestions appear as I type
    And the suggestions should be non-intrusive (underlines or margin indicators)
    And I should be able to accept suggestions with a single click
    And I should be able to dismiss suggestions without affecting my workflow

  Scenario: Performance requirements for large documents
    Given I have a document with more than 10,000 words
    When I perform any style analysis operation
    Then the operation should complete within 5 seconds
    And the extension should not freeze the VSCode interface
    And memory usage should not exceed 100MB above baseline
    And I should see a progress indicator for operations taking longer than 1 second

  Scenario: Integration with existing VSCode features
    Given I am using VSCode's built-in spell checker
    When I run PseudoScribe style analysis
    Then both tools should work together without conflicts
    And style suggestions should not interfere with spell check underlines
    And I should be able to use both features simultaneously
    And the extension should respect VSCode's theme and UI conventions

  Scenario: Offline capability for basic features
    Given the backend API is temporarily unavailable
    When I try to use cached style templates
    Then basic style checking should still work with local rules
    And I should see a clear indicator that advanced features are unavailable
    And the extension should gracefully degrade functionality
    And I should be notified when full functionality is restored

  Scenario: Multi-language document support
    Given I have a document containing both English and Spanish text
    When I run style analysis on the mixed-language content
    Then the extension should detect language boundaries
    And it should apply appropriate style rules for each language section
    And the analysis should handle code-switching appropriately
    And I should get language-specific style recommendations
