Feature: Skill schema v2 — the layered, type-classified Phase + Skill model (Spec 371)
  The v2 schema enriches Phase with inline content (goal / instructions /
  example / done_when / freedom — A1/A2/R8/R9) and Skill with a best-practices
  structure (type / owner / description / overview / when_to_use / when_not /
  references / common_mistakes / examples / eval_scenarios / source_stamp —
  R1/R15/A4/A6). Validation is LAYERED: a small required core per type, the
  rest optional. Back-compat is the iron invariant — every legacy skill
  (no `type`) parses exactly as before, and every live ontology skill stays clean.

  # ── Phase content fields (A1/A2/R8/R9) ────────────────────────────────────────

  Scenario: a phase carries inline instructions and round-trips losslessly (A1/A2)
    When I parse a phase with goal, instructions, example, done_when and freedom
    Then the v2 phase parse succeeds
    And the phase round-trips its instructions and freedom

  Scenario: a phase with an unknown freedom level fails with a typed code (R8)
    When I parse a phase with freedom "rigid"
    Then the v2 phase parse fails with code "phase_unknown_kind" mentioning "freedom"

  # ── Skill type classification (R15) ───────────────────────────────────────────

  Scenario: a typed discipline skill with its required core parses
    When I parse a discipline skill with description and common_mistakes
    Then the v2 skill parse succeeds with type "discipline"

  Scenario: a discipline skill missing its rationalization table fails (R13/R15)
    When I parse a discipline skill with no common_mistakes
    Then the v2 skill parse fails with code "skill_parse_invalid" mentioning "common_mistakes"

  Scenario: a technique skill requires phases (R15 Technique)
    When I parse a technique skill with no phases
    Then the v2 skill parse fails with code "skill_parse_invalid" mentioning "phases"

  Scenario: a reference skill requires references (R15 Reference)
    When I parse a reference skill with no references
    Then the v2 skill parse fails with code "skill_parse_invalid" mentioning "references"

  Scenario: a pattern skill requires an overview (R15 Pattern)
    When I parse a pattern skill with no overview
    Then the v2 skill parse fails with code "skill_parse_invalid" mentioning "overview"

  Scenario: an unknown skill type fails with a typed code
    When I parse a skill with type "tutorial"
    Then the v2 skill parse fails with code "skill_parse_invalid" mentioning "type"

  Scenario: an unknown owner fails with a typed code (A6)
    When I parse a skill with owner "vendor"
    Then the v2 skill parse fails with code "skill_parse_invalid" mentioning "owner"

  # ── rich structure round-trips (R1/R9/A4/A6) ──────────────────────────────────

  Scenario: a full typed skill round-trips every v2 field
    When I parse a full capability skill with all v2 fields
    Then the v2 skill parse succeeds with type "capability"
    And the skill round-trips description, overview, references and examples

  # ── back-compat (the iron invariant) ──────────────────────────────────────────

  Scenario: a legacy skill with no type still parses (back-compat)
    When I parse a legacy skill with only name kind and phases
    Then the v2 skill parse succeeds with no type

  Scenario: every live ontology skill still parses under the v2 boundary
    Given a fresh agency engine in code-mode
    Then every live skill parses clean under the v2 schema

  # ── R1–A7 coverage + the published JSON schemas ───────────────────────────────

  Scenario: the Skill and Phase schemas express a field for every R1–A7 rule
    Then every best-practices rule maps to a schema field

  Scenario: the published JSON schemas declare the v2 surface
    Then the phase JSON schema declares the inline content fields
    And the skill JSON schema declares every skill type and the v2 fields
