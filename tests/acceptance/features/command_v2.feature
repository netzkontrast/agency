Feature: Command v2 — curated, launch-not-stub slash commands (Spec 376)
  The generated /agency-<slug> commands are a CURATED set — one per discipline
  (walkable method) and one per pillar (concept) — instead of a top-N alpha cap of
  near-identical "walk the skill" stubs. Each body LAUNCHES its skill: a discipline
  invokes the skill walk; a pillar points at its self-contained concept SKILL.md.
  Rendered from the live skill schema (371) so command and skill never drift.

  Scenario: the per-skill command set is exactly the discipline and pillar skills
    When the install files are generated
    Then the per-skill command slugs are exactly the discipline and pillar skills
    And no per-skill command is generated for a non-curated skill kind

  Scenario: each discipline command launches its skill walk
    When the install files are generated
    Then every discipline command body invokes the skill walk naming its real skill

  Scenario: each pillar command points at its concept skill
    When the install files are generated
    Then every pillar command body points at its concept SKILL.md

  Scenario: command bodies are not identical stubs
    When the install files are generated
    Then no two per-skill command bodies are byte-identical

  Scenario: the curated command set is deterministic (A7)
    When the install files are generated
    And the install files are generated again
    Then the two command sets are identical
