Feature: Derive-docs fence rewrite — spec.md derived-zone updates
  `derive_docs` rewrites content between
  `<!-- derived:<id> -->` ... `<!-- /derived:<id> -->` fences;
  hand-authored prose outside the fences is byte-preserved.

  # ── fence rewrite ─────────────────────────────────────────────────────────

  Scenario: test-count fence is filled from the affects-file test count
    Given a spec.md with a test-count fence and affects "tests/test_foo.py"
    And 7 collected tests for "tests/test_foo.py"
    When I apply derivations to the spec text
    Then the test-count fence content shows "7"
    And the hand prose outside the fence is unchanged

  Scenario: applying derivations twice is idempotent
    Given a spec.md with a test-count fence and affects "tests/test_foo.py"
    And 3 collected tests for "tests/test_foo.py"
    When I apply derivations to the spec text
    And I apply derivations to the result again
    Then the two results are identical

  Scenario: an unclosed fence raises ValueError
    Given a spec.md with an unclosed test-count fence
    When I apply derivations to the spec text
    Then a ValueError is raised mentioning the unclosed fence

  Scenario: a spec without any fences is unchanged
    Given a spec.md with no derived fences
    When I apply derivations to the spec text
    Then the output is identical to the input

  # ── drift check (Slice 2.3) ───────────────────────────────────────────────

  Scenario: stale derived zone is detected as drift
    Given a spec.md with a stale test-count fence showing "42" but 7 collected tests
    When I check the spec text for derived-zone drift
    Then drift is detected and a diff hint is returned

  Scenario: up-to-date derived zone reports no drift
    Given a spec.md with an up-to-date test-count fence showing "7" and 7 collected tests
    When I check the spec text for derived-zone drift
    Then no drift is detected

  Scenario: spec without fences reports no drift
    Given a spec.md with no derived fences and 5 collected tests
    When I check the spec text for derived-zone drift
    Then no drift is detected

  # ── live tree ──────────────────────────────────────────────────────────────

  Scenario: live tree — derive-docs dry-run completes without error
    When I run derive-docs in dry-run mode on the live repo
    Then it completes without error and reports at least one spec

  Scenario: live tree — derive-docs --check exits 0
    When I run derive-docs --check on the live repo
    Then it exits 0
