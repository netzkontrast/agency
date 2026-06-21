Feature: source-coverage grounding + SARIF property test (Spec 383)

  The 12-book source-coverage matrix is vendored as derived data (count from the
  file, never hardcoded). A finding may cite a book only if that book exists in
  source-coverage — no name-dropping. SARIF validity is a computed property over a
  frozen finding fixture: valid 2.1.0, rule set == the live registry, one result
  per finding (no lossy parse).

  Background:
    Given an engine and confirmed intent

  Scenario: the book registry is derived from the file, not hardcoded
    Then source-coverage lists at least the twelve canonical books
    And each book entry carries an encoded list and a do-not-ignore list
    And the book count is derived from the file

  Scenario: every cited book exists in source-coverage (no name-dropping)
    Then every book a decay risk cites is present in source-coverage

  Scenario: SARIF is a valid computed property over a frozen finding fixture
    Given a frozen finding fixture spanning risks, a custom Cx, and a decidable-only
    When analyze.sarif renders the fixture
    Then the SARIF is valid 2.1.0
    And the rule set equals the live risk-code registry
    And every finding produces exactly one SARIF result
