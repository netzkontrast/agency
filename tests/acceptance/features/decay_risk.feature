Feature: decay-risk Finding shape — the Iron Law foundation (Spec 354)
  The brooks-lint port (Spec 353) teaches agency's Finding value object the
  Iron Law — Symptom → Source → Consequence → Remedy — plus a derived severity
  tier, backward-compatibly, and vendors the twelve decay risks as cited data so
  the decidable findings analyze already produces can be tagged with the risk
  code + book source they evidence. Observable through the Finding shape, the
  vendored data, and the decay tagger's output.

  # ── the Finding learns the Iron Law (backward-compatible) ────────────────────

  Scenario: the Iron Law fields default to empty (backward-compatible)
    Given a finding constructed with no Iron Law fields
    Then its risk_code, source, consequence, and remedy all default to empty
    And its legacy fields are unchanged

  Scenario: a finding preserves its Iron Law fields in full (no truncation)
    Given a finding constructed with a long remedy and the Iron Law fields
    Then risk_code, source, consequence, and remedy are preserved verbatim

  Scenario: to_dict emits the Iron Law keys additively
    Given a finding tagged with risk_code "R1"
    When I serialise it with to_dict
    Then the dict still carries the legacy keys
    And it also carries risk_code, source, consequence, and remedy

  Scenario: severity tier is derived from the canonical enum, not stored
    Given a finding with severity "fail"
    Then its rendered tier is "critical"
    And the dataclass has no second severity field

  Scenario: every severity maps to a brooks tier
    Then severity "fail" renders tier "critical"
    And severity "warn" renders tier "warning"
    And severity "info" renders tier "suggestion"

  # ── the vendored decay-risk knowledge (data, not prose-in-code) ──────────────

  Scenario: the vendored decay-risk data covers exactly the canonical risk set
    When I load the decay-risk data
    Then the built-in risks are exactly R1 through R6 and T1 through T6
    And the risk count is computed from the data, never a pinned literal

  Scenario: every decay risk carries its full diagnostic shape
    When I load the decay-risk data
    Then every risk defines name, diagnostic, consequence, remedy, symptoms, sources, severity_guide, and what_not_to_flag
    And every listed source cites a book and a principle
    And every severity_guide names a critical, warning, and suggestion band

  Scenario: the vendored data is drift-tracked to its upstream revision
    Then decay-risks.json carries a "_source" key naming the brooks-lint revision

  # ── the decidable→risk tagger (the bridge to judgment) ───────────────────────

  Scenario: a long-function finding is tagged R1 while its legacy fields stay intact
    Given a Python source file with a very long function
    When the quality scanner runs and its findings are decay-tagged
    Then the long-function finding keeps its legacy rule, severity, file, and line
    And it is tagged risk_code "R1" with a Source, Consequence, and Remedy

  Scenario: a decidable finding maps to its risk via the vendored data
    Given a Python package with a circular import between two modules
    When the architecture scanner runs and its findings are decay-tagged
    Then the import-cycle finding is tagged risk_code "R5"
    And its Source names a book from decay-risks.json
    And it carries a non-empty Consequence and Remedy

  Scenario: an analyze finding in no decidable list stays decidable-only
    Given a Python source file with one unused import
    When the quality scanner runs and its findings are decay-tagged
    Then the unused-import finding keeps an empty risk_code
    And it still carries its original message

  # ── the open set — custom Cx risks (§4; config merge lands in Spec 356) ───────

  Scenario: the risk registry is an open set — a custom Cx risk tags like a built-in
    Given a custom risk registry defining "C1" over the long-function rule
    When a long-function finding is decay-tagged against that registry
    Then the finding is tagged risk_code "C1" with the custom Source, Consequence, and Remedy

  # ── analyze.run records the enriched findings (the bridge wired in) ───────────

  Scenario: analyze.run records decidable findings already decay-tagged
    Given a fresh agency engine in code-mode
    And a confirmed intent
    And a Python package with a circular import between two modules
    When I run analyze on that package with axis "architecture"
    Then a recorded Finding node for the cycle carries risk_code "R5"
