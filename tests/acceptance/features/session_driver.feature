Feature: Session driver verbs — session lifecycle and mode management (Spec 114)
  The plugin drives sessions via develop.session_init / session_check / mode_select,
  reflect.synthesize_session, dogfood.record_decision / boundary_use_audit.
  Observable behaviour: graph nodes minted, SERVES edges, mode recorded.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── session_init ────────────────────────────────────────────────────────────

  Scenario: session_init mints a SessionLifecycle that SERVES the intent
    When I call develop.session_init with mode_hint brainstorming
    Then the result has a session_lifecycle_id starting with sessionlifecycle:
    And the result mode is brainstorming
    And the result has a suggested_first_verb
    And the SessionLifecycle SERVES the intent in the graph

  Scenario: session_init records the supplied mode_hint
    When I call develop.session_init with mode_hint spec-authoring
    Then the result mode is spec-authoring

  # ── session_check ────────────────────────────────────────────────────────────

  Scenario: session_check reads an explicit lifecycle by id
    Given a session lifecycle has been initialised with mode brainstorming
    When I call develop.session_check with that session_lifecycle_id
    Then the session_check result mode is brainstorming
    And the session_check result has a session_lifecycle_id

  Scenario: session_check falls back to most-recent when no id given
    Given a session lifecycle has been initialised with mode brainstorming
    When I call develop.session_check with no session_lifecycle_id
    Then the session_check result mode is brainstorming

  # ── mode_select ────────────────────────────────────────────────────────────

  Scenario: mode_select records a ModeShift and updates the lifecycle mode
    Given a session lifecycle has been initialised with mode brainstorming
    When I call develop.mode_select with new_mode coding on that lifecycle
    Then the mode_select result to_mode is coding
    And a ModeShift node is recorded in the graph

  # ── synthesize_session ──────────────────────────────────────────────────────

  Scenario: synthesize_session produces an Artefact and archives the lifecycle
    Given a session lifecycle has been initialised with mode brainstorming
    When I call reflect.synthesize_session with that session_lifecycle_id
    Then the synthesize result contains a session-reflection artefact

  # ── dogfood.record_decision ─────────────────────────────────────────────────

  Scenario: record_decision creates a DecisionRecord that SERVES the intent
    When I call dogfood.record_decision with subject "use A" and decision "accept" and rationale "reason"
    Then the decision result has a decision_id
    And the DecisionRecord SERVES the intent in the graph

  # ── dogfood.boundary_use_audit ──────────────────────────────────────────────

  Scenario: boundary_use_audit returns empty breakdown when no uses are recorded
    When I call dogfood.boundary_use_audit
    Then the audit result has a bypass_count
    And the audit tool breakdown is empty

  # ── session_resume ──────────────────────────────────────────────────────────

  Scenario: session_resume finds the active lifecycle for the intent
    Given a session lifecycle has been initialised with mode brainstorming
    When I call develop.session_resume
    Then the resume result has a session_lifecycle_id
    And the resume result status is active
