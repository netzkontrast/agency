Feature: ADR spec→decision extraction + ready predicate (Spec 356 Slice 1)

  When a spec lands in /open its key decisions are extracted into `proposed`
  Decision drafts that REFINE the spec (decidable-first — no API key); the
  /open→/inprogress predicate `spec_decisions_ready` is true only once every
  extracted decision is approved (355). A spec with no decisions does NOT
  vacuously pass — the owner must clear it explicitly.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: extract previews evidence-anchored WH(Y) candidates with no API key
    Given an ingested spec with two design decisions
    When I extract decisions from it as a preview
    Then at least two candidates are returned
    And every candidate has an evidence span

  Scenario: applying extraction drafts decisions that REFINE the spec, idempotently
    Given an ingested spec with two design decisions
    When I apply extraction to draft the decisions
    And I apply extraction again
    Then the spec has exactly two decisions

  Scenario: the spec is not ready until every extracted decision is approved
    Given an ingested spec with two design decisions
    When I apply extraction to draft the decisions
    Then the spec is not ready to advance
    When I approve every decision of the spec as owner "owner-alice"
    Then the spec is ready to advance

  Scenario: a spec with no decisions does not vacuously pass the gate
    Given an ingested spec with no decisions
    When I check whether the spec is ready
    Then the spec is not ready to advance
    And the not-ready reason is "no-decisions"

  # ── Slice 2 — architecture-hint loading ──────────────────────────────────────

  Scenario: hints are empty until decisions are approved
    Given an ingested spec with two design decisions
    When I apply extraction to draft the decisions
    And I load the implementation hints with budget 2000
    Then the hints are empty

  Scenario: hints return a token-bounded block over approved decisions
    Given an ingested spec with two design decisions
    When I apply extraction to draft the decisions
    And I approve every decision of the spec as owner "owner-alice"
    And I load the implementation hints with budget 2000
    Then at least one hint is returned
    And the returned tokens are within budget
