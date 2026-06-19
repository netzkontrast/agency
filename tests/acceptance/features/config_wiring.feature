Feature: unified config wiring — generation points (Spec 334 Slice 3)
  The annotated .agency/config.yaml is generated at install/setup and repaired at
  SessionStart — zero manual steps, non-destructive. A hook never CREATES a config
  in an arbitrary cwd (it only repairs an existing one); creation is install/setup.

  Scenario: agency install scaffolds the annotated config
    Given a clean project directory
    When agency scaffolds the project
    Then the project config exists
    And the project frugal level is "full"
    And the project config lists every registered key

  Scenario: SessionStart repairs an existing config — adds a new section, keeps edits
    Given a clean project directory
    And the project config has been scaffolded
    And the user edits the project frugal level to "ultra"
    And a new capability registers a config section "demo3" key "x" default "one"
    When a SessionStart hook fires for the project
    Then the project config lists "demo3.x"
    And the project frugal level is "ultra"

  Scenario: SessionStart never creates a config from a hook
    Given a clean project directory
    When a SessionStart hook fires for the project
    Then the project config does not exist
