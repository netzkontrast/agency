Feature: Template and schema bootstrap — loading, lint, and coverage audit
  File-discovered templates and schemas are merged into the engine ontology at
  bootstrap. The template folder lint rule requires AGENT instruction blocks.
  The schema coverage audit reports covered/uncovered node kinds.

  Background:
    Given a fresh agency engine in code-mode

  # ── bootstrap wiring ─────────────────────────────────────────────────────────

  Scenario: file-discovered templates are available after bootstrap
    Given an extra capability with a templates folder containing "greeting.md"
    When I boot the engine with that capability
    Then "greeting" is reachable via the engine ontology templates

  Scenario: file-discovered schemas are available after bootstrap
    Given an extra capability with a schemas folder containing "greeter-payload.json"
    When I boot the engine with that capability
    Then "greeter-payload" is reachable via the engine ontology schemas

  Scenario: ctx.template returns the template for a known name
    Given an extra capability with a templates folder containing "greeting.md"
    When I boot the engine with that capability
    Then ctx.template("greeting") returns a template with the expected body

  Scenario: ctx.template raises for an unknown name
    Given an extra capability with a templates folder containing "greeting.md"
    When I boot the engine with that capability
    Then ctx.template("missing") raises KeyError

  Scenario: a schema declared in both dict and file raises at bootstrap
    Given an extra capability with a colliding schema in both OntologyExtension and file
    Then bootstrapping the engine raises ValueError mentioning the collision

  # ── template folder lint rule ─────────────────────────────────────────────────

  Scenario: lint passes when all templates carry an AGENT instruction block
    Given a capability whose template "greeting.md" has an AGENT instruction block
    Then lint_capability reports no template_folder findings

  Scenario: lint flags a template without an AGENT instruction block
    Given a capability whose template "silent.md" has no AGENT instruction block
    Then lint_capability reports a template_folder finding mentioning "silent.md"

  Scenario: lint flags a template with a non-kebab-case filename
    Given a capability whose template is named "BadName.md" with an AGENT block
    Then lint_capability reports a template_folder finding about kebab-case

  Scenario: lint flags when the templates folder does not exist
    Given a capability whose render_templates points to a nonexistent folder
    Then lint_capability reports a template_folder finding about missing folder

  Scenario: lint is silent for a capability with no render_templates declared
    Given a capability with no render_templates attribute
    Then lint_capability reports no template_folder findings

  # ── schema coverage audit ─────────────────────────────────────────────────────

  Scenario: schema coverage audit returns a coverage report
    Given a schemas folder with "intent.json" and ontology labels {"Intent", "Reflection"}
    When I run the schema coverage audit
    Then "Intent" is covered and "Reflection" is uncovered
    And the coverage fraction is between 0.0 and 1.0

  Scenario: an empty ontology yields full coverage
    Given an empty ontology labels set
    When I run the schema coverage audit
    Then the coverage fraction is 1.0

  Scenario: a schema whose label is not in the ontology is a non-node schema
    Given a schemas folder with "wire.json" titled "GateOutcome" and ontology labels {"Gate"}
    When I run the schema coverage audit
    Then "GateOutcome" is in non_node_schemas and coverage is 0.0

  Scenario: covered is always a subset of ontology labels
    Given a mix of node and non-node schemas in the folder
    When I run the schema coverage audit
    Then the covered set is a subset of the ontology labels

  Scenario: the live tree audit runs without crashing
    When I run the schema coverage audit against the live agency tree
    Then the result is a CoverageReport with valid covered, uncovered, and fraction fields

  # ── schema coverage baseline (Slice 2) ────────────────────────────────────────

  Scenario: the committed baseline matches the live uncovered set exactly
    When I run the live audit and compare to the committed baseline
    Then there are no new uncovered labels
    And there are no newly-covered labels still in the baseline

  # ── schema coverage backfill (Slice 6) ────────────────────────────────────────

  Scenario: the core substrate provenance labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the core provenance labels are all schema-covered

  Scenario: the core provenance schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the core provenance labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 cont.) ─────────────────────────────────

  Scenario: the document-convergence labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the document convergence labels are all schema-covered

  Scenario: the document-convergence schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the document convergence labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 — workflow-spine wave) ─────────────────

  Scenario: the workflow-spine labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the workflow spine labels are all schema-covered

  Scenario: the workflow-spine schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the workflow spine labels each have a loaded ontology schema

  # ── schema coverage Slice 4 — engine-load intersection gate ──────────────────

  Scenario: a schema file not declared by the capability goes to dormant_schemas, not covered
    Given a capability with a schema file for "Dormant" but no artefact_schemas declaration
    When I run the schema coverage audit with engine_loaded_titles excluding "Dormant"
    Then "Dormant" is in dormant_schemas and not in covered

  Scenario: the live tree has no dormant schemas — all on-disk schemas are engine-loaded
    When I run the live schema audit with engine-load intersection
    Then there are no dormant schemas

  # ── schema coverage backfill (Slice 6 — discover-prompt wave) ────────────────

  Scenario: the discover-prompt labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the discover-prompt labels are all schema-covered

  Scenario: the discover-prompt schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the discover-prompt labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 — prompt-dossier + document + jules wave) ─

  Scenario: the prompt-dossier + document + jules labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the prompt-dossier-document-jules labels are all schema-covered

  Scenario: the prompt-dossier + document + jules schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the prompt-dossier-document-jules labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 — analyze + select wave) ───────────────

  Scenario: the analyze-select labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the analyze-select labels are all schema-covered

  Scenario: the analyze-select schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the analyze-select labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 — foundational-service wave) ───────────

  Scenario: the foundational-service labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the foundational service labels are all schema-covered

  Scenario: the foundational-service schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the foundational service labels each have a loaded ontology schema
  # ── schema coverage backfill (Slice 6 — research + develop-extras wave) ──────

  Scenario: the research-develop-extras labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the research-develop-extras labels are all schema-covered

  Scenario: the research-develop-extras schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the research-develop-extras labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 — recommend + mode + panel + thinking wave) ─

  Scenario: the recommend-mode-panel-thinking labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the recommend-mode-panel-thinking labels are all schema-covered

  Scenario: the recommend-mode-panel-thinking schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the recommend-mode-panel-thinking labels each have a loaded ontology schema

  # ── schema coverage backfill (Slice 6 — plugin + persona + doctrine + dogfood wave) ─

  Scenario: the plugin-persona-doctrine-dogfood labels are schema-covered
    When I run the schema coverage audit against the live agency tree
    Then the plugin-persona-doctrine-dogfood labels are all schema-covered

  Scenario: the plugin-persona-doctrine-dogfood schemas are loaded + enforced by the engine
    When I boot the live engine
    Then the plugin-persona-doctrine-dogfood labels each have a loaded ontology schema
