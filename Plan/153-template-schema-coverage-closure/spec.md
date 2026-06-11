---
spec_id: "153"
slug: template-schema-coverage-closure
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "004"
depends_on: ["004", "060", "032", "149"]
vision_goals: [4, 7]
affects:
  - agency/_templates.py
  - agency/_lints/_schema_coverage.py
  - tests/test_template_schema_coverage.py
---

# Spec 153 — Template/schema coverage closure

## Why

Spec 004 (wire the generate/validate loop for uncovered node kinds) is
Not Started. Spec 060 shipped the substrate (loader + dataclasses +
materialiser) + 15 schema files + 7 template files, but Phase 5 (verb
migration to `ctx.template()`) is opt-in and most node kinds still have
NO schema — so the generate/validate pair (CORE.md §"Schemas &
templates") is half-wired. This closes the coverage gap with a derived
audit, not a hand-maintained list.

## Done When

- [ ] **`_check_schema_coverage` audit** lists every node label the
      live ontology declares vs every label with a Schema; the delta is
      the uncovered set (derived — Spec 149, rule 8). Typed shape:
      `{covered: list[Label], uncovered: list[Label], coverage_fraction:
      float, priority_uncovered: list[(Label, node_count)]}`.
- [ ] **`agency_doctor` reports `schema_coverage`** as a fraction.
- [ ] **Schemas authored for the highest-traffic uncovered kinds**
      (the audit ranks by graph node-count — derive the priority).
- [ ] **`generate → validate` round-trip test** per newly-covered kind:
      a Template renders an Artefact a Schema validates; a missing field
      fails (the CORE.md proven-runnable pattern, extended).
- [ ] **Measurable invariants** (rule 8):
      (a) `schema_coverage.fraction >= floor` (monotone non-decreasing,
      floor = last shipped); (b) for every node label with ≥ 1 live
      graph node, a Schema exists OR the label is tagged
      `# AGENCY-SCHEMA-DEFERRED: <reason>` (no silent gaps);
      (c) every Schema has ≥ 1 Template that round-trips against it
      (covered_schemas ⊆ template_renderable_schemas).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  ontology declares node label "Reflection" with 1,403 live nodes
        and no Schema authored
When:   _check_schema_coverage runs
Then:   uncovered includes "Reflection";
        priority_uncovered ranks it near the top by node_count;
        agency_doctor.schema_coverage.fraction < 1.0

Given:  a "Reflection" Schema + Template are authored
When:   the round-trip test runs (template renders → schema validates →
        material round-trips back to dict)
Then:   passes; coverage_fraction increases monotonically; floor advances
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Schema without Template | author Schema, skip Template | invariant (c) — round-trip gate | block CI; require paired Template |
| Speculative Schema | Schema for a label with 0 live nodes | priority ranking surfaces low value | tag `# AGENCY-SCHEMA-SPECULATIVE` so it doesn't inflate fraction |
| Coverage regression on label rename | label renamed without Schema migration | invariant (a) — monotone floor | block; require explicit migration step |
| LLM-generated nodes bypass Schema | a Driver (Spec 147) emits raw dicts directly into the graph | round-trip gate (c) catches missing Schema; typed `Codes.SCHEMA_MISSING` at write | all graph writes go through generate→validate; no direct dict insertion |

## Interconnects

- **Drift-derivation chain** (149): `schema_coverage` is derived.
- Spec 060 (templates-schemas) is the substrate this exercises.
- Spec 152 (typed Skill/Phase) is the parse-side sibling of this
  generate/validate discipline.
- Spec 151 (Codes coverage) supplies `Codes.SCHEMA_MISSING` /
  `Codes.TEMPLATE_RENDER_FAILED` for the round-trip surface.
- Spec 157 (architecture-drift gate) treats `schema_coverage.fraction`
  as one of its standing monotone invariants.
- Spec 159 (dogfood collect deprecation) closes the markdown-parse
  anti-pattern — the schema/template pair is the IN-substrate replacement.
- Spec 154 (output-overflow) — overflow Artefacts are themselves a node
  kind that needs a Schema; this audit covers them uniformly.
- Spec 158 (capability scaffold) — scaffold-marked capabilities are
  expected to declare Schemas for any node kind they emit.
- **LLM-driver chain** (147): generate-side validation gives the
  Driver typed `output_config.format` to write structured outputs
  against; without Schemas the Driver falls back to freeform text.

## Open questions

1. Author all uncovered schemas, or only graph-present kinds?
   **Recommend**: only kinds with ≥1 live node first (the rest are
   speculative); the audit ranks by count.
2. Schema versioning policy — pin per spec or float? **Recommend**:
   float with a `schema_version` field in the prefix (Spec 146) so a
   schema bump invalidates the cache deliberately, never silently.
