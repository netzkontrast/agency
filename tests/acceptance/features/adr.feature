Feature: ADR ontology + capability — author & validate (Spec 354 Slice 1)

  A dedicated `adr` capability lands the decision-record primitive: a `Decision`
  whose only storage-required fields are the decision statement + status (so a
  `proposed` skeleton can be recorded and completed incrementally), with the full
  WH(Y) completeness + length budgets enforced by `validate` (derived from the
  `decision` Schema). AdrTheme is a Document(kind=adr-theme), not a new label.

  Scenario: the adr capability is registered on the wire surface
    Given a fresh agency engine in code-mode
    Then a wire tool name contains "adr"

  Scenario: draft creates a WH(Y) Decision that serves the intent
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "datalayer"
    When I draft a well-formed decision under that theme
    Then the decision result has status "proposed"
    And the decision serves the intent

  Scenario: the ontology rejects a Decision missing the required decision statement
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I create a Decision node missing the "decision" field
    Then the adr result is an error

  Scenario: the ontology rejects an unknown decision status
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I create a Decision node with status "totally-bogus"
    Then the adr result is an error

  Scenario: validate flags an incomplete decision as a WHY-001 error
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "substrate"
    When I draft a decision with an empty "facing" field under that theme
    And I validate that decision
    Then the validate findings include rule "WHY-001" with severity "error"
    And the validate result is not ok

  Scenario: validate flags a missing alternative as a WHY-003 error
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "substrate"
    When I draft a decision whose "neglected" field is "none" under that theme
    And I validate that decision
    Then the validate findings include rule "WHY-003" with severity "error"

  Scenario: validate warns when an element exceeds its Schema length budget
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "substrate"
    When I draft a decision with an over-long "tradeoffs" field under that theme
    And I validate that decision
    Then the validate findings include rule "WHY-LEN" with severity "warn"

  Scenario: validate passes a well-formed decision
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "capabilities"
    When I draft a well-formed decision under that theme
    And I validate that decision
    Then the validate result is ok
