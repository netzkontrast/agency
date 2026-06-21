Feature: Loop spec + emission — Spec 368 (graph → portable artefacts)
  The graph is the source of truth; compile projects the spine loop into looper's
  loop.resolved.json shape (the contract the runner reads), and emit renders the
  portable workspace as anchored document files (round-trippable, Spec 292).

  Background:
    Given a fresh agency engine in code-mode

  Scenario: compile produces a resolved spec that conforms to the schema
    Given a fully-specified loop on the spine
    When I compile the loop
    Then the resolved spec is valid
    And it contains criteria_by_id and council_by_id with the inlined judge rubric

  Scenario: compile resolves every council member to an argv invocation
    Given a fully-specified loop on the spine
    When I compile the loop
    Then every council member invoke is an argv array, never a shell string

  Scenario: emit writes the portable workspace with anchored markdown
    Given a fully-specified loop on the spine
    When I emit the loop to a temp directory
    Then loop.yaml, loop.resolved.json, LOOP.md, RUN_IN_SESSION.md, README.md and loop-workspace exist
    And each rendered markdown carries an agency-node anchor on its first line

  Scenario: compile of an under-specified loop returns findings, not a crash
    Given an under-specified loop with only a reviewer member
    When I compile the loop
    Then it is not valid and returns a reviewer-only-rule finding
