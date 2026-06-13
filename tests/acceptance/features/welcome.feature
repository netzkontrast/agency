Feature: agency_welcome onboarding tool (Spec 029 / 030)
  agency_welcome is a pure introspective tool that returns the live capability
  tier, DB path, state-aware next steps, and the bootstrap example — all in one
  sub-2 KB payload. It must never mutate the graph.

  Scenario: fresh graph returns "fresh" state with onboarding steps
    Given a fresh agency engine in code-mode
    When I call agency_welcome
    Then the state is "fresh"
    And the intents_count is 0
    And the next steps mention intent_bootstrap or agency_install

  Scenario: welcome payload carries all required onboarding fields
    Given a fresh agency engine in code-mode
    When I call agency_welcome
    Then the payload contains bootstrap_example with intent_bootstrap
    And the payload contains install_example with agency_install
    And the payload contains a sorted capability list including plugin and reflect
    And the payload carries a db_path
    And the payload carries a next list with at least 2 steps
    And the payload carries a state field

  Scenario: capability list is in sorted order
    Given a fresh agency engine in code-mode
    When I call agency_welcome
    Then the capabilities list is sorted

  Scenario: welcome is pure read — no graph mutations
    Given a fresh agency engine in code-mode
    When I call agency_welcome twice
    Then no Intent Invocation or Reflection nodes were created

  Scenario: in-progress state surfaces last intent
    Given an engine with an existing confirmed intent
    When I call agency_welcome
    Then the state is "in_progress"
    And the intents_count is 1
    And the last_intent is the confirmed intent id
    And the next steps mention search or memory_graph_provenance

  Scenario: welcome payload stays within the per-capability token budget
    Given a fresh agency engine in code-mode
    When I call agency_welcome
    Then the payload byte size is within 150 bytes per capability plus 1000

  Scenario: welcome reports the database path even when the DB file is missing
    Given an engine whose AGENCY_DB points at a non-existent path
    When I call agency_welcome
    Then the db_path contains session.db

  Scenario: welcome prefix keys exclude per-call state
    Given a fresh agency engine in code-mode
    When I call agency_welcome
    Then the _prefix_keys field is present
    And the prefix does not contain per-call state keys like state or intents_count
    And the prefix contains capability_set_hash and schema_version

  Scenario: welcome prefix bytes are stable across repeated calls
    Given a fresh agency engine in code-mode
    When I call agency_welcome twice
    Then the prefix bytes are identical across both calls
