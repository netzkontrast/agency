---
spec_id: "272"
slug: jules-skills-derive
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "013"
depends_on: ["013", "081", "163", "149"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/jules/_main.py
  - tests/test_jules_skills_derive.py
---

# Spec 272 — Jules skills: derive from capability docstring

## Why

Spec 013 ships 6 Jules skills + AGENCY_PROTOCOL + lint + flag matrix.
Like the broader SkillDoc derive (Spec 080/081), these should derive
from their host code (the Jules cap docstring) instead of duplicating —
matching the SkillDoc discipline already shipped for every other cap
(Spec 163 closure). The doctrine: **authored metadata that duplicates
an existing source is drift waiting to happen** (CLAUDE.md "Derivability
audit"). Today the Jules skills are the last hand-pinned holdout.

## Done When

- [ ] **All 6 Jules skills derive** from
      `agency/capabilities/jules/_main.py` docstring via the Spec 081
      walker. Literal `SKILL.md` files are removed (or shimmed to a
      one-line `<!-- derived: see _main.py docstring -->`). The Spec
      080 docstring convention applies (`Use when:`, `Triggers:`, `Red
      flags:` headings parsed by section).
- [ ] **AGENCY_PROTOCOL §10 regenerates** on docstring change. The Spec
      149 derived-doc drift gate covers §10 — `scripts/check-doc-drift`
      reports stale when the docstring's SHA-256 changes but §10 was
      not regenerated. `--update` re-stamps.
- [ ] **Flag matrix derived from the live flag set.** The matrix rows
      come from `jules.ontology.flags` (the runtime flag enum), not a
      hand-pinned list. Adding a flag in code surfaces it in the
      matrix without a doc edit.
- [ ] **Invariants** (CLAUDE.md rule 8):
      - For every skill `s` in the Jules skill set:
        `s.body.sha256 == derive(jules_docstring, s.name).sha256` —
        equality is the contract; a drift is a test failure.
      - `set(matrix.rows) == set(jules.ontology.flags)` — symmetric
        difference is the violation. (Don't pin a count of 6 skills
        or N flags; pin the set equality.)
      - `count(literal SKILL.md bodies under skills/jules-*) == 0`
        post-migration — derive is the only path.
- [ ] **Test:** docstring change updates skill bodies + matrix in one
      derive pass; hand-editing a derived skill body fails CI with a
      `DERIVED_SKILL_HAND_EDIT` lint code; adding a flag in
      `jules.ontology.flags` makes a matrix row appear without a
      separate edit.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  agency/capabilities/jules/_main.py docstring carries a
        `Use when:` section for the `jules-dispatch` skill, and
        skills/jules-dispatch/SKILL.md is the literal hand-edit
When:   migration runs: Spec 081 walker reads docstring → emits
        derived body; the existing SKILL.md is replaced by a
        derive-shim; `scripts/check-doc-drift --update` re-stamps
Then:   body.sha256 matches derive(docstring); a subsequent docstring
        edit + walker re-run produces an updated body; CI sees no
        drift

Given:  someone adds `jules.ontology.flags.new_flag = "..."` in code
When:   derive pass runs (build-time / pre-commit)
Then:   AGENCY_PROTOCOL §10 flag matrix gains a row for `new_flag`
        automatically; no separate doc edit; check-doc-drift clean

Given:  a contributor edits skills/jules-dispatch/SKILL.md body by
        hand (forgetting the derive contract)
When:   pre-commit lint runs
Then:   DERIVED_SKILL_HAND_EDIT fires with file:line, pointing at the
        docstring section to edit instead
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | Docstring section missing for a registered skill | Walker raises `MissingSection` | Build fails; error names the skill + the required section |
| F2 | Docstring drift between code + derived body | check-doc-drift SHA mismatch | CI red; `--update` re-derives |
| F3 | Hand-edit to a derived SKILL.md body | Pre-commit lint AST check | Block commit; show derive-path |
| F4 | Flag added in code but matrix renderer cached | Section regenerate triggered by `jules.ontology.flags` hash | Invalidate cache on flag-set hash change |
| F5 | Walker can't parse a malformed docstring section | Walker error with line number | Block build; surface line in the docstring (NOT the derived file) |

## Interconnects

- Spec 013 (parent) — last hand-pinned Jules skill set.
- Spec 081 (walkable usage-skill derive) is the pattern source.
- Spec 080 (SkillDoc derive) is the canonical example for every other
  capability.
- Spec 163 (progressive-disclosure closure) is the parallel discipline
  this closes.
- Spec 149 (derived-doc drift) gates AGENCY_PROTOCOL §10.
- Spec 271 (Jules/MA bridge) renames events to include `driver` field —
  the docstring sections must cover both drivers so derived skill
  bodies stay driver-agnostic.
- **Drift-derivation chain** (149) closure.

## Open questions

1. **Skill body cache location.** Render-on-demand into memory, or
   stamp to disk alongside the shim? **Recommend**: render-on-demand,
   cached in the graph as a `DerivedDoc` node — files are a view (rule
   2); disk stamping invites a second drift gate.
2. **Backward compatibility with the existing 6 SKILL.md paths.**
   Keep the path so external tools (Claude Code's skill loader) still
   resolve? **Recommend**: yes — the shim file at the existing path
   returns the rendered body; the loader sees no breaking change.
3. **Docstring section ordering authority.** If a contributor reorders
   sections in the docstring, does the derived body reorder?
   **Recommend**: yes, body order follows docstring order — single
   source of truth; reordering is a content edit, not a render edit.
