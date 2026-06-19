Feature: multi-agent self-installer (Spec 327)
  agency installs itself across agent runtimes — one surface_card projected into
  each agent's native format; idempotent fenced-block merge that never clobbers
  user content; per-adapter independent report; uninstall removes only the block.

  Scenario: install into a clean Cursor project
    Given a clean installer project
    When I install agency for agent "cursor"
    Then the cursor rules file exists with valid frontmatter
    And the cursor file contains the frugal discipline
    And the cursor file contains the agency CLI entry pointer
    And the cursor file does not inline the full verb index
    And the cursor file carries the pipx bootstrap line

  Scenario: re-install is idempotent — one block, never duplicated
    Given a clean installer project
    And agency is installed for agent "cursor"
    When I install agency for agent "cursor" again
    Then the cursor file has exactly one agency block

  Scenario: merge into an existing unfenced file preserves user content
    Given a clean installer project
    And a user-authored copilot instructions file
    When I install agency for agent "copilot"
    Then the user content is preserved
    And an agency block is appended to the copilot file

  Scenario: uninstall removes only the agency block
    Given a clean installer project
    And a user-authored copilot instructions file
    And agency is installed for agent "copilot"
    When I uninstall agency for agent "copilot"
    Then the user content is preserved
    And no agency block remains in the copilot file

  Scenario: install all agents reports each adapter independently
    Given a clean installer project
    When I install agency for all instruction agents
    Then every requested adapter is reported
    And the cursor and agents adapters succeeded

  Scenario: the card is the single source — adapters carry the live discipline
    Given a clean installer project
    When I install agency for agent "windsurf"
    Then the windsurf file's discipline matches the live frugal render

  Scenario: agency_install installs an agent over the wire and the doctor reports it
    Given a clean installer project
    When I call agency_install for agent "cursor" over the wire
    Then the cursor rules file exists with valid frontmatter
    And the doctor lists cursor as an installed agent

  # Spec 327 Slice 5 — drift guard: no adapter copy may silently drop the floor.
  Scenario: every adapter projection carries the safety floor
    Given a clean installer project
    When I install agency for all instruction agents
    Then every installed agent file carries every safety-floor marker
