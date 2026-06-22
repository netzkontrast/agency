---
spec_id: "190"
slug: skill-surface-reconciliation-impl
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "071"
depends_on: ["071", "152", "163", "149"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/
  - skills/
  - tests/test_skill_surface_reconciliation.py
---

# Spec 190 — skill-surface reconciliation implementation

## Why

Spec 071 (skill-surface-reconciliation) is WARN-accepted — CORE.md
flags that a skill name lives on TWO surfaces (`ontology.skills` key +
`skills/<name>/SKILL.md`) and they can diverge (`tdd` ↔
`test-driven-development`), with "one name per skill across both
surfaces" as the canonical direction. The typed Skill boundary (Spec
152) + derived SkillDocs (Spec 163) make reconciliation mechanical:
derive both surfaces from one source so they CAN'T diverge.

## Done When

- [ ] **One canonical skill name per skill** — both the
      `ontology.skills` key and the `skills/<name>/` folder derive from
      a single source: the typed `Skill{canonical_name:str, aliases:
      list[str], folder_path:Path, ontology_key:str}` per Spec 152.
      Invariant: `skill.ontology_key == skill.canonical_name` AND
      `skill.folder_path.name == skill.canonical_name`.
- [ ] **The divergent pairs reconciled** (e.g. `tdd` →
      `test-driven-development` alias-and-deprecate). The list is
      DERIVED from the live drift report, not pinned.
- [ ] **A lint fails when the two surfaces diverge** (Spec 149 drift) —
      `_check_skill_surface` AST + filesystem inspection reports a
      typed `SkillDriftFinding{ontology_key, folder_name, kind:Literal[
      "missing_folder","missing_ontology","name_mismatch"]}`.
- [ ] **`develop.skill_walk` resolves either name** during the
      deprecation window — identity resolution, the alias points to
      the same Skill object (not a copy). Post-window, the alias
      removal happens only after zero calls to the deprecated name.
- [ ] **Skill count relationships** (rule 8): `len(ontology.skills) ==
      len(skills_folder_entries)` AND `every canonical_name resolves
      from both surfaces` — no pinned skill count.
- [ ] **Failure-mode coverage** for partial reconciliation, alias
      cycles, and walk-target ambiguity.
- [ ] Test: a divergent fixture trips the lint; both names resolve to
      one walk; the invariant test passes on the live surface.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  ontology.skills key == "tdd" AND skills/test-driven-development/
        SKILL.md exists (current divergence)
        AND Spec 152 typed Skill is installed
When:   the reconciliation pass runs with `tdd` → `test-driven-development`
        as the canonical
Then:   ontology.skills now keys "test-driven-development" (canonical);
        a `tdd` alias still resolves via develop.skill_walk during the
        deprecation window; SkillDriftFinding{kind:"name_mismatch"} is
        cleared; both call_tool paths return the same Skill object identity

Given:  a divergent fixture {ontology_key: "foo", folder: "bar/"}
When:   `_check_skill_surface` lint runs
Then:   SkillDriftFinding{ontology_key:"foo", folder_name:"bar",
        kind:"name_mismatch"} is emitted; the reconciliation pass
        proposes "foo" → "bar" OR "bar" → "foo" per the canonical
        rule (kebab marketplace name wins); a human confirms; alias
        ships

Given:  develop.skill_walk(intent_id, "tdd") during the deprecation window
When:   the engine resolves the walk
Then:   it walks the test-driven-development skill (identity), records
        a deprecation warning on the Invocation node, and returns the
        same phase the canonical name would deliver
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Partial reconciliation | one surface renamed, other forgotten | `_check_skill_surface` post-pass | both surfaces written atomically or neither |
| Alias cycle | `tdd` → `test-driven-development` → `tdd` | resolution recursion-depth probe | reject; canonical_name must terminate the chain |
| Walk-target ambiguity | two skills share a canonical_name | invariant: canonical_name uniqueness | reject the duplicate before reconciliation |
| Marketplace install drift | external plugin ships a colliding skill name | install-time name-conflict check | namespace by plugin or reject |
| Deprecation window violation | deprecated name removed while still walked | call-frequency probe | window of zero walks before removal |

## Interconnects

- Spec 152 (typed Skill) is the single source.
- Spec 163 (progressive disclosure) derives the SKILL.md surface.
- **Drift-derivation chain** (149).
- Spec 189 (verb consolidation) is the sibling reconciliation on the
  verb side; both follow the alias-and-deprecate pattern.
- Spec 191 (vision matrix) reads the reconciled skill set for the
  Goal-4 row.
- Spec 195 (event replay) records skill-walk Invocations the
  deprecation-window probe reads.

## Open questions

1. Which name wins on a divergence? **Recommend**: the kebab
   marketplace name (`test-driven-development`) — matches the
   superpowers convention + the using-agency meta-skill.
2. Should ontology.skills accept snake_case for backward compat?
   **Recommend**: yes during the deprecation window, no after —
   the post-window invariant is "kebab only".
3. What about external (plugin-installed) skills with conflicting
   names? **Recommend**: namespace by plugin (`<plugin>:<skill>`)
   in the ontology, kebab in the folder. Cross-plugin collisions
   surface as install-time errors, not run-time.
