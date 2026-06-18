Feature: skill_generator capability — author + lint a SKILL.md (Spec 028)
  generate authors a SKILL.md from name/description/body and lints it against
  the CSO rules, flagging whether it is deploy-ready (ok + violations).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a well-formed skill is authored and passes the lint
    When I generate a skill with a well-formed description and body
    Then the generate result carries the skill_md
    And the generate result is deploy-ready with no violations

  Scenario: a malformed skill is flagged with violations
    When I generate a skill with a malformed name and a vague description
    Then the generate result is not deploy-ready
    And the generate result lists at least one violation
