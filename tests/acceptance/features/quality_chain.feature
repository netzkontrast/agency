Feature: the judgment subagent walks the Brooks review chain (Spec 380 §judgment)

  The judgment pass is fulfilled by a SUBAGENT (model_hint="subagent"). Rather than
  a flat risk-dump, the subagent is driven by the vendored, mode-aware Brooks REVIEW
  CHAIN — the ordered review methodology (scope calibration → step-ordered risk scans
  → severity tiers → fix order → restraint) ported from brooks-lint. The chain reaches
  the subagent inside the `llm_delegate` envelope's prompt, so when no backend is wired
  the returned envelope carries the active mode's chain. The chain is mode-aware: the
  PR-review chain ends in a Quick Test Check; the architecture chain has no test check
  and adds a Conway's Law step instead. Every risk code the chain names is a real
  decay-risks code (grounding — rule 8).

  Background:
    Given an engine and confirmed intent

  Scenario: the review-mode delegate carries the PR-review chain
    Given a fixture file and no inference backend
    When analyze.review runs in "review" mode with no completion
    Then the delegate prompt contains the chain title "PR Review"
    And the delegate prompt contains the chain step "Quick Test Check"
    And the delegate prompt contains the chain methodology marker "recommended fix order"

  Scenario: the chain is mode-aware — audit differs from review
    Given a fixture file and no inference backend
    When analyze.review runs in "audit" mode with no completion
    Then the delegate prompt contains the chain title "Architecture Audit"
    And the delegate prompt contains the chain step "Conway"
    And the delegate prompt excludes the chain step "Quick Test Check"

  Scenario: every chain risk-code is grounded in the decay-risks registry
    Then every review-chain step code is a real decay-risk code
    And every quality mode has a non-empty chain
