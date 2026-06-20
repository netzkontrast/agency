Feature: discover.clarity — the Intent readiness score + gate input (Spec 322)
  Scores a captured Intent's clarity as the normalized sum of five independent
  readiness signals, each COMPUTED from the live discovery graph. Read-only — the
  confirm gate reads {score, missing, ready} to refuse work against a vague Intent.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a freshly interviewed draft scores low and is not ready
    When I interview and score the resulting draft
    Then the clarity score is between 0 and 1
    And the draft is not ready
    And missing lists the unsatisfied readiness signals

  Scenario: an incomplete interview draft lacks the triple signal
    When I interview vaguely and score the resulting draft
    Then the has_triple signal is false

  Scenario: satisfying signals raises the score and flips ready
    When I interview and score the resulting draft
    And I add a measurable acceptance criterion and a scope boundary to the draft
    And I re-score the draft
    Then the clarity score increased
    And the draft is now ready
    And scoring created no extra acceptance criterion

  # ── clarity_gate (Spec 322 Slice 2) ──────────────────────────────────────

  Scenario: clarity_gate refuses a below-threshold intent without override
    Given an open lifecycle
    When I interview a vague intent and run clarity_gate without override
    Then clarity_gate returns GATE_FAILED

  Scenario: clarity_gate passes with an override token despite low score
    Given an open lifecycle
    When I interview a vague intent and run clarity_gate with an override token
    Then clarity_gate passes and records the override

  Scenario: clarity_gate passes when the intent is already ready
    Given an open lifecycle
    When I satisfy all signals and run clarity_gate
    Then clarity_gate passes without override

  Scenario: clarity_gate threshold is a documented budget
    Given an open lifecycle
    When I interview a vague intent and run clarity_gate with min_clarity 0.0
    Then clarity_gate passes without override
