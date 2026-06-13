Feature: analyze capability — code analysis and graph census (Spec 042, Spec 048, Spec 084)
  The analyze capability exposes five decidable analysis axes (quality, security,
  performance, architecture, paths), a graph-query verb, and provenance-recorded
  invocations. Behaviour is observable through returned values, graph state, and
  graph census counts.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── analyze.graph ──────────────────────────────────────────────────────────

  Scenario: graph census includes at least the confirmed intent
    When I invoke analyze.graph with no filters
    Then the census contains at least one Intent node
    And the nodes list is empty when no node_type is given

  Scenario: graph lists nodes filtered by label and scope
    Given a reflection is recorded with scope "observation"
    When I invoke analyze.graph for label "Reflection" and scope "observation"
    Then every listed node has scope "observation"
    And the census shows at least one Reflection

  Scenario: graph limit caps the returned rows
    Given four reflections are recorded
    When I invoke analyze.graph for label "Reflection" with limit 2
    Then at most 2 nodes are returned

  # ── analyze.run — quality axis ─────────────────────────────────────────────

  Scenario: run records an Analysis node in the graph
    Given a Python source file with one unused import
    When I run analyze on that file with axis "quality"
    Then the result carries an analysis_id
    And an Analysis node with that id exists in the graph
    And the result totals include the "quality" axis

  Scenario: run on a file with two unused imports records at least two Q001 findings
    Given a Python source file with two unused imports
    When I run analyze on that file with axis "quality"
    Then at least 2 Finding nodes with rule "Q001" exist in the graph

  Scenario: run with all axes returns totals for all five axes
    Given a trivial Python source file
    When I run analyze on that file with no axis filter
    Then the result totals include keys for quality, security, performance, architecture, and paths

  Scenario: run summary payload is compact
    Given a Python source file with one unused import
    When I run analyze on that file with axis "quality"
    Then the JSON payload is under 500 characters

  # ── analyze.improve ────────────────────────────────────────────────────────

  Scenario: improve drafts a plan without applying it
    Given a Python source file with two unused imports
    And I have run analyze with axis "quality" producing an analysis_id
    When I call analyze.improve with apply False
    Then the result carries an improvement_plan_id
    And the item_count is at least 2
    And a Reflection node with kind "improvement-plan" exists for that id

  # ── analyze.cleanup ────────────────────────────────────────────────────────

  Scenario: cleanup dry_run returns a patch plan with findings
    Given a Python source file with one unused import
    When I call analyze.cleanup in dry_run mode
    Then the cleanup result carries an improvement_plan_id
    And the cleanup item_count is at least 1

  # ── quality scanner behaviours ─────────────────────────────────────────────

  Scenario: quality scanner detects unused imports
    Given a Python source file with two unused imports
    When I invoke the quality scanner on that file
    Then the findings include at least 2 entries with rule "Q001"
    And those findings have severity "warn"

  Scenario: quality scanner flags lines over 100 characters
    Given a Python source file with a very long line
    When I invoke the quality scanner on that file
    Then the findings include a Q002 entry with severity "warn"

  Scenario: quality scanner does not flag __future__ annotations import
    Given a Python source file with only "from __future__ import annotations"
    When I invoke the quality scanner on that file
    Then no Q001 finding is produced

  Scenario: quality scanner does not flag imports listed in __all__
    Given a Python source file that re-exports a name via __all__
    When I invoke the quality scanner on that file
    Then no Q001 finding is produced

  Scenario: quality finding shape carries required keys
    Given a Python source file with one unused import
    When I invoke the quality scanner on that file
    Then every finding has keys rule, severity, file, line, message, and evidence
    And severity is one of info, warn, or fail
    And line is a positive integer
    And message is at most 120 characters
    And evidence is at most 200 characters

  # ── security scanner behaviours ────────────────────────────────────────────

  Scenario: security scanner flags eval() as fail
    Given a Python source file that calls eval on user input
    When I invoke the security scanner on that file
    Then a S001 finding with severity "fail" is produced

  Scenario: security scanner flags hardcoded API key as fail without leaking the value
    Given a Python source file with a hardcoded API key
    When I invoke the security scanner on that file
    Then a S002 finding with severity "fail" is produced
    And the finding message does not contain the literal key value

  Scenario: security scanner flags pickle.load as warn
    Given a Python source file that calls pickle.load
    When I invoke the security scanner on that file
    Then a S003 finding with severity "warn" is produced

  Scenario: security scanner does not flag shell=True outside subprocess
    Given a Python source file that uses shell=True in a non-subprocess call
    When I invoke the security scanner on that file
    Then no S004 finding is produced

  # ── performance scanner behaviours ─────────────────────────────────────────

  Scenario: performance scanner flags nested loops on growing list
    Given a Python source file with a nested loop on a growing list
    When I invoke the performance scanner on that file
    Then a P001 finding with severity "warn" is produced

  Scenario: performance scanner flags string concat in loop as info
    Given a Python source file with string concatenation inside a loop
    When I invoke the performance scanner on that file
    Then a P002 finding with severity "info" is produced

  Scenario: performance scanner does not flag integer counter in loop
    Given a Python source file with an integer counter in a loop
    When I invoke the performance scanner on that file
    Then no P002 finding is produced

  # ── architecture scanner behaviours ────────────────────────────────────────

  Scenario: architecture scanner flags circular import as fail
    Given a Python package with a circular import between two modules
    When I invoke the architecture scanner on that package
    Then an A001 finding with severity "fail" is produced

  Scenario: architecture scanner does not flag an acyclic package
    Given a Python package where b imports a but a does not import b
    When I invoke the architecture scanner on that package
    Then no A001 finding is produced

  # ── external deps integration ───────────────────────────────────────────────

  Scenario: agency_doctor reports analyze_extras with known tool names
    When I call agency_doctor
    Then the payload includes analyze_extras
    And the known extra tools are exactly ruff, bandit, and radon
    And each status value is a non-empty string
