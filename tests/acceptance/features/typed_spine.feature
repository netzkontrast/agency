Feature: typed Lifecycle state + the Memory provenance spine (Spec 329)
  The interweave's remaining concepts become typed: Lifecycle (the task/session
  state, woven to its Intent) and Memory (the Artefact + the general typed Edge
  table). The hot FK columns cover the constantly-traversed relationships; the
  Edge table mirrors EVERY typed edge so any provenance question is a typed query,
  not just the hot four.

  Background:
    Given a fresh agency engine

  Scenario: an artefact's provenance is captured by foreign key
    When an invocation serving an intent produces an artefact serving it
    Then the artefact's produced_by_id resolves to that invocation
    And the artefact's serves_intent_id resolves to that intent

  Scenario: an intent-produced artefact has no invocation producer
    When an intent directly produces an artefact
    Then the artefact's produced_by_id is null

  Scenario: a lifecycle state weaves to the intent it serves
    When a lifecycle serving an intent is recorded
    Then the lifecycle state's serves_intent_id resolves to that intent

  Scenario: every graph edge is mirrored into the typed Edge spine
    When an invocation serving an intent produces an artefact serving it
    Then every live graph edge has a matching typed Edge row

  Scenario: a new link adds exactly one typed Edge row
    When I record two nodes and link them once
    Then the typed Edge count increased by exactly one
    And the new Edge row carries the src, dst, and rel

  Scenario: the Edge spine is one-way and failure-isolated
    When an Edge-spine write fails while linking
    Then the authoritative graph still has the edge
