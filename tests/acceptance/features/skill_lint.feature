Feature: Strict skill-schema lint (Spec 377 Slice 1)
  Beyond the SkillDoc shape `lint_skill` checks, the strict lint validates a 371
  Skill dict: per-type completeness (a typed skill carries its R15 required core),
  R1 (description is a 'Use when…' trigger), self-containment (every phase spells
  out non-empty instructions, A1), no-stub (no Tier-B placeholder reaches disk),
  and verb-resolves (an `invoke` binding names a live verb). Low-quality skills
  that used to pass now FAIL.

  Background:
    Given a confirmed intent

  Scenario: a typed skill missing its required core fails strict lint
    When I strict-lint the "thin-technique" sample skill
    Then the skill lint result is not ok
    And a skill-lint violation names the rule "schema"

  Scenario: a skill carrying a Tier-B stub fails strict lint
    When I strict-lint the "tier-b-stub" sample skill
    Then the skill lint result is not ok
    And a skill-lint violation names the rule "no-stub"

  Scenario: a phase without instructions fails self-containment
    When I strict-lint the "no-instructions" sample skill
    Then the skill lint result is not ok
    And a skill-lint violation names the rule "phase-self-contained"

  Scenario: a phase invoking an unknown verb fails verb-resolves
    When I strict-lint the "bad-verb" sample skill
    Then the skill lint result is not ok
    And a skill-lint violation names the rule "verb-resolves"

  Scenario: the committed pillars pass strict lint
    When I strict-lint every committed pillar
    Then every committed pillar passes strict lint

  # ── Spec 377 Slice 2 — the committed-skill gate (install + check-drift) ────────

  Scenario: the committed pillar source passes the strict lint gate
    When I run the committed-skill lint gate
    Then the committed-skill lint gate reports no failures

  Scenario: a committed pillar that fails strict lint is caught by the gate
    When I run the committed-skill lint gate over a lint-failing source
    Then the committed-skill lint gate flags the failing pillar

  Scenario: install generation is refused when a committed pillar fails strict lint
    When I generate the install with a lint-failing committed pillar
    Then install generation is refused
