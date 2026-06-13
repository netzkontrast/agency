Feature: A working capability surface and engine health
  The engine offers a substantial capability surface and reports its own health.
  These observable behaviours must survive the Spec-286 refactor (the verb
  surface must not collapse; the doctor must keep answering).

  Scenario: The engine exposes a substantial set of capability verbs
    Given a fresh agency engine in code-mode
    When a client lists the capability verbs
    Then many capability verbs are available

  Scenario: The engine doctor reports health
    Given a fresh agency engine in code-mode
    When I ask the engine doctor for a health report
    Then a non-empty health report is returned

  Scenario Outline: A clustered capability keeps its full verb suite after splitting
    # Guards the P3 god-class splits — a cluster mixin split must not drop verbs.
    # Behaviour: the capability still offers its whole feature set.
    Given a fresh agency engine in code-mode
    When a client lists the capability verbs
    Then the "<cap>" capability exposes a full clustered verb suite

    Examples:
      | cap   |
      | music |
      | novel |
