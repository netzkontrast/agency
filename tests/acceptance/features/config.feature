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
