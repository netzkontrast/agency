Feature: develop capability — scaffolding, linting, authoring walk, discipline cues
  The develop capability scaffolds new capabilities (Spec 016/024), lints them
  (Spec 023/024), walks the authoring-capabilities discipline, and cues
  critical-thinking intent methods from discipline phases (Spec 092 G4).
  All assertions are on observable verb outputs and file/graph state.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── develop.scaffold_capability ───────────────────────────────────────────

  Scenario: light scaffold emits a single .py file
    When I scaffold a capability named "mycap" with kind "light"
    Then a file named "mycap.py" is created in the output directory

  Scenario: medium scaffold emits a file with OntologyExtension stubs
    When I scaffold a capability named "midcap" with kind "medium"
    Then the output file contains "nodes="

  Scenario: heavy scaffold emits a folder with __init__.py and main module
    When I scaffold a capability named "bigcap" with kind "heavy"
    Then a folder named "bigcap" is created
    And the folder contains "__init__.py"
    And the folder contains "bigcap.py"

  Scenario: every scaffolded file begins with the agency-scaffold marker
    When I scaffold capabilities with kind "light" and kind "medium"
    Then each output file's first non-blank line is "# agency-scaffold: v1"

  Scenario: scaffold response carries the artefact shape
    When I scaffold a capability named "acap" with kind "light"
    Then the response has a "result" field with the file path
    And the response "artefact" has kind "capability-scaffold"
    And the artefact scaffold_version is 1

  Scenario: unknown kind returns the input-required shape
    When I scaffold a capability named "ucap" with kind "WRONG"
    Then the scaffold response status is "input-required"
    And "kind" is listed in resume_with

  # ── plugin.lint_capability ────────────────────────────────────────────────

  Scenario: a scaffolded capability with missing docstring markers fails lint in block mode
    When I lint a broken scaffolded capability
    Then the lint mode is "block"
    And lint ok is false
    And at least one "structural" violation is reported

  Scenario: a clean scaffolded capability passes lint in block mode
    When I lint a clean scaffolded capability
    Then the lint mode is "block"
    And lint ok is true
    And no violations are reported

  Scenario: a legacy capability with violations warns but does not block
    When I lint a legacy capability with violations
    Then the lint mode is "warn"
    And lint ok is true
    And the warnings list is non-empty
    And the violations list is empty

  Scenario: a transform-role verb importing a network library triggers role_tag
    When I lint a transform capability that imports requests
    Then "role_tag" appears in the lint findings

  Scenario: a verb with an empty docstring triggers render_slice
    When I lint a scaffolded capability with an empty verb docstring
    Then "render_slice" appears in the lint findings

  Scenario: the lint return always includes ok, violations, warnings, skipped and mode
    When I lint any capability
    Then the lint result has keys "ok", "violations", "warnings", "skipped", and "mode"

  Scenario: a scaffold-generated capability lints clean in block mode
    When I scaffold a capability named "zcap" with kind "light"
    And I lint the scaffolded capability
    Then the lint mode is "block"
    And lint ok is true

  # ── authoring-capabilities discipline walk (Spec 024) ─────────────────────

  Scenario: walking the authoring-capabilities skill records a Reflection that SERVES the intent
    When I walk the authoring-capabilities discipline to completion
    Then a Reflection node exists in the graph
    And its text mentions both the capability name and the discipline name

  Scenario: phase 2 of the authoring walk creates the scaffold file on disk
    When I walk the authoring-capabilities discipline through phase 2
    Then the scaffolded file exists on disk

  Scenario: phase 6 is a hard gate that blocks without explicit confirmation
    When I walk to phase 6 of the authoring-capabilities discipline without confirming
    Then the response status is "input-required"

  # ── develop disciplines cue intent methods (Spec 092 G4) ──────────────────

  Scenario: plan skill cues intent.premortem
    When I inspect the cued verbs in the "plan" discipline
    Then "intent.premortem" is in the cue set

  Scenario: spec-panel skill cues intent.steelman
    When I inspect the cued verbs in the "spec-panel" discipline
    Then "intent.steelman" is in the cue set

  Scenario: brainstorm skill cues intent.tradeoffs
    When I inspect the cued verbs in the "brainstorm" discipline
    Then "intent.tradeoffs" is in the cue set

  Scenario: cued intent methods can actually be invoked and return results
    When I invoke the premortem method cued by the plan discipline
    Then the result method is "premortem"
    And the result has at least one step

  Scenario: cued discipline skills are walkable
    When I walk each of the "plan", "spec-panel", and "brainstorm" disciplines
    Then each walk returns a valid terminal status

  Scenario: develop.index produces a repo briefing via the ported indexer
    When I call develop.index on the agency repo
    Then the develop index result carries an index_id
    And the develop index token count is positive

  Scenario: port_plugin ingests an external plugin's prompts and maps coverage
    Given an external plugin directory with command files "analyze", "brainstorm", and "frobnicate"
    When I call develop.port_plugin on that directory
    Then the port result ingests three Documents
    And the port gap-map covers "analyze" and flags "frobnicate" as a gap
    And the external files are left without an anchor
