Feature: Loop verification as typed gates — Spec 364 (add_criterion / check_criterion / verify_report)
  Looper's typed verification (programmatic/judge/human) expressed on agency's
  gate shape: one typed verdict per criterion (pass|revise|input-required).
  programmatic is argv-only (shell safety, Spec 192); a judge degrades unparseable
  council output to revise+warning; verify_report audits the criteria SET against
  verification-rubric.md. (Criteria stored on the loop as JSON — promoted to typed
  nodes when the loop capability's ontology extension lands.)

  Background:
    Given a fresh agency engine in code-mode
    And an open loop

  Scenario: a programmatic criterion passes on exit zero
    When I check a programmatic criterion that runs true expecting exit_zero
    Then the verdict is "pass"

  Scenario: a programmatic criterion check must be an argv array
    When I add a programmatic criterion with a shell-string check
    Then adding is rejected as not an argv array

  Scenario: a judge verdict is parsed to a typed verdict
    When I check a judge criterion with a passing JSON verdict
    Then the verdict is "pass"

  Scenario: an unparseable judge verdict degrades to revise with a warning
    When I check a judge criterion with non-JSON council output
    Then the verdict is "revise"
    And the warning is "unparseable_judge_output"

  Scenario: a human criterion returns an input-required pause
    When I check a human criterion prompting for sign-off
    Then the verdict is "input-required"
    And the pause names the prompt

  Scenario: verify_report warns on an all-vibe criteria set
    Given the loop has a judge criterion and a human criterion
    When I run verify_report
    Then a warning cites the verification rubric about the missing deterministic floor
    And the programmatic ratio is 0
