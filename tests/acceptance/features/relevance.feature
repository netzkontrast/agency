Feature: Relevance filter — content-aware output trimmer (Spec 350 Slice 1)
  A pure ``relevance_filter(text, profile)`` extracts signal lines from verbose
  output by include/exclude regex patterns + context.  Never truncates silently:
  ``elided`` + ``locator`` always present.  The same helper backs both the
  ``relevance:`` strategy in ``_apply_filter`` and ``jules.activities(filter=)``.

  # ── pure helper ──────────────────────────────────────────────────────────────

  Scenario: relevance keeps the matching lines and reports what it dropped
    Given output of 2000 lines where 3 lines contain "ERROR"
    And a profile include=["ERROR"] context=0 budget=0
    When I call relevance_filter
    Then kept contains the 3 ERROR lines
    And elided equals 1997
    And locator is present

  Scenario: exclude wins over include
    Given text with a "WARN: real" line and a "WARN: deprecated" line
    And a profile include=["WARN"] exclude=["deprecated"]
    When I call relevance_filter
    Then kept contains "WARN: real"
    And kept does not contain "WARN: deprecated"
    And matched equals 1

  Scenario: budget bounds the wire return but not matched count
    Given output of 500 lines each 10 chars wide
    And a profile include=[] exclude=[] budget=50
    When I call relevance_filter
    Then kept length is at most 100 chars
    And elided is reported in the result
    And locator is present

  Scenario: a bad regex fails open — never raises on the hook path
    Given text with a line "hello world"
    And a profile include=["[invalid"] context=0 budget=0
    When I call relevance_filter
    Then the call succeeds without raising
    And kept is the original text (bad pattern skipped, all lines kept)

  # ── shell _apply_filter integration ───────────────────────────────────────

  Scenario: the relevance strategy in _apply_filter uses the same helper
    Given text with "ERROR: disk full" and "INFO: startup complete"
    And a relevance spec string targeting "ERROR"
    When I call _apply_filter with the relevance spec
    Then the result contains "ERROR: disk full"
    And the result does not contain "INFO: startup complete"

  # ── jules.activities integration ──────────────────────────────────────────

  Scenario: jules.activities filter keeps only matching activities
    Given a stub backend returning activities of kinds agentMessaged and heartbeat
    When I call jules.activities with filter including "agentMessaged"
    Then the returned activities list contains only the agentMessaged activity
    And filter_applied is present in the result

  Scenario: jules.activities full=True bypasses the filter
    Given a stub backend returning activities of kinds agentMessaged and heartbeat
    When I call jules.activities with full=True and filter including "agentMessaged"
    Then the returned activities list contains both activities

  # ── Slice 2: config registry ─────────────────────────────────────────────────

  Scenario: jules.activities accepts a named config profile as the filter arg
    Given a config file with a "testprofile" filter including "agentMessaged"
    And a stub backend returning activities of kinds agentMessaged and heartbeat
    When I call jules.activities with filter name "testprofile" and the config path
    Then only the agentMessaged activity is returned via the named profile

  Scenario: capture_filter applies config filters.shell profile to Bash output
    Given a config file with filters.shell.exclude containing "SKIPME"
    When I capture Bash output containing a "SKIPME" line via capture_filter with the config
    Then the capture_filter filtered result does not contain "SKIPME"

  Scenario: PostToolUse capture uses filters.toolcall profile from config
    Given a config file with filters.toolcall.include=["IMPORTANT"]
    When a PostToolUse event with output containing "IMPORTANT" and "noise" is dispatched with the config
    Then the toolcall store filtered view contains "IMPORTANT" and not "noise"
