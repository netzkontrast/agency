Feature: Pillar event bus — declarative subscriptions (Spec 349b)
  A capability declares its event interest as DATA (`subscriptions = [...]`) and
  one engine-bootstrap loop registers every handler — replacing scattered
  import-time `subscribe` calls. Subscribers run in ascending priority order.

  Scenario: a capability's declared subscription is registered at bootstrap
    Given a fresh agency engine for the bus
    Then the bus has a subscription named "frugal.first_use" for "PreToolUse"

  Scenario: subscribers fire in ascending priority order
    Given two bus subscribers registered with priorities 70 and 30
    When the priority event is run
    Then the lower-priority fragment comes first
