Feature: the typed Intent read API — joins, not Cypher (Spec 330)
  IntentStore reads the whole interweave through typed SQL joins over the
  four-concept tables: every capability serving an intent, its agent, its
  artefacts, its lifecycle, and whether it is fulfilled. A parity gate guarantees
  the typed projection never diverges from the authoritative graph, and manage
  consumes it so the columns are load-bearing (not dormant surface).

  Background:
    Given a fresh agency engine

  Scenario: serves returns exactly the invocations that serve the intent
    When an invocation serving an intent produces an artefact serving it
    Then IntentStore serves matches the SERVES-Invocation set from the graph

  Scenario: provenance is faithful to the authoritative graph
    When an invocation serving an intent produces an artefact serving it
    Then IntentStore provenance invocations match the graph
    And IntentStore provenance includes the produced artefact

  Scenario: the intent tree follows the PARENT_INTENT chain
    When I capture a child intent under a parent intent
    Then IntentStore intent_tree of the parent includes both intents

  Scenario: fulfilment reports the Intent-owned gate verdict
    When I capture and confirm an intent
    Then IntentStore fulfilment carries a verdict gate for that intent

  Scenario: manage state surfaces the typed fulfilment read
    When I capture and confirm an intent
    Then manage state for that intent includes a fulfilment block

  Scenario: manage provenance surfaces the typed cross-concern join
    When an invocation serving an intent produces an artefact serving it
    Then manage provenance for that intent includes the invocation and artefact

  Scenario: manage subtree walks the typed parent-intent tree
    When I capture a child intent under a parent intent
    Then manage subtree of the parent includes both intents
