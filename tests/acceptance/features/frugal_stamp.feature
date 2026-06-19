Feature: frugal M2 — per-verb envelope stamp (Spec 332 Slice 2)
  The compact frugal discipline rides every capability verb's wire return in a
  byte-stable stamp; off omits it; it degrades silently; agency_welcome carries
  it in its cache-stable prefix.

  Scenario: a capability verb return carries the compact frugal stamp
    Given a frugal wire engine at the default level
    When a capability verb returns over the wire
    Then the wire return carries a frugal stamp naming the floor
    And the frugal stamp is byte-identical on a repeat call

  Scenario: off omits the per-verb stamp
    Given a frugal wire engine at level "off"
    When a capability verb returns over the wire
    Then the wire return has no frugal stamp

  # Spec 332 C6 — any render failure degrades silently; the verb still succeeds.
  Scenario: a broken render degrades silently — the verb is unaffected
    Given a frugal wire engine at the default level
    And the frugal render is broken
    When a capability verb returns over the wire
    Then the wire return has no frugal stamp
    And the wire return is otherwise intact

  Scenario: agency_welcome carries the frugal stamp in its prefix
    Given a frugal wire engine at the default level
    When agency_welcome returns over the wire
    Then the welcome prefix carries the frugal stamp

  # Spec 332 Slice 5 — out of the box the doctor surfaces the discipline status
  Scenario: the doctor reports the frugal discipline is live
    Given a frugal wire engine at the default level
    When agency_doctor returns over the wire
    Then the doctor reports frugal level "full"
    And the doctor reports the per-verb stamp active
