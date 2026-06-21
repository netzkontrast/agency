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

  # ── Slice 2 — link / supersede / theme_status / impact / render ──────────────

  Scenario: link adds a typed dependency edge that impact can traverse
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "datalayer"
    When I draft decisions "A" and "B" under that theme
    And I link "A" DEPENDS_ON "B"
    Then the link result is linked
    And the impact of "B" includes at least one dependent

  Scenario: link rejects a circular dependency (DEP-001)
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "datalayer"
    When I draft decisions "A" and "B" under that theme
    And I link "A" DEPENDS_ON "B"
    And I link "B" DEPENDS_ON "A"
    Then the link result is an error with rule "DEP-001"

  Scenario: link rejects a dependency on a rejected decision (DEP-003)
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "datalayer"
    When I draft decisions "A" and "B" under that theme
    And I set "B" to status "rejected"
    And I link "A" DEPENDS_ON "B"
    Then the link result is an error with rule "DEP-003"

  Scenario: supersede mints a replacement and flips the old to superseded
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "substrate"
    When I draft decisions "A" and "B" under that theme
    And I supersede "A" with a new decision
    Then the supersede result has a new decision id
    And the superseded decision "A" now has status "superseded"

  Scenario: theme_status aggregates approved children as approved
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "capabilities"
    When I draft decisions "A" and "B" under that theme
    And I set "A" to status "approved"
    And I set "B" to status "approved"
    And I check the theme status
    Then the aggregate status is "approved"

  Scenario: theme_status reports blocked when a child is rejected
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "capabilities"
    When I draft decisions "A" and "B" under that theme
    And I set "B" to status "rejected"
    And I check the theme status
    Then the aggregate status is "blocked"

  Scenario: render projects live decisions and is idempotent
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And an adr theme "datalayer"
    When I draft decisions "A" and "B" under that theme
    And I supersede "A" with a new decision
    And I render that theme
    Then the render reports 2 active and 1 superseded decisions
    And re-rendering produces the same content hash
