Feature: VSC-006 Collaboration
  As a content creator working in a team
  I want to collaborate with others in real-time on documents
  So that we can work together efficiently and see each other's contributions

  Background:
    Given the PseudoScribe extension is installed and activated
    And the backend API is running and accessible
    And I have a document open in VSCode
    And collaboration features are enabled

  Scenario: Multi-user document editing with real-time sync
    Given multiple users are connected to the same document
    When one user makes changes to the document
    Then the changes should be synchronized to all other users within 200ms
    And each user should see the changes reflected in their editor
    And the document state should remain consistent across all users
    And no changes should be lost during synchronization

  Scenario: User presence awareness and cursor visibility
    Given I am in a shared editing session
    When other users are actively editing the document
    Then I should see visual indicators of their presence
    And I should see their cursors with unique colors and labels
    And I should see their current selection ranges
    And the presence indicators should update in real-time
    And inactive users should be shown as "away" after 30 seconds

  Scenario: Conflict resolution for simultaneous edits
    Given two users are editing the same text region simultaneously
    When both users make conflicting changes to overlapping text
    Then the system should detect the conflict automatically
    And both users should be notified of the conflict
    And a conflict resolution interface should be presented
    And users should be able to choose which changes to keep
    And the resolution should be applied consistently across all sessions

  Scenario: Real-time collaborative style suggestions
    Given multiple users are collaborating on a document
    When one user receives a style suggestion
    Then other users should see the suggestion as well
    And users should be able to vote on or discuss suggestions
    And accepted suggestions should be applied for all users
    And the suggestion history should be shared across the session

  Scenario: Session management and user permissions
    Given I want to start a collaborative session
    When I create a new collaboration session
    Then I should be able to invite other users via email or link
    And I should be able to set permissions (read-only, edit, admin)
    And users should be able to join the session seamlessly
    And I should be able to manage user permissions during the session
    And users should be notified when permissions change

  Scenario: Document version control and history
    Given multiple users have been editing a document
    When I want to review the editing history
    Then I should see a timeline of all changes with user attribution
    And I should be able to see who made each change and when
    And I should be able to revert to any previous version
    And the version history should include style suggestions and acceptances
    And I should be able to branch from any historical version

  Scenario: Offline collaboration and sync recovery
    Given I am working in a collaborative session
    When my internet connection is temporarily lost
    Then I should be able to continue editing locally
    And my changes should be queued for synchronization
    And when connection is restored, changes should sync automatically
    And conflicts with changes made while offline should be resolved
    And no work should be lost due to connectivity issues

  Scenario: Performance requirements for collaboration
    Given I am in a collaborative session with up to 10 users
    When multiple users are actively editing
    Then change synchronization should complete within 200ms
    And cursor position updates should be near-instantaneous (<50ms)
    And the extension should maintain responsive performance
    And memory usage should not exceed 100MB additional overhead
    And network bandwidth should be optimized for minimal data transfer

  Scenario: Integration with existing VSCode features
    Given I am using VSCode's built-in features during collaboration
    When I use features like find/replace, multi-cursor, or extensions
    Then collaborative features should not interfere with VSCode functionality
    And my actions should be synchronized appropriately with other users
    And VSCode's native undo/redo should work correctly in collaborative mode
    And other extensions should continue to function normally

  Scenario: Security and privacy in collaborative sessions
    Given I am sharing a document with sensitive content
    When I start a collaborative session
    Then all communication should be encrypted end-to-end
    And user authentication should be required to join sessions
    And I should be able to control who can access the document
    And session data should not be stored permanently without consent
    And users should be able to leave sessions cleanly without data retention
