Feature: Unified config is a live fallback for capability read paths (Spec 334 Slice 6)

  The unified .agency/config.yaml becomes a live but lowest-priority source for
  a capability's own config read path: cap-local nested file wins, then the
  unified file, then the built-in dataclass default.

  Scenario Outline: the unified file is a live fallback when no cap-local file exists
    Given no cap-local config for "<cap>"
    And the unified config sets "<cap>.content_root" to "/data/<cap>"
    When I load the "<cap>" config
    Then the loaded content_root is "/data/<cap>"

    Examples:
      | cap   |
      | novel |
      | music |

  Scenario: a cap-local file wins over the unified file
    Given a cap-local "novel" config with content_root "/local/novels"
    And the unified config sets "novel.content_root" to "/data/novels"
    When I load the "novel" config
    Then the loaded content_root is "/local/novels"

  Scenario: a per-key env var overrides the unified file for a capability key
    Given no cap-local config for "novel"
    And the unified config sets "novel.content_root" to "/data/novels"
    And the env var "AGENCY_NOVEL_CONTENT_ROOT" is "/env/novels"
    When I load the "novel" config
    Then the loaded content_root is "/env/novels"

  Scenario: with neither set the built-in default is returned
    Given no cap-local config for "novel"
    And the unified config is empty
    When I load the "novel" config
    Then the loaded content_root is the "novel" default

  Scenario: editing the unified file invalidates the cached load
    Given no cap-local config for "novel"
    And the unified config sets "novel.content_root" to "/data/v1"
    And I load the "novel" config
    When the unified config sets "novel.content_root" to "/data/v2"
    And I load the "novel" config
    Then the loaded content_root is "/data/v2"
