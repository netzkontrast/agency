Feature: codes-coverage audit — typed ToolResult.failure codes (Spec 151)
  The audit walks `ToolResult.failure(code, …)` call sites and classifies each:
  `Codes.X` (a real member → covered) vs a bare string literal or a typo'd
  member (offender — a runtime Attribute/NameError waiting to happen). The
  Slice 2 gate compares live offenders to a committed baseline, keyed by
  `(path, literal)` as a multiset so it tolerates line shifts, and fails only
  on genuinely NEW offenders.

  Scenario: a typed Codes member is covered and a string literal is an offender
    When I audit a source with one Codes.NOT_FOUND call and one "NOT_FOUND" literal
    Then exactly one call site is covered
    And exactly one call site is an offender

  Scenario: a typo'd Codes member is surfaced as an offender, not covered
    When I audit a source whose failure call uses a Codes typo
    Then the typo call site is an offender

  Scenario: the baseline comparison tolerates line shifts
    When I shift the offender down by inserting blank lines above it
    Then the baseline comparison reports no new offenders

  Scenario: an empty tree is trivially covered
    When I audit a source with no failure call sites
    Then the codes coverage fraction is 1.0

  Scenario: the live audit stays in sync with the committed baseline
    When I run the live codes audit and compare to the committed baseline
    Then there are no new codes offenders
    And there are no fixed baseline entries to trim
