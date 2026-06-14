Feature: Code-mode wire contract
  The agency engine's entire wire surface is three verbs — search, get_schema,
  execute. Capability verbs are reached only from inside execute, never exposed
  directly. This observable behaviour must hold across the Spec-286 refactor.

  Scenario: The wire exposes exactly the three contract verbs
    Given a fresh agency engine in code-mode
    When a client lists the available tools
    Then "search", "get_schema" and "execute" are all available
    And no capability verb is exposed directly at the wire

  Scenario: A capability verb is reachable through execute
    Given a fresh agency engine in code-mode
    When a client lists the available tools
    Then the execute verb is available to run capability code
