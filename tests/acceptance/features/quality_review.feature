Feature: Spec 380 — Six quality modes as walkable skills + develop.review seam

  The brooks-lint port's "integrate linting into develop" half: six walkable
  disciplines (quality-review/audit/debt/test/health/sweep) on develop.ontology.skills,
  plus develop.review (transform, READ-ONLY) and develop.remediate (effect, writes).
  The shared analyze/_review.py core is the single engine both the interactive
  developer and the headless CI actor drive — their pause behaviour differs, not
  the logic. The Iron Law gate is a DECIDABLE PREDICATE over Finding fields, not
  agent self-assertion (Wiegers fix). Decidable + judgment findings merge — one
  Finding per (risk_code, file, line), never double-counted (Hohpe fix).

  Background:
    Given an engine and confirmed intent

  # ── pure-function tests (no engine needed) ─────────────────────────────────

  Scenario: Iron Law gate fails when a brooks finding has empty consequence or remedy
    Given a brooks Finding with risk_code "R1" and empty remedy
    When the iron_law_passed predicate is evaluated
    Then it returns False

  Scenario: Iron Law gate fails when consequence is empty
    Given a brooks Finding with risk_code "R1" and empty consequence
    When the iron_law_passed predicate is evaluated
    Then it returns False

  Scenario: Iron Law gate passes when all brooks findings are complete
    Given a brooks Finding with risk_code "R1", consequence, and remedy filled
    When the iron_law_passed predicate is evaluated
    Then it returns True

  Scenario: Iron Law gate ignores decidable-only findings (empty risk_code)
    Given a decidable-only Finding with no risk_code but no consequence or remedy
    When the iron_law_passed predicate is evaluated
    Then it returns True because only brooks findings (non-empty risk_code) are checked

  Scenario: Decidable and judgment passes merge — one finding per span
    Given a decidable R1 Finding for file "app.py" line 10
    And a judgment R1 Finding for the same file and line with a sharper remedy
    When merge_findings is called with the decidable and judgment lists
    Then there is exactly one R1 Finding in the output
    And the output Finding carries the judgment's sharper remedy

  Scenario: Judgment creates a new finding when no decidable spans the location
    Given a decidable R1 Finding for file "app.py" line 10
    And a judgment R1 Finding for file "app.py" line 50 (different span)
    When merge_findings is called with the decidable and judgment lists
    Then there are exactly two R1 Findings in the output

  Scenario: classify_remedy returns "safe" for local mechanical fixes
    Given a Finding whose remedy is "extract constant to a named variable"
    When classify_remedy is called
    Then the result is "safe"

  Scenario: classify_remedy returns "risky" for structural changes
    Given a Finding whose remedy is "invert dependency direction"
    When classify_remedy is called
    Then the result is "risky"

  # ── skill registry + verb metadata ─────────────────────────────────────────

  Scenario: Six quality modes are discoverable as walkable skills
    When I look at the develop capability's skill registry
    Then "quality-review" is a registered walkable skill
    And "quality-audit" is a registered walkable skill
    And "quality-debt" is a registered walkable skill
    And "quality-test" is a registered walkable skill
    And "quality-health" is a registered walkable skill
    And "quality-sweep" is a registered walkable skill

  Scenario: quality-review has the required phase structure
    When I inspect the quality-review skill
    Then it has a phase named "scope"
    And it has a phase named "decidable"
    And it has a phase named "judgment"
    And it has a phase named "score-report"

  Scenario: quality-sweep additionally has a remedy phase
    When I inspect the quality-sweep skill
    Then it has a phase named "scope"
    And it has a phase named "decidable"
    And it has a phase named "judgment"
    And it has a phase named "score-report"
    And it has a phase named "remedy"

  Scenario: develop.review is role=transform (read-only, no fix param)
    When I inspect develop.review's verb metadata
    Then its role is "transform"

  Scenario: develop.remediate is role=effect (mutating)
    When I inspect develop.remediate's verb metadata
    Then its role is "effect"

  # ── verb behaviour ──────────────────────────────────────────────────────────

  Scenario: develop.review returns a diagnosis result
    When I call develop.review with mode "review" and scope "."
    Then the result contains scope_line, findings, iron_law_passed, and mode
    And mode is "review"

  Scenario: analyze.review is the headless twin — never pauses
    When I call analyze.review with mode "review" and path "."
    Then the result contains headless=True
    And risky remedies are reported in gated
    And the result contains iron_law_passed
