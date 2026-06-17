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

  Scenario: The substrate onboarding tools are exposed
    # Guards A5 (substrate-tools-as-a-registered-set): the onboarding surface a
    # client reaches must stay complete after de-closuring build_mcp.
    Given a fresh agency engine in code-mode
    When a client lists all tools without code-mode
    Then the onboarding tools are all exposed

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

  Scenario: The doctor reports surface freshness and accurate test coverage (Spec 302)
    Given a fresh agency engine in code-mode
    When I ask the engine doctor for a health report
    Then the doctor reports a surface_freshness with a live hash
    And the doctor does not falsely flag acceptance-tested capabilities as untested
