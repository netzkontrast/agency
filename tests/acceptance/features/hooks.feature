Feature: hook dispatch — event recording, BoundaryUse capture, foreign-hook install (Spec 076 / 195 / 280)
  The unified hook dispatcher records every Claude Code event as an Event node,
  optionally linking it to the active intent. A raw mutating tool used under an
  active intent records a BoundaryUse node with a verb_shadow. The install
  library merges foreign hooks and patches claude settings idempotently.

  Background:
    Given a fresh agency engine in code-mode

  Scenario: dispatch_hook records an Event node with name and session
    When a UserPromptSubmit hook event fires with session s1
    Then an Event node with name UserPromptSubmit and session s1 is in the graph

  Scenario: PostToolUse event captures a trimmed tool summary under 600 chars
    When a PostToolUse hook event fires with a 200-line Bash command
    Then an Event node for PostToolUse is recorded
    And the event summary is at most 600 characters

  Scenario: missing hook_event_name does not crash the dispatcher
    When a hook event fires without a hook_event_name
    Then the result carries recorded or skipped without raising

  Scenario: hook_event substrate tool is accessible via MCP
    When I call hook_event via the wire with a SubagentStop event
    Then a SubagentStop Event node is in the graph

  Scenario: event links to active AGENCY_INTENT via OBSERVED_DURING edge
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse hook event fires with tool Edit
    Then an OBSERVED_DURING edge connects the Event to the intent

  Scenario: event without active intent still records successfully
    Given no AGENCY_INTENT is set
    When a Notification hook event fires
    Then a Notification Event node is in the graph

  Scenario: raw Bash git commit under active intent records BoundaryUse with verb_shadow branch.commit_smart
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse Bash event fires with command git commit -m x
    Then a BoundaryUse node is recorded
    And the verb_shadow is branch.commit_smart
    And the BoundaryUse tool is Bash

  Scenario: raw Bash pytest under active intent records BoundaryUse with verb_shadow develop.test
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse Bash event fires with command pytest tests/
    Then the verb_shadow is develop.test

  Scenario: raw Edit on a spec under active intent records BoundaryUse with verb_shadow dogfood.observe
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse Edit event fires with file_path Plan/280-foo/spec.md
    Then the verb_shadow is dogfood.observe

  Scenario: PostToolUse Bash does not record BoundaryUse — bypass detection fires only at PreToolUse
    Given a confirmed intent set as AGENCY_INTENT
    When a PostToolUse Bash event fires with command git commit -m x
    Then no BoundaryUse node is created

  Scenario: read-only tools do not record BoundaryUse
    Given a confirmed intent set as AGENCY_INTENT
    When PreToolUse events fire for Read Grep Glob and WebFetch
    Then no BoundaryUse node is created

  Scenario: BoundaryUse serves the active intent and links to the Event via RECORDED_BY
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse Bash git commit event fires under that intent
    Then the BoundaryUse SERVES the intent
    And the BoundaryUse is RECORDED_BY the Event

  Scenario: merge_settings is idempotent and preserves foreign plugins
    When I merge settings with another plugin already enabled
    Then agency@agency is added to enabledPlugins
    And the other plugin's entry is preserved
    And merging again produces no change

  Scenario: detect_foreign_hooks finds user-authored hooks and skips agency dispatcher entries
    When I call detect_foreign_hooks on settings containing a hand-authored PreToolUse hook
    Then one ForeignHook is found
    When I call detect_foreign_hooks on settings already containing the agency dispatcher
    Then no ForeignHook is found

  Scenario: wrap_foreign_hook preserves the async flag and records _wrapped_from
    When I wrap a sync ForeignHook
    Then the wrapped entry has async False
    And the wrapped entry has _wrapped_from set to the original command
    And the wrapped command uses agency hook wrap

  Scenario: apply_foreign_wraps does not double-wrap on a second run
    When I apply foreign wraps once then apply again
    Then the first run wraps 1 foreign hook
    And the second run wraps 0 foreign hooks
    And the resulting settings are byte-identical

  Scenario: patch_settings_file writes settings when file is missing and creates a backup on existing file
    When I patch a non-existent settings file
    Then the settings file is created with agency@agency enabled
    And no backup is created
    When I patch an existing settings file
    Then a .bak file is created containing the original content
    And the patched file still has the other plugin entries

  Scenario: canonical settings patch carries the version marker and marketplace entry
    Then CANONICAL_SETTINGS_PATCH contains the _agency_version marker
    And CANONICAL_SETTINGS_PATCH contains agency in extraKnownMarketplaces

  Scenario: async doctrine table blocks PreToolUse and UserPromptSubmit
    Then PreToolUse and UserPromptSubmit are sync in ASYNC_BY_EVENT
    And PostToolUse Stop and SessionEnd are async in ASYNC_BY_EVENT

  Scenario: agency_doctor carries a hooks field with the install status shape
    Given a fresh agency engine in code-mode
    When I call agency_doctor
    Then the result contains a hooks field
    And the hooks field has plugin_enabled cli_on_path hook_scripts_present and next_steps

  Scenario: SessionEnd auto-archives the session as a Document (Spec 292)
    Given a confirmed intent set as AGENCY_INTENT
    When a SessionEnd hook event fires
    Then the hook result archives a session Document
    And that session Document exists in the graph

  Scenario: UserPromptSubmit injects the assumption-guard wiring in intent and thinking
    Given a confirmed intent set as AGENCY_INTENT
    When a UserPromptSubmit hook event fires with session s1
    Then the hook injects an assumption-guard naming intent and thinking
    And the injected guard names the active intent purpose

  Scenario: the Session Graph makes a complete session restorable (Spec 292)
    Given a confirmed intent set as AGENCY_INTENT
    When a UserPromptSubmit then a PostToolUse event fire in session s9
    And a SessionEnd event fires in session s9
    Then restoring session s9 reports a closed session with events and a Document

  Scenario: session analytics summarise a single session via cypher (Spec 292)
    Given a confirmed intent set as AGENCY_INTENT
    When a UserPromptSubmit then a PostToolUse event fire in session s9
    And a SessionEnd event fires in session s9
    Then session analytics for s9 report the event-type and tool breakdown
    And session analytics for s9 attach the archived Document

  Scenario: cross-session analytics aggregate every session (Spec 292)
    Given a confirmed intent set as AGENCY_INTENT
    When a UserPromptSubmit then a PostToolUse event fire in session s9
    Then cross-session analytics report a positive session count and a busiest list

  # ── Spec 195 Slice 2 — PreToolUse returns the agency MCP call + schema ──────

  Scenario: a PreToolUse on git commit returns the agency MCP call and schema
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse event fires for a "git commit -m x" Bash command
    Then the hook returns an agency_suggestion for "capability_branch_commit_smart"
    And the suggestion carries a JSON object schema for the call
    And the additionalContext names the MCP call and its schema

  Scenario: a PreToolUse on a Grep suggests the agency search surface
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse event fires for a Grep tool
    Then the hook returns an agency_suggestion for "mcp__agency__search"

  Scenario: a PreToolUse on a tool with no agency equivalent suggests nothing
    Given a confirmed intent set as AGENCY_INTENT
    When a PreToolUse event fires for a Read tool
    Then the hook returns no agency_suggestion
