Feature: discover capability scaffold — the intent pillar's drop-in shell (Spec 308)
  Adding the discover/ folder yields a complete, discoverable, CLI-exposed,
  MCP-wired capability that registers the WHOLE Spec 307 program ontology — and
  nothing outside the folder changed. Each of 309-325 is then a pure addition.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: discover is discovered and its status reports the locked Spec 307 surface
    When I ask discover for its status
    Then the discover status reports the seven program node types
    And the discover status reports the seven program edges
    And the discover status reports the four program enums and six schemas

  Scenario: discover reuses research's Citation rather than redeclaring it
    Then the discover ontology does not declare a Citation node

  Scenario: discover derives a SkillDoc and the guided-discovery discipline is registered
    Then discover has a derived SkillDoc
    And the guided-discovery walkable skill is registered
