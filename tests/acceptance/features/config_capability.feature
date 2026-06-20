Feature: User-facing config capability (Spec 334 Slice 8)

  A thin `config` capability exposes get / set / list over the unified config so
  an agent (or the CLI) can read and persist values without hand-editing the file.

  Scenario: get resolves a registered key with its source
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I get config "core.embedder"
    Then the config result value is "tfidf" with source "default"

  Scenario: set persists a value and get reflects it
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I set config "frugal.level" to "lite"
    And I get config "frugal.level"
    Then the config result value is "lite" with source "file"

  Scenario: list reports registered keys with sources and redacts secrets
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I list config
    Then the config listing includes "core.db_path"
    And the secret "secrets.jules_api_key" is redacted in the listing

  Scenario: set refuses a secret key
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I set config "secrets.jules_api_key" to "leak"
    Then the config result is an error mentioning "secret"

  Scenario: get on an unregistered key errors cleanly
    Given a fresh agency engine in code-mode
    And a confirmed intent
    When I get config "nope.missing"
    Then the config result is an error mentioning "unregistered"
