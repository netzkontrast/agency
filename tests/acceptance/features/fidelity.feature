Feature: No-truncate-or-paginate data fidelity (Spec 336 S1)
  Captured/stored data is never silently truncated. When a RETURN must be
  size-bounded it PAGINATES — a page + a cursor + a read-continuation instruction
  — so the complete set is always reachable, never cut.

  Scenario: a small set fits in one page with no continuation
    Given a sequence of 3 items
    When I paginate it with page size 10
    Then the page holds all 3 items
    And the read-more instruction is empty

  Scenario: a large set paginates with a working continuation cursor
    Given a sequence of 25 items
    When I paginate it with page size 10
    Then the page holds 10 items
    And the read-more instruction names cursor 10
    And the reported remaining count is 15

  Scenario: walking every page reconstructs the complete set, nothing dropped
    Given a sequence of 25 items
    When I walk every page at page size 10
    Then the walked set equals the original 25 items
