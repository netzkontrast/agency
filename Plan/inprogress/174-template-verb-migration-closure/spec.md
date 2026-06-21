---
spec_id: "174"
slug: template-verb-migration-closure
status: draft
state: inprogress
last_updated: 2026-06-10
owner: "@agency"
enhances: "060"
depends_on: ["060", "153", "032", "149"]
vision_goals: [4, 7]
affects:
  - agency/capabilities/jules/_main.py
  - agency/capabilities/document/_main.py
  - agency/capabilities/analyze/_main.py
  - tests/test_template_verb_migration.py
---

# Spec 174 — template verb-migration closure (Phase 5)

## Why

Spec 060 (templates-schemas-agent-instructions) is "Mostly shipped" —
Phases 1+2+3+4+6 complete, but "Phase 5 (verb migration to
`ctx.template()`) remains as opt-in: dogfood.render migrated;
jules._main.preambles + document.explain + analyze.run/improve can flip
when iteration pressure justifies." The enhancement-wave pressure now
justifies it: a migrated verb renders from a vendored Template (Goal 7,
files-render-from-graph) instead of an inline literal, and Spec 153
closed schema coverage so the validate side is ready.

## Done When (measurable invariants — rule 8)

- [ ] **Typed migration record: `MigrationVerdict{verb_id,
      template_node_id, schema_node_id, status: Literal["migrated",
      "pending", "deferred"], inline_literal_count: int}`** — one per
      target verb; queryable graph node.
- [ ] **Invariant: `inline_literal_count == 0`** for every `migrated`
      verb — derived AST sweep (CLAUDE.md derivability rule 2).
- [ ] **Invariant: every migrated verb's output has a
      `VALIDATES_AGAINST` edge to a Schema node** (Spec 153 coverage)
      — generate/validate pair is whole; absence fails CI.
- [ ] **Invariant: `set(migrated_verbs) ⊇ {jules.preambles,
      document.explain, analyze.run, analyze.improve}`** — the four
      Phase-5 targets; new targets can join the set (open-set, rule 5).
- [ ] **Invariant: Template + Schema versions match per-render** —
      a render reads `template.version`; the corresponding Schema's
      `version` field must equal it or fall within a documented
      compatibility window. Drift fails `Codes.TEMPLATE_SCHEMA_VERSION_SKEW`.
- [ ] **Relationship: removing a Template field that the Schema
      requires breaks the validate test** — proves the pair tightly
      coupled; not pinned to a specific field.
- [ ] **Failure mode (render path):** a Template missing a required
      placeholder fails fast with `Codes.TEMPLATE_MISSING_FIELD`
      pointing at the placeholder name; render never produces a
      half-substituted string.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  pre-migration document.explain returns an f-string literal
        with three interpolated fields {summary, examples, refs}
When:   PR flips document.explain to `ctx.template("document.explain",
        summary=..., examples=..., refs=...)` + adds a Schema
        `document.explain.v1` declaring all three fields required
Then:   migrated verb's output validates AGAINST Schema (PRODUCES +
        VALIDATES_AGAINST edges both land); inline_literal_count == 0
        for the verb; MigrationVerdict.status flips to "migrated"

Given:  someone edits the Template to drop the `refs` placeholder
        without bumping the Schema
When:   render runs
Then:   validate fails — Schema requires `refs`, render output missing;
        verb errors with Codes.TEMPLATE_MISSING_FIELD pointing at "refs";
        Spec 149 drift gate catches the version skew

Given:  jules.preambles ships its migration PR; document/analyze still
        pending
When:   MigrationVerdict audit runs
Then:   jules.preambles.status=="migrated"; others=="pending"; 174
        TODO row stays Partial until all four flip
```

## Failure modes

| Failure | Migration response |
|---|---|
| Template missing a Schema-required field | `TEMPLATE_MISSING_FIELD` at render |
| Schema added without a Template | `SCHEMA_NO_TEMPLATE` (Spec 153 sibling) |
| Inline literal sneaks back into a migrated verb | `inline_literal_count > 0` → drift fail |
| Template/Schema version skew | `TEMPLATE_SCHEMA_VERSION_SKEW` |
| Render output > Spec 154 body budget | Spec 146 envelope guards — body truncates, prefix never |

## Interconnects

- Spec 153 (schema coverage) is the validate-side prerequisite + the
  generate/validate pair-completion.
- Spec 060 is the parent substrate; Spec 032 + Spec 153 the schema
  layer.
- Spec 165 (micro-extensions closure) is the sibling
  closure-of-a-partial pattern.
- Spec 149 (derive doctrine) audits inline_literal_count + version
  skew.
- Spec 146 (envelope) — render output is body, never prefix.
- Spec 170 (doctor) reports `template_migration_status` (derived per
  verb).
- Spec 151 (Codes coverage) supplies `TEMPLATE_MISSING_FIELD`,
  `TEMPLATE_SCHEMA_VERSION_SKEW`, `SCHEMA_NO_TEMPLATE`.

## Open questions

1. Migrate all four now or stage? **Recommend**: stage by capability
   (one PR each) to keep blast radius small — Spec 060's own pattern.
2. Template versioning — semver or content-hash? **Recommend**:
   content-hash (derived; no manual bump); Schema declares the
   accepted hash range.
3. Deprecate `analyze.run`'s old literal path immediately or
   keep a one-cycle WARN? **Recommend**: one-cycle WARN (Spec 056/058
   promotion pattern); flip to error when the migration audit shows
   zero literal calls.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the wave-1 typed-shape batch-2 (intent:2219e694; engine-driven tdd walk).

### Done — Slice 1 (typed shape)

Typed frozen dataclass + `__post_init__` invariants in
`agency/_typed_shapes_wave1_part2.py`; tests in
`tests/test_typed_shapes_wave1_part2.py` (17 tests total across the
8-spec batch). Slice 2 wires each shape into its consuming runtime
(red-team rerunner, CLI projection, derive audit, wrapper modules,
networkx metric, axis registry, migration walker, ref audit).

### Still — Slice 2+

See the spec's main "Done When" + "Still" sections.

