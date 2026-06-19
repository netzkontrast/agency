Feature: typed Intent fulfilment — the Intent-owned Gate + AcceptanceCriterion (Spec 328)
  A Gate captures whether an Intent is FULFILLED (owner directive: the Gate lives
  in Intent). Confirming an Intent records a clarity Gate keyed to that Intent, and
  the check accrues as history. AcceptanceCriteria — the definition of "fulfilled"
  — are typed and foreign-keyed to their Intent. The clarity score is sourced from
  the shipped substrate scorer (Spec 322), never a second source.

  Background:
    Given a fresh agency engine

  Scenario: confirming an Intent records an Intent-owned clarity Gate
    When I capture and confirm an intent
    Then a typed clarity Gate exists for that intent
    And the clarity Gate's intent_id resolves to a typed Intent row
    And the clarity Gate's score equals the intent's substrate clarity score

  Scenario: the Gate check accrues as history
    When I capture and confirm an intent
    And I add a measurable acceptance criterion and re-confirm
    Then the intent has more than one clarity Gate
    And the latest clarity Gate's score is higher than the first

  Scenario: an acceptance criterion is typed and foreign-keyed to its intent
    When I capture an intent and add a measurable acceptance criterion to it
    Then the criterion has a typed AcceptanceCriterion row
    And the criterion row's intent_id resolves to that intent
    And the criterion row's measurable flag is true

  Scenario: a Lifecycle gate is not mis-attributed to an intent
    When I record a Lifecycle gate not tied to any intent
    Then that Gate row has a null intent_id
