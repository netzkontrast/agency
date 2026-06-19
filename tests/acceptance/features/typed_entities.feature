Feature: typed entity projection — the Intent + Capability core (Spec 327)
  The four-concept core entities (Intent, Invocation, Agent) are mirrored ONE-WAY
  from the write-authoritative graph into explicit typed tables with foreign-key
  columns. The load-bearing invariant: every capability Invocation maps to the
  Intent it serves (serves_intent_id NOT NULL) and names the Agent that ran it —
  "all capabilities mapped into intents" as a typed, join-able fact.

  Background:
    Given a fresh agency engine

  Scenario: core entities are mirrored into their typed tables keyed by node id
    When I capture and confirm an intent and invoke a capability that serves it
    Then the intent has a typed Intent row with the same id
    And the invocation has a typed Invocation row with the same id

  Scenario: every capability invocation maps to the intent it serves
    When I capture and confirm an intent and invoke a capability that serves it
    Then no typed Invocation row has a null serves_intent_id
    And every typed Invocation serves_intent_id resolves to a typed Intent row

  Scenario: serves_intent_id tracks the SERVES edge
    When I capture and confirm an intent and invoke a capability that serves it
    Then the invocation's serves_intent_id equals the target of its SERVES edge

  Scenario: the agent performer is captured by foreign key
    When I capture an intent and invoke a capability performed by an agent
    Then the invocation's agent_id resolves to a typed Agent row

  Scenario: PARENT_INTENT is mirrored as a typed foreign key
    When I capture a child intent under a parent intent
    Then the child Intent row's parent_intent_id equals the parent id

  Scenario: the typed projection is one-way and failure-isolated
    When a typed-projection write fails while recording an intent
    Then the authoritative graph still has the intent node

  Scenario: enum values are enforced from the ontology
    When I record an intent with an owner that is not in the ontology
    Then the record is rejected

  Scenario: superseding a core node keeps it in the typed projection
    When an invocation serving an intent is superseded
    Then the live invocation still serves that intent in the typed projection
