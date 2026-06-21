Feature: guided-discovery discipline skill (Spec 322 Slice 3)
  The ``guided-discovery`` authored discipline is registered in the ``discover``
  capability's ontology, replacing the derived ``discover-usage`` default.  Its
  final ``decide`` phase carries ``gate: "computed"`` and ``gate_verb:
  "clarity_gate"`` — making the clarity gate a structural property of the walk
  (invariant, not a reviewer's hope) before an Intent is confirmed.

  Scenario: the skill parses cleanly from the live registry
    Given a fresh agency engine in code-mode
    When I load the guided-discovery skill from the discover ontology
    Then parse_skill returns success

  Scenario: the skill is a discipline that overrides the derived default
    Given a fresh agency engine in code-mode
    When I load the guided-discovery skill from the discover ontology
    Then the skill kind is "discipline"

  Scenario: all seven phases are present with non-empty produces
    Given a fresh agency engine in code-mode
    When I load the guided-discovery skill from the discover ontology
    Then the skill has exactly 7 phases
    And every phase declares at least one produces item

  Scenario: phase indices are contiguous 1 through 7
    Given a fresh agency engine in code-mode
    When I load the guided-discovery skill from the discover ontology
    Then phase indices are 1 through 7 in order

  Scenario: the final phase carries the computed clarity gate
    Given a fresh agency engine in code-mode
    When I load the guided-discovery skill from the discover ontology
    Then the last phase name is "decide"
    And the last phase gate is "computed"
    And the last phase gate_verb is "clarity_gate"

  Scenario: the skill is discoverable via the engine ontology
    Given a fresh agency engine in code-mode
    Then "guided-discovery" is registered in the engine ontology skills
