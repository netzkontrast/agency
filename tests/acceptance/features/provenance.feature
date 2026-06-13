Feature: Provenance is a free byproduct
  Every capability invocation records an Invocation in the one bi-temporal graph,
  edged SERVES to the active intent — the moat (CORE.md §Memory). This observable
  behaviour must hold across the Spec-286 refactor, however the engine is
  internally restructured.

  Scenario: Invoking a verb records provenance against its intent
    Given a confirmed intent
    When I invoke a capability verb under that intent
    Then an Invocation is recorded in the graph
    And that Invocation SERVES the intent

  Scenario: A fresh intent has no served invocations yet
    Given a confirmed intent
    Then the intent has no served invocations
