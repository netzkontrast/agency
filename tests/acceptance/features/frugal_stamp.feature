Feature: frugal M2 — per-verb envelope stamp (Spec 326 Slice 2)
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

  Scenario: agency_welcome carries the frugal stamp in its prefix
    Given a frugal wire engine at the default level
    When agency_welcome returns over the wire
    Then the welcome prefix carries the frugal stamp
