Feature: unified config doctor (Spec 328 Slice 4)
  agency_doctor reports each registered config key's resolved value + source
  (secrets redacted to presence), flags an invalid value in next_steps, and
  --write-config repairs a missing config non-destructively.

  Scenario: doctor reports the resolved config with sources
    Given a doctor engine with a clean config
    When agency_doctor runs
    Then the doctor config reports "frugal.level" from source "default"
    And the doctor config redacts every secret

  Scenario: doctor flags an invalid config value with a repair hint
    Given a doctor engine whose file sets frugal level to "turbo"
    When agency_doctor runs
    Then the doctor next_steps mention "frugal.level"
    And the doctor next_steps mention "write-config"

  Scenario: write-config repairs a missing config
    Given a doctor engine with a clean config
    When I run doctor with --write-config
    Then the project config exists
    And the project frugal level is "full"
