Feature: Output overflow capture and recall (Spec 154 Slice 1)
  When a verb returns more than the token budget, the tail is LOST without
  overflow capture. capture_overflow() truncates the head and preserves the
  full body for Artefact storage; recall_overflow_slice() retrieves the body
  or a filtered slice on demand. Observable: OverflowResult.head truncation,
  OverflowHandle presence, RecallSlice content, typed rejection.

  Scenario: short body within budget returns head unchanged with no overflow flag
    When I capture a body of 13 tokens with a budget of 100
    Then the head equals the full body
    And the overflow flag is False

  Scenario: long body above budget is truncated at the head
    When I capture a body of 500 tokens with a budget of 50
    Then the overflow flag is True
    And the head is shorter than the full body
    And the head token count does not exceed 50

  Scenario: the full body is preserved byte-for-byte in the overflow result
    When I capture an overflowing body
    Then the OverflowResult carries the complete original body

  Scenario: recall with no slice returns the full captured body
    When I capture an overflowing body and recall it with no slice specifier
    Then the recalled body equals the full original body

  Scenario: recall by line range returns only that range
    When I capture a 20-line body and recall with slice 5 to 10
    Then the recalled body contains only lines at indices 5 to 9

  Scenario: recall by grep returns only matching lines
    When I capture a body with some ERROR lines and recall with grep ERROR
    Then every line in the recalled body contains ERROR

  Scenario: recall grep with no matches returns an empty body
    When I capture a body with no ERROR lines and recall with grep ERROR
    Then the recalled body is empty

  Scenario: OverflowHandle carries a typed shape
    When I capture an overflowing body
    Then the handle has a body_hash and a byte_count

  Scenario: capture with zero budget returns an empty head
    When I capture a body with a budget of zero tokens
    Then the head is empty

  Scenario: capture with negative budget raises ValueError
    When I attempt to capture a body with a negative budget
    Then a ValueError is raised

  Scenario: RecallSlice is a frozen dataclass
    When I recall an overflow body
    Then the RecallSlice cannot be mutated
