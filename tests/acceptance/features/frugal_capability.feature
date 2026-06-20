Feature: frugal capability — the ponytail port (Spec 348 Slice 1)
  The minimal-code discipline exposed as a discoverable, MCP-wired capability
  wrapping the core _frugal module (Spec 332 — single source for ladder + floor).

  Scenario: level reports the active discipline level (default full)
    When I read the frugal capability level
    Then the reported frugal level is "full"

  Scenario: set_level persists across a fresh read
    When I set the frugal capability level to "lite"
    And I read the frugal capability level
    Then the reported frugal level is "lite"

  Scenario: instructions returns the ruleset with the safety floor (the MCP port)
    When I get the frugal instructions at "ultra"
    Then the frugal instructions name every safety-floor marker
    And the reported frugal level is "ultra"

  Scenario: instructions at off are empty
    When I get the frugal instructions at "off"
    Then the frugal instructions are empty

  Scenario: help returns the complete reference card
    When I get the frugal help
    Then the frugal help contains "Intensity levels (active:"
    And the frugal help contains "YAGNI"
    And the frugal help contains "skipped:"

  Scenario: debt harvests comment-prefixed markers (incl. an HTML comment) as provenance
    Given a source tree with frugal markers
    When I harvest the frugal debt for that tree
    Then the debt ledger has 3 markers
    And 1 marker has no upgrade trigger
    And a DebtMarker node serves the intent

  Scenario: debt ignores a frugal: string that is not in a comment (M3)
    Given a source file with a frugal string literal
    When I harvest the frugal debt for that tree
    Then the debt ledger has 0 markers

  Scenario: gain shows the published benchmark and never invents a per-repo number
    When I get the frugal gain scoreboard
    Then the scoreboard names the ponytail benchmark source
    And the scoreboard points to frugal.debt for the only real per-repo number

  Scenario: review flags decidable bloat and records provenance (composes analyze)
    Given a python file with over-engineering bloat
    When I review that tree for over-engineering
    Then the review flags a decidable cut
    And the review names the over-engineering tags
    And a FrugalReview node serves the intent

  Scenario: review on lean code flags nothing but still records the run
    Given a lean python source tree
    When I review that tree for over-engineering
    Then the review flags no decidable cuts
    And a FrugalReview node serves the intent

  Scenario: frugal emits a first-use hint once per tool (event bus, Spec 349a)
    When a PreToolUse fires for "Bash" the first time
    Then the injected context contains the frugal first-use hint
    When a PreToolUse fires for "Bash" again
    Then the injected context omits the frugal first-use hint

  # ── the mandatory SessionStart port: deep + delivered exactly once ──────────
  # These scenarios are the GUARANTEE that the next session uses the ponytail
  # port — they fail loudly if the inject is ever shallowed or fires more than
  # once per session.

  Scenario: SessionStart injects the FULL frugal discipline — the mandatory ponytail port (Spec 348)
    When a SessionStart hook fires for session "s-deep"
    Then the session "s-deep" inject names every safety-floor marker
    And the session "s-deep" inject teaches the ladder, the rules, and the output pattern
    And the session "s-deep" inject is far deeper than the one-line per-verb stamp

  Scenario: the deep frugal inject fires exactly once per session (Spec 349a dedup over startup/resume/compact)
    When a SessionStart hook fires for session "s-once"
    And a SessionStart hook fires for session "s-once"
    Then the session "s-once" discipline is injected exactly once
    And the second session "s-once" inject is empty

  Scenario: a different session re-injects the discipline (per-session, not global)
    When a SessionStart hook fires for session "s-a"
    And a SessionStart hook fires for session "s-b"
    Then the session "s-b" inject carries the frugal discipline

  Scenario: the SessionStart inject is silent only when frugal is explicitly off
    Given the frugal level is "off"
    When a SessionStart hook fires for session "s-off"
    Then the session "s-off" inject is empty

  Scenario: event-bus dedup markers never pollute the tool-call capture (Spec 336/349a)
    When a PreToolUse fires for "Bash" the first time
    And a PreToolUse fires for "Bash" again
    Then the tool-call capture stats carry no event-bus marker
