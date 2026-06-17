Feature: mode capability — behavioral modes, first-class (Spec 295)
  A native reimplementation of SuperClaude's behavioral modes — postures that
  change how the agent works, selected decidably and recorded as provenance.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the roster lists the five behavioral modes
    When I list the modes
    Then the mode roster has five modes including brainstorming and introspection

  Scenario: detect ranks brainstorming for a vague exploratory request
    When I detect the mode for "I'm not sure, maybe we could explore some ideas"
    Then the top detected mode is "brainstorming"

  Scenario: activate auto-resolves introspection and records provenance
    When I activate the auto mode for "reflect on why did this fail unexpected"
    Then the activated mode is "introspection"
    And activation records a ModeActivation node serving the intent
    And the activated mode returns behavioral rules

  Scenario: activate falls back to brainstorming when nothing matches
    When I activate the auto mode for "xyzzy"
    Then the activated mode is "brainstorming"
