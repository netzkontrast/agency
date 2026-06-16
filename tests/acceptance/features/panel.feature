Feature: panel capability — multi-expert business analysis (Spec 294)
  A native reimplementation of SuperClaude's Business Panel: nine expert
  frameworks, three modes (discussion/debate/socratic), decidable mode selection.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the roster lists the nine experts with frameworks
    When I list the panel experts
    Then the roster has nine experts including Porter and Taleb

  Scenario: convene auto-selects debate mode for a risky decision
    When I convene the panel on "a controversial high-risk pricing decision"
    Then the panel mode is "debate"
    And the panel records a Panel node serving the intent

  Scenario: convene auto-selects socratic mode for a learning subject
    When I convene the panel on "help me understand why this strategy works"
    Then the panel mode is "socratic"
    And each expert contributes a question

  Scenario: convene defaults to discussion with framework lenses
    When I convene the panel on "our market expansion plan"
    Then the panel mode is "discussion"
    And each expert contributes a framework prompt

  Scenario: full focus convenes all nine experts
    When I convene the full panel on "our market expansion plan"
    Then the panel includes all nine experts
