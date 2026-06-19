Feature: intent capability — critical-thinking methods and chaining
  The intent capability exposes eight critical-thinking methods that reason about
  the serving intent (Spec 091), plus intent chaining (Spec 048), owner rules,
  path-analysis (analyze.paths, Spec 048), and skill projection (intent.suggests).
  All assertions are on observable verb outputs and graph state only.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── critical-thinking methods ─────────────────────────────────────────────

  Scenario: premortem defaults to the serving intent as its subject
    When I invoke the premortem method with no subject override
    Then the result method is "premortem"
    And the result subject contains the intent deliverable
    And the result has at least 3 steps

  Scenario: explicit subject overrides the ambient intent
    When I invoke decompose with subject "migrate the database"
    Then the result subject is "migrate the database"

  Scenario: tradeoffs parses explicit options and criteria
    When I invoke tradeoffs with options "postgres, sqlite" and criteria "cost, risk"
    Then the result options list is ["postgres", "sqlite"]
    And the result criteria list is ["cost", "risk"]

  Scenario: tradeoffs supplies default criteria when none given
    When I invoke tradeoffs with no options or criteria
    Then "cost" and "reversibility" are among the default criteria

  Scenario: intent.suggests projects to a skill via pattern matching
    When I call suggests with state "which skill should I walk"
    Then a skill is projected with mode "pattern"
    And the projected confidence is 0.8

  Scenario: suggests returns no skill when state is unrelated
    When I call suggests with state "totally unrelated xyzzy"
    Then no skill is projected

  Scenario: suggests floor filters low-confidence matches
    When I call suggests with state "which skill should I walk" and floor 0.9
    Then no skill is projected and the reason mentions the floor

  # ── intent chaining (Spec 048) ─────────────────────────────────────────────

  Scenario: a root intent has no parent
    When I capture and confirm a root intent
    Then that intent has no parent_intent_id

  Scenario: a child intent records its parent
    When I capture a child intent under a parent
    Then the child's parent_intent_id matches the parent

  Scenario: a PARENT_INTENT graph edge is recorded
    When I capture a child intent under a parent
    Then a PARENT_INTENT edge exists from the child to the parent in the graph

  Scenario: a three-level chain is traversable
    When I build a three-level intent chain
    Then the leaf can reach the root via PARENT_INTENT edges in the graph

  # ── owner rules (Spec 048) ──────────────────────────────────────────────────

  Scenario: root intent defaults to owner "user"
    When I capture and confirm a root intent
    Then that intent's owner is "user"

  Scenario: child intent defaults to owner "agent"
    When I capture a child intent under a parent
    Then the child's owner is "agent"

  Scenario: explicit owner overrides the default
    When I capture a child intent under a parent with owner "subagent"
    Then the child's owner is "subagent"

  Scenario: all five owner values are accepted by the engine
    When I capture an intent with each of the five owner values
    Then each intent's stored owner matches the value used to create it

  Scenario: intent_bootstrap returns owner "user" for a root intent
    When I bootstrap an intent via the wire tool with no parent
    Then the bootstrap response carries owner "user"

  Scenario: intent_bootstrap returns owner "agent" for a child intent
    When I bootstrap a child intent via the wire tool under a root
    Then the bootstrap response carries owner "agent"

  Scenario: intent_bootstrap respects an explicit owner override
    When I bootstrap an intent via the wire tool with owner "jules"
    Then the bootstrap response carries owner "jules"

  # ── path analysis (analyze.paths, Spec 048) ──────────────────────────────────

  Scenario: IP001 fires on a deep intent chain
    Given a user root intent with a 6-deep sub-intent chain beneath it
    When I run analyze.paths
    Then finding IP001 is present with severity "info"
    And the finding references the root intent

  Scenario: IP001 does not fire on a shallow chain
    Given a user root intent with only 2 levels beneath it
    When I run analyze.paths
    Then finding IP001 is absent

  Scenario: IP002 fires on a long verb sequence
    Given a user root intent with 14 Invocations serving it
    When I run analyze.paths
    Then finding IP002 is present with severity "warn"

  Scenario: IP002 does not fire for a short sequence
    Given a user root intent with 5 Invocations serving it
    When I run analyze.paths
    Then finding IP002 is absent

  Scenario: IP003 fires on a frequently-repeated verb
    Given a user root intent with 5 invocations of "analyze.quality" and 3 of "document.render"
    When I run analyze.paths
    Then finding IP003 names "analyze.quality"
    And finding IP003 does not name "document.render"

  Scenario: max_paths caps the number of paths scanned
    Given 5 user root intents each with a 6-deep chain
    When I run analyze.paths with max_paths 2
    Then at most 2 IP001 findings are returned

  # ── substrate clarity gate (Spec 307 §Refinement — the gate lives on confirm) ─

  Scenario: confirming an Intent records its clarity_score
    Given a captured-and-confirmed intent
    Then the intent node carries a clarity_score between 0 and 1

  Scenario: the clarity gate blocks a shallow Intent when required
    Given a freshly captured shallow intent
    When I confirm it requiring clarity
    Then the confirm is refused for low clarity
    And confirming it with an override token succeeds

  Scenario: the substrate clarity score agrees with discover.clarity
    Given a captured-and-confirmed intent
    Then the substrate clarity score equals discover clarity's score
