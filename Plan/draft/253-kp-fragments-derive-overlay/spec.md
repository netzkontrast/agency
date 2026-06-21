---
spec_id: "253"
slug: kp-fragments-derive-overlay
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "143"
depends_on: ["143", "239", "147", "149", "146", "248", "150"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/data/kp-fragments.yaml
  - tests/test_kp_fragments_derive.py
---

# Spec 253 — KP fragments: derived overlay + coverage lint

## Why

Spec 143 vendors ~60 KP-derived fragments across 6 families. Like Spec
239 generalizes for Dramatica fragments, the KP overlay should derive
the per-novel overlay from project-specific node properties (alter
names, mode-block labels, reveal-channels). Author authors ONCE per
slug; rest derive.

## Done When

- [ ] **`prompt.derive_overlay_fragments(novel_id) -> OverlayFragmentSet`** —
      typed return `OverlayFragmentSet{ novel_id, fragments: dict[
      FragmentSlug, FragmentBody], coverage: {derived: int,
      placeholder: int, missing: int, total: int}, source_property_map:
      dict[FragmentSlug, list[NodePropertyRef]], derived_at: datetime }`.
      Author authors per-slug source rules ONCE; per-novel bodies derive.
- [ ] **Invariant: coverage is a relationship, not a count** — the
      lint enforces `coverage.missing == 0` (every KP-substrate node
      has a fragment OR placeholder), NOT a pinned `derived == 60`.
      Adding a slug or KP-substrate node updates the count; the
      relationship stays valid.
- [ ] **Invariant: derivation is pure-function over graph** —
      `derive_overlay_fragments(novel_id)` is deterministic given the
      novel's graph state at time T; re-running produces byte-identical
      output. Property test asserts idempotence over two consecutive
      calls.
- [ ] **Invariant: source_property_map is queryable** — every derived
      fragment ships with the list of NodeProperties it was derived
      from; rename/delete a property → drift caught by Spec 149
      (`check-doc-drift`), not silent staleness.
- [ ] **Invariant: vendored KP corpus is a fixture, not a snapshot** —
      the test "derive overlay reproduces vendored KP corpus" asserts
      the FORMAL EQUIVALENCE (each fragment's substrate sources match);
      cosmetic prose drift in the vendored corpus does NOT fail the
      test (the corpus updates via Spec 150 amendments, not pinning).
- [ ] **Lint runs in `check-doc-drift`** (Spec 149) — missing
      coverage = lint failure; CI gates.
- [ ] **Failure modes**: graph property type mismatch (e.g. Alter.
      taboo_rules expected list but author wrote dict) → derivation
      fails CLOSED with `Codes.OVERLAY_PROPERTY_SHAPE` (Spec 151),
      naming the property; novel with zero KP-substrate nodes →
      empty overlay, NOT error; cache-stable across re-derivation —
      sorted fragment slugs for byte-stability (Spec 146); when an
      author-edited overlay diverges from derivation, surface the
      diff (don't silently overwrite).
- [ ] Test: derive overlay reproduces vendored KP corpus on a
      fixture; adding a new KP-substrate node auto-extends the
      overlay; renaming a sourced property triggers Spec 149 lint.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel with 3 alters (each with taboo_rules), 2 mode-blocks
        (with labels), and 4 reveal-channels; the KP corpus declares
        slug "alter-taboo" sourced from Alter.taboo_rules
When:   prompt.derive_overlay_fragments(novel_id) runs; then the
        author renames Alter.taboo_rules to Alter.taboos and runs
        scripts/check-doc-drift
Then:   first call: OverlayFragmentSet.fragments contains 3 derived
        "alter-taboo" entries, one per alter; coverage.missing == 0;
        source_property_map["alter-taboo"] lists the 3 NodePropertyRefs.
        after rename: check-doc-drift fails with the slug + the
        renamed property; author re-points the source rule, re-derives,
        coverage clean
```

## Interconnects

- Spec 239 (Dramatica derive) is the parent pattern; this spec is
  the KP-specific specialization of the same shape.
- **Drift-derivation chain** (149) — coverage lint is part of
  `check-doc-drift`.
- Spec 248 (plural-character query) — alter-sourced fragments
  read via the same graph-query substrate.
- **Output-budget chain** (146) — overlay output sorted + envelope-
  framed for cache stability.
- **Dogfood-loop chain** (150) — recurring placeholder fragments
  (the author keeps NOT authoring a body) classify into amendment
  proposals (slug too narrow / source rule misnamed).
- Spec 147 (AnthropicDriver) — optional Driver-assisted authoring of
  the per-slug source rules when the author scaffolds a new slug.

## Open questions

1. **Placeholder rendering.** Render placeholders verbatim, or skip?
   **Recommend**: render verbatim with a `[[placeholder]]` marker —
   skipping hides drift; the marker is searchable.
2. **Author override of derived bodies.** Allow per-fragment manual
   override? **Recommend**: yes, but mark `derivation_overridden=
   True` in metadata; Spec 149 still flags if the source property
   shifts (overrides go stale too).
3. **Cross-novel sharing of source rules.** Per-project, or
   per-installation? **Recommend**: per-installation defaults with
   per-project override — KP slugs are universal; sources are
   per-project.
