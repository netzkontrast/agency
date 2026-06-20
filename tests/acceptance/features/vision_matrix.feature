Feature: Live vision-alignment matrix — derived from spec frontmatter
  The SPEC-VISION-ALIGNMENT matrix regenerates from each spec's
  `vision_goals:` + `status:` frontmatter (Spec 149) instead of being
  hand-maintained. Each Goal row carries computed shipped/partial/
  not-started counts, a shipped fraction, and a green/yellow/red status
  from named thresholds. The "three biggest gaps" recompute on every run.

  # ── goal status (computed, named thresholds) ───────────────────────────────

  Scenario: a goal is green when at least 80% of its specs are shipped
    Given a goal with 8 shipped, 1 partial, and 1 not-started spec
    When I build the goal row
    Then the shipped fraction is "0.80"
    And the goal status is "green"

  Scenario: goal status is classified from the shipped fraction by threshold
    Given shipped fractions "0.80", "0.50", "0.49"
    When I classify each fraction
    Then the statuses are "green", "yellow", "red"

  # ── biggest gaps (derived, recomputed) ─────────────────────────────────────

  Scenario: the three biggest gaps are the lowest shipped-fraction goals
    Given goals with shipped fractions "0.9", "0.2", "0.5", "0.1", "0.7"
    When I take the three biggest gaps
    Then the gap fractions in order are "0.1", "0.2", "0.5"

  # ── goal catalogue derived from GOALS.md (rule 8 — never hardcoded) ─────────

  Scenario: the goal catalogue is derived from GOALS.md
    When I parse the goals from the live GOALS.md
    Then each goal id maps to a non-empty title
    And the goal ids are contiguous starting from 1

  # ── status source: the TODO.md binding index (rule 4) ──────────────────────

  Scenario: spec status is sourced from the TODO verdict rows
    Given a TODO verdict listing "001" and "007" as shipped
    When I parse the status index
    Then "001" and "007" resolve to "shipped"
    And an unlisted spec id resolves to nothing

  # ── coverage invariant over the live tree ──────────────────────────────────

  Scenario: every spec with vision_goals lands in at least one goal row
    Given the matrix is built over the live Plan tree
    Then every spec with vision_goals appears in at least one goal row
    And no spec references a goal id absent from GOALS.md
