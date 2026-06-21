Feature: QualityRun history as a graph node + trend (Spec 381 §3)

  Each review run is recorded as a QualityRun graph node SERVING the intent — not
  a .brooks-lint-history.json sidecar. Trend is a query over prior same-mode runs;
  only complete runs count, so a crashed (incomplete) walk never distorts the delta.

  Background:
    Given an engine and confirmed intent

  Scenario: a quality run is recorded as a graph node, not a sidecar file
    When I record a "review" run of 1 critical
    Then a QualityRun graph node exists for mode "review"
    And no brooks-lint history file is written

  Scenario: the trend is the delta from the prior complete run
    Given a recorded "review" run of 1 critical and 1 warning
    When I record a "review" run of 1 critical, 2 warning, and 3 suggestion
    Then the trend delta is -8

  Scenario: an incomplete prior run is excluded from the trend
    Given a recorded "review" run of 1 critical and 1 warning
    And a recorded incomplete "review" run of 2 warning
    When I record a "review" run of 1 critical, 2 warning, and 3 suggestion
    Then the trend delta is -8

  Scenario: the first run for a mode reports no prior trend
    When I record an "audit" run of 1 critical
    Then the trend reports first run
