Feature: Loop goal coaching — Spec 363 (frame_goal / critique_goal)
  A loop's goal IS a root Intent (reuse intent.capture); context_sources bind
  argv-safe onto the Intent; critique surfaces goal-rubric.md findings and is
  advisory — it never blocks (looper parity).

  Background:
    Given a fresh agency engine in code-mode

  Scenario: framing a goal binds it to a root Intent with argv-safe context
    When I frame a goal "Produce a workflow map" done "every step maps to a tool, no TBD" with a file context source
    Then the goal's root Intent has purpose "Produce a workflow map" and acceptance "every step maps to a tool, no TBD"
    And the context source is stored as a structured file entry

  Scenario: a cmd context source must be an argv array, never a shell string
    When I frame a goal with a shell-string cmd context source
    Then framing is rejected as not an argv array

  Scenario: critique flags an activity-framed, unfalsifiable goal (advisory)
    Given a framed goal "work on improving the docs" done "make it good" with no context
    When I critique the goal
    Then critique flags outcome-vs-activity citing the goal rubric
    And critique flags the unfalsifiable done-state
    And critique flags missing context sources
    And critique does not block

  Scenario: a sharp goal passes critique clean
    Given a framed goal "Produce a workflow map for new users" done "every step maps to a tool or human owner, no TBD" with a file context
    When I critique the goal
    Then critique returns no findings
