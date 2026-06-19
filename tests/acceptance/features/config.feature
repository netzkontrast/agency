Feature: unified config — .agency/config.yaml resolver + registry (Spec 328)
  config_resolve resolves a registered key as env > file > built-in default;
  config_set persists to the file; capabilities register sections so the file is
  the union of all live config.

  Scenario: default when no env and no file
    Given a registered config key "demo.color" default "blue" env "DEMO_COLOR"
    And a clean env and an empty config file
    When I resolve "demo.color"
    Then the value is "blue" with source "default"

  Scenario: file overrides default
    Given a registered config key "demo.color" default "blue" env "DEMO_COLOR"
    And a clean env and an empty config file
    And the config file sets "demo.color" to "green"
    When I resolve "demo.color"
    Then the value is "green" with source "file"

  Scenario: env overrides file and default
    Given a registered config key "demo.color" default "blue" env "DEMO_COLOR"
    And a clean env and an empty config file
    And the config file sets "demo.color" to "green"
    And the env var DEMO_COLOR is "red"
    When I resolve "demo.color"
    Then the value is "red" with source "env"

  Scenario: set persists and a fresh read sees it
    Given a registered config key "demo.color" default "blue" env "DEMO_COLOR"
    And a clean env and an empty config file
    When I set "demo.color" to "violet"
    Then resolving "demo.color" gives "violet" with source "file"

  Scenario: a registered key appears in the registered set
    Given a registered config key "demo.color" default "blue" env "DEMO_COLOR"
    And a clean env and an empty config file
    Then "demo.color" is in the registered keys

  # Spec 328 Slice 2 — the annotated scaffold generator (config_scaffold)
  Scenario: scaffold writes every registered key at its default with comments
    Given a clean env and an empty config file
    When I scaffold the config
    Then the config file lists every registered key
    And the frugal level line carries a comment
    And the frugal level default is "full"

  Scenario: scaffold renders secrets as env references, never literals
    Given a clean env and an empty config file
    When I scaffold the config
    Then every secret key is written as an env reference

  Scenario: re-scaffold is non-destructive — user edits and comments survive
    Given a clean env and an empty config file
    And the config has been scaffolded
    And the user edits the frugal level to "ultra" with a "# my note" comment
    When I scaffold the config again
    Then the frugal level is still "ultra"
    And the comment "# my note" is preserved

  Scenario: scaffold appends a newly registered section without clobbering
    Given a clean env and an empty config file
    And the config has been scaffolded
    And the user edits the frugal level to "ultra" with a "# my note" comment
    And a new capability registers a config section "demo2" key "color" default "teal"
    When I scaffold the config again
    Then the config file lists "demo2.color"
    And the frugal level is still "ultra"
    And the comment "# my note" is preserved

  # Spec 328 — a secret resolves env → default, NEVER the file ${env:} placeholder.
  Scenario: a secret never resolves to the file placeholder
    Given a clean env and an empty config file
    And the JULES_API_KEY env is unset
    And the config has been scaffolded
    When I resolve "secrets.jules_api_key"
    Then the secret value is empty with source "default"

  # Spec 328 — repair must NOT append to a corrupt config (would doubly-break it).
  Scenario: scaffold leaves a corrupt config untouched
    Given a clean env and an empty config file
    And the config file is corrupt
    When I scaffold the config
    Then the config file is unchanged

  # Spec 328 Slice 5 — open-set proof: config_scaffold SELF-registers capability
  # config via its glob (NO explicit import here), so a fresh install emits their
  # sections. If the glob regressed, nothing would register novel/music and these
  # assertions would fail.
  Scenario: scaffold self-registers a capability's config section
    Given a clean env and an empty config file
    When I scaffold the config
    Then the config file lists "novel.default_genre"
    And the config file lists "music.db_backend"
