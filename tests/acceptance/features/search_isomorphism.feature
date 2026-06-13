Feature: MCP/CLI search isomorphism (Spec 023 §F3.1)
  The MCP form (mcp.call_tool('search', ...)) and the CLI form
  (python -m agency.cli search) must return structurally identical results
  after JSON parse. This is the load-bearing guarantee that the canon's
  "isomorphic over MCP / Skills / bash CLI" claim holds for the search surface.

  Scenario Outline: MCP search and CLI search return identical structures
    When I search for "<query>" via MCP and via CLI on the same database
    Then the MCP result and CLI result are structurally identical

    Examples:
      | query         |
      | reflect note  |
      | dispatch      |
      | graph         |
