Feature: Capability skill migration — phase-fill + A6 (Spec 378 Slice 1)
  The frugal migration: keep capability skills DERIVED (rule 2), but author real
  inline phase `instructions` for the high-value disciplines so they are
  self-contained (A1) — the capability-authored richer skill data (A6) the v2
  schema validates the same as an auto-derived one. This slice enriches the core
  develop disciplines (debug · verify · plan · execute), joining `tdd` (the 372
  exemplar) as fully self-contained.

  Background:
    Given a confirmed intent

  Scenario: the core develop disciplines are self-contained after phase-fill
    When I strict-lint the core develop disciplines
    Then the "debug" discipline is self-contained
    And the "verify" discipline is self-contained
    And the "plan" discipline is self-contained
    And the "execute" discipline is self-contained

  Scenario: an enriched discipline renders its phase instructions (A2 parity)
    When the install files are generated
    Then the rendered develop skill inlines the enriched "debug" phase instructions

  # ── Spec 378 Slice 2 — the core SDLC disciplines ──────────────────────────────

  Scenario: the core SDLC develop disciplines are self-contained after phase-fill
    When I strict-lint the SDLC develop disciplines
    Then the "brainstorm" discipline is self-contained
    And the "review" discipline is self-contained
    And the "spec-panel" discipline is self-contained

  # ── Spec 378 Slice 3 — the whole develop discipline set ───────────────────────

  Scenario: every develop discipline is self-contained after the migration
    When I strict-lint every develop discipline
    Then every develop discipline is self-contained

  # ── Spec 378 Slice 4 — the graduated discipline gate ──────────────────────────

  Scenario: the discipline gate blocks compliant disciplines and warns the tail
    When I lint all registered disciplines
    Then no compliant discipline is blocked
    And every develop discipline is reported clean
    And the migration tail is reported as warnings

  # ── Spec 378 Slice 5 — the cross-cap understand cluster (gate auto-widens) ─────

  Scenario: the cross-capability understand disciplines join the gate
    When I lint all registered disciplines
    Then the "code-analysis" discipline is reported clean
    And the "critical-thinking" discipline is reported clean
    And the "guided-discovery" discipline is reported clean

  # ── Spec 378 Slice 6 — the cross-cap dispatch cluster ─────────────────────────

  Scenario: the cross-capability dispatch disciplines join the gate
    When I lint all registered disciplines
    Then the "dispatch-decision" discipline is reported clean
    And the "dispatching-parallel-agents" discipline is reported clean
    And the "subagent-driven-development" discipline is reported clean
