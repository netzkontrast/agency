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
