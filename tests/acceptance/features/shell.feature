Feature: Shell capability — run, filter, define, templates
  shell runs allowlisted commands with token-efficient output filtering and
  records provenance; templates are discoverable and definable; the
  allowlist is a hard boundary (Spec 073/075).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── filter verb ───────────────────────────────────────────────────────────

  Scenario: filter verb trims output without executing any command
    When I filter 100 lines with spec "tail:3"
    Then the filtered output has 3 lines
    And no subprocess was started

  # ── run: allowlist + provenance ───────────────────────────────────────────

  Scenario: run an allowlisted command, get filtered output and provenance
    When I run "ls -la" with filter "tail:5" and 500 lines of stdout
    Then the exit code is 0
    And the output has 5 lines
    And a command-run node is recorded with tool "ls"
    And the command-run node SERVES the intent

  Scenario: run rejects a non-allowlisted command
    When I run "rm -rf /" with no filter
    Then the result carries an error
    And no subprocess was started

  # ── run via template ──────────────────────────────────────────────────────

  Scenario: run via a known template applies its command and filter
    When I run template "test-failures" with stdout "ok\nFAILED test_x\nok\nFAILED test_y"
    Then the result names the template "test-failures"
    And every output line contains "FAILED"
    And a subprocess was started

  Scenario: run via an unknown template returns an error with the template list
    When I run template "does-not-exist"
    Then the result carries an error
    And the error response lists available templates

  # ── templates list ────────────────────────────────────────────────────────

  Scenario: templates verb lists discoverable templates including seeds
    When I list templates
    Then the list includes the seed template "tests"
    And every template entry has a command and a doc

  # ── define + discovery round-trip ─────────────────────────────────────────

  Scenario: define a template then run it
    When I define template "last2" with command "git log" and filter "tail:2" and stdout "a\nb\nc\nd\ne"
    Then the template is recorded with a template_id
    And running template "last2" returns 2 lines
    And the dispatched command starts with "git"

  Scenario: defined template surfaces through query discovery
    When I define template "audit-log" with command "git log --oneline" tag "review"
    And I query templates with "review"
    Then "audit-log" appears in the results with source "graph"
    And querying templates with "zzz-nomatch" returns an empty list

  Scenario: graph template overrides a seed template of the same name
    When I define a template that overrides a seed template using command "echo overridden"
    Then running that template dispatches "echo overridden"
    And the template list shows one entry for that name from source "graph"

  Scenario: define rejects a non-allowlisted command
    When I define template "evil" with command "rm -rf /"
    Then the result carries an error
    And querying templates for "evil" returns no results

  Scenario: redefine a template supersedes the previous version
    When I define template "dup" with command "git status"
    And I redefine template "dup" with command "git diff"
    Then the template list shows one "dup" entry with command "git diff"
    And a SUPERSEDED_BY trail exists in the graph

  Scenario: empty query returns seeds and graph templates together
    When I define template "mine" with command "ls"
    And I list templates
    Then "mine" appears in the results
    And all seed templates are present

  Scenario: define records a SERVES edge to the intent for provenance
    When I define template "prov" with command "ls"
    Then the template artefact SERVES the intent

  # ── allowlist regression (Spec 280) ───────────────────────────────────────

  Scenario: public shell.run remains allowlist-gated after Spec 280
    When I run "/usr/local/bin/audit.sh" with no filter
    Then the result carries an error
    And no subprocess was started
