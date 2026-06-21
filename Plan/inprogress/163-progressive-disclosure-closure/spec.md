---
spec_id: "163"
slug: progressive-disclosure-closure
status: draft
state: inprogress
last_updated: 2026-06-10
owner: "@agency"
enhances: "031"
depends_on: ["031", "080", "081", "149"]
vision_goals: [1, 4]
affects:
  - agency/_skilldoc.py
  - tests/test_progressive_disclosure_closure.py
---

# Spec 163 — Progressive-disclosure closure

## Why

Spec 031 (skills-progressive-disclosure) is Partial — "per-spec skill
rendering: emit_skill, references, bash wrappers; active work on main".
Specs 080/081 generalized SkillDoc derivation, which means the per-spec
emit_skill path now has a single canonical source. This spec finishes
031 by routing emit_skill through the 080/081 derive engine (no
literal duplication) and deriving the references/ + bash-wrapper set
instead of hand-maintaining them.

## Done When (measurable invariants — rule 8)

- [ ] **Invariant: every SkillDoc body is byte-equal to its derived
      render** — `derive(docstring) == emit_skill(skill)` for every
      skill in the live registry; lint asserts (no literal
      duplication, CLAUDE.md derivability rule).
- [ ] **Invariant: references/ set = live verb set** — `set(references)
      == set(registry.verbs)` for every capability; derived, not
      hand-maintained (Spec 149).
- [ ] **Invariant: bash-wrapper set ⊆ Spec 079 CLI surface** — every
      legacy wrapper either maps to a live `agency <cap> <verb>`
      command or is formally cancelled-with-pointer (no silent
      dangling).
- [ ] **Relationship: docstring change ⇒ SkillDoc change** — mutate
      a `Use when:` line in a fixture capability, assert the
      rendered SkillDoc reflects it on the next call (no stale
      cache, no manual regen).
- [ ] **Failure mode (derive path):** a docstring missing the
      `Use when:` / `Triggers:` / `Red flags:` sections fails the
      derive with `Codes.SKILLDOC_MISSING_SECTION` pointing at the
      module path (never silently emit a partial SkillDoc).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability `develop` with a verb `develop.brainstorm` whose
        module docstring contains "Use when: starting any creative
        work, before code"
When:   emit_skill("develop.brainstorm") runs
Then:   the rendered SkillDoc's body contains "Use when: starting
        any creative work, before code" verbatim AND no other
        SkillDoc field re-states it (derivability — single source)

Given:  the same capability gains a new verb `develop.estimate`
When:   the references/ index regenerates (commit-time, Spec 149)
Then:   references/ contains an entry for `develop.estimate` AND
        the legacy bash wrapper folder either gains a redirect to
        `agency develop estimate` or is closed-with-pointer
```

## Interconnects

- **Drift-derivation chain** (149) · **output-budget chain** (146)
  (SkillDoc bodies count against the brief-tier discovery payload).
- Spec 080/081 (SkillDoc derive) is the engine this routes through.
- Spec 161 (discovery rank) consumes the derived SkillDoc bodies
  for re-rank context — drift here breaks rank quality.
- Spec 175 (install surface derived) consumes the SkillDoc set for
  the README capability table.
- Spec 177 (plugin-reference audit) gates SkillDoc shape against
  the working-with-claude-code reference.

## Open questions

1. **Keep bash wrappers, or fold into Spec 079 CLI mirror?**
   **Recommend**: fold — the 079 mirror already exposes every verb;
   per-spec wrappers are redundant. Deprecate them here with a
   one-cycle WARN, then remove.
2. **Cache rendered SkillDocs across calls?** **Recommend**: derive
   on demand + cache keyed on `(module_path, docstring_hash)`;
   invalidates the moment a docstring changes (rule 8 — relationship,
   not snapshot).
3. **Lint promotion cadence?** **Recommend**: WARN one cycle (Spec
   056/058 pattern), then promote `SKILLDOC_LITERAL_DUPLICATION`
   to error once the live registry reports zero violations.

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

