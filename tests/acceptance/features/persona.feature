Feature: persona capability — specialist engineering personas, first-class (Spec 297)
  A native registry of SuperClaude's specialist agents, matched to tasks
  decidably and composed into dispatch briefs recorded as provenance.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the roster lists the specialist personas
    When I list the personas
    Then the persona roster includes security-engineer and refactoring-expert

  Scenario: recommend matches a security task to the security engineer
    When I recommend a persona for "find the auth vulnerability and fix the security exploit"
    Then the top recommended persona is "security-engineer"

  Scenario: summon auto-selects and composes a dispatch brief with provenance
    When I summon the auto persona for "profile the latency bottleneck and optimize throughput"
    Then the summoned persona is "performance-engineer"
    And the brief embeds the role focus and the task
    And summon records a PersonaBrief node serving the intent

  Scenario: summon an explicit persona by name
    When I summon the "requirements-analyst" persona for "turn this vague idea into a spec"
    Then the summoned persona is "requirements-analyst"
