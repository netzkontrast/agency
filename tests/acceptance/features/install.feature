Feature: install pipeline — scaffold, hooks, skills, prune (Spec 029 / 031 / 032 / 062 / 064 / 065 / 092)
  The install pipeline produces the plugin manifest, the help skill, per-capability
  SKILL.md files, the session-start hook, bash wrappers, and the MCP config.
  It prunes orphaned wrappers on regen and is idempotent.

  Scenario: agency_install scaffolds .agency/ and writes CLAUDE.md
    Given a fresh agency engine in code-mode
    When I call agency_install on a temporary target
    Then .agency/ directory is created
    And .agency/README.md exists
    And .gitattributes exists
    And CLAUDE.md exists and contains agency_welcome

  Scenario: agency_install is idempotent
    Given a fresh agency engine in code-mode
    When I call agency_install on a temporary target twice
    Then the second call reports claude_md_updated False
    And CLAUDE.md contains exactly one onboarding start marker
    And CLAUDE.md contains exactly one onboarding end marker

  Scenario: agency_install preserves existing CLAUDE.md content
    Given a fresh agency engine in code-mode
    And a target with a pre-existing CLAUDE.md
    When I call agency_install on that target
    Then the original CLAUDE.md content is preserved
    And the agency onboarding block is appended

  Scenario: generate emits per-capability SKILL.md when skill_doc is present
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then the fixed plugin.json and help SKILL.md are present
    And at least one per-capability SKILL.md is present under skills/

  Scenario: generate emits the monitor entry
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then monitors/monitors.json contains exactly one agency-engine entry

  Scenario: generate emits a unified hooks.json wiring PostToolUse UserPromptSubmit Stop
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then hooks/hooks.json wires PostToolUse UserPromptSubmit and Stop to the dispatch script
    And the dispatch script is emitted

  Scenario: hooks.json registers SessionStart with the correct matcher and async flag
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then hooks.json SessionStart entry has matcher startup|resume|clear
    And the SessionStart hook command has async False

  Scenario: session-start script uses pipx and contains scaffold step before guard
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then the session-start script starts with the bash shebang
    And the script contains command -v pipx
    And the script contains pipx install --editable
    And the scaffold step appears before the agency-mcp idempotency guard

  Scenario: session-start script uses agency install --scaffold-only not --scaffold-db
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then the session-start script contains agency install --scaffold-only
    And the script does not contain agency install --scaffold-db

  Scenario: .mcp.json uses bare agency-mcp command and correct AGENCY_DB
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then .mcp.json command is agency-mcp
    And .mcp.json AGENCY_DB is ${CLAUDE_PROJECT_DIR}/.agency/session.db
    And .mcp.json does not contain PYTHONPATH
    And .mcp.json cwd is ${CLAUDE_PROJECT_DIR}
    And .mcp.json env_vars includes AGENCY_EMBEDDER AGENCY_DB and JULES_API_KEY

  Scenario: write preserves an external MCP server across regen
    Given a fresh agency engine in code-mode
    And a target whose .mcp.json declares an external codegraph server
    When I write the install to that target
    Then .mcp.json still declares the external codegraph server
    And .mcp.json still declares the agency server

  Scenario: write is idempotent when an external MCP server is present
    Given a fresh agency engine in code-mode
    And a target whose .mcp.json declares an external codegraph server
    When I write the install to that target twice
    Then the two .mcp.json contents are byte-identical

  Scenario: marketplace description names the live capability count
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then the marketplace description contains the word capabilities
    And the marketplace description contains the live capability count
    And the marketplace description is under 400 characters

  Scenario: help skill teaches both MCP form and bash fallback
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then the help SKILL.md contains mcp__plugin_agency_agency__execute
    And the help SKILL.md contains agency intent or agency execute
    And the help SKILL.md allowed-tools lists all three agency MCP tools

  Scenario: using-agency skill is generated with bootstrap chain
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then skills/using-agency/SKILL.md exists
    And the using-agency skill contains agency_welcome and intent_bootstrap
    And the using-agency skill allows mcp__plugin_agency_agency__execute

  Scenario: write prunes orphaned bin wrappers on regen
    Given a fresh agency engine in code-mode
    And install.write has been run once on a temporary directory
    When a fake orphan bin wrapper is planted and write is run again
    Then the orphan wrapper is removed
    And the real analyze-graph wrapper is still present

  Scenario: dry run does not write to disk
    Given a fresh agency engine in code-mode
    When I run install.main with --dry-run on a temporary target
    Then no files are written to the target
    And the dry-run output mentions SKILL.md or plugin.json

  Scenario: hook scripts are written executable
    Given a fresh agency engine in code-mode
    When I write the install to a temporary target
    Then hooks/session-start is executable
    And hooks/run-hook.cmd is executable

  Scenario: polyglot wrapper is generated with correct structure
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then hooks/run-hook.cmd starts with the polyglot marker
    And hooks/run-hook.cmd contains exec bash

  Scenario: plugin.json does not declare hooks to avoid duplicate-hooks error
    Given a fresh agency engine in code-mode
    When I generate the install manifest
    Then .claude-plugin/plugin.json does not contain a top-level hooks key
