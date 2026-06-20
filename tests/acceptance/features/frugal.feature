Feature: frugal core discipline — level + render (Spec 332 Slice 1)
  The minimal-code discipline's active level resolves via Spec 334 config
  (default full); render() emits the ladder + the non-negotiable safety floor;
  off emits nothing; the compact render is token-bounded but still names the floor.

  Scenario: default level is full
    Given no AGENCY_FRUGAL_LEVEL and an empty config file
    When I read the frugal level
    Then the level is "full"

  Scenario: env sets the level
    Given no AGENCY_FRUGAL_LEVEL and an empty config file
    And the env var AGENCY_FRUGAL_LEVEL is "ultra"
    When I read the frugal level
    Then the level is "ultra"

  Scenario: an invalid level falls back to full
    Given no AGENCY_FRUGAL_LEVEL and an empty config file
    And the env var AGENCY_FRUGAL_LEVEL is "turbo"
    When I read the frugal level
    Then the level is "full"

  Scenario: set persists the level across a fresh read
    Given no AGENCY_FRUGAL_LEVEL and an empty config file
    When I set the frugal level to "lite"
    Then a fresh read of the frugal level is "lite"

  Scenario: the full render carries the ladder and the safety floor
    When I render the discipline at "full"
    Then the render contains "YAGNI"
    And the render contains every safety-floor marker

  Scenario: the compact render is short and names the floor
    When I render the discipline at "full" compact
    Then the compact render is at most 200 characters
    And the compact render contains "floor"

  Scenario: off renders nothing
    When I render the discipline at "off"
    Then the render is empty

  Scenario: a prompt injects the frugal discipline at the default level (M1)
    Given a frugal engine with no level override
    When a UserPromptSubmit event fires
    Then the injected text contains "YAGNI"
    And the injected text contains "floor"

  Scenario: off injects no frugal discipline into the prompt (M1)
    Given a frugal engine with level "off"
    When a UserPromptSubmit event fires
    Then the injected text does not contain "YAGNI"

  Scenario: a session start injects the full discipline (M1)
    Given a frugal engine with no level override
    When a SessionStart event fires
    Then the injected text contains every safety-floor marker

  Scenario: a session start injects the COMPLETE frugal help by default (Spec 348)
    Given a frugal engine with no level override
    When a SessionStart event fires
    Then the injected text contains "YAGNI"
    And the injected text contains "Intensity levels (active:"
    And the injected text contains "Switch the level"
    And the injected text contains every safety-floor marker

  Scenario: session_inject discipline injects only the ladder and floor
    Given a frugal engine with session_inject "discipline"
    When a SessionStart event fires
    Then the injected text contains "YAGNI"
    And the injected text does not contain "Intensity levels (active:"

  Scenario: session_inject off injects no frugal at session start
    Given a frugal engine with session_inject "off"
    When a SessionStart event fires
    Then the injected text does not contain "YAGNI"
