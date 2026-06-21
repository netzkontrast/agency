---
spec_id: "142"
slug: novel-craft-skill-walks
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["018", "130", "136", "137", "138", "139", "140", "141"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/develop/_main.py
  - tests/test_novel_skill_walks.py
domain: novel / workflow / walkable-skills
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/03_anteile-profile-sprach-dna.md (§12 Pre-scene mandatory checks)"
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§13 16-section drafting discipline)"
  - "Plan/done/130-scene-writer-skill/spec.md (5-phase walkable precedent)"
---

# Spec 142 — Novel-craft walkable skills (per-cluster authoring)

## Why

Specs 136–141 ship the **graph surface** for the KP-derived features —
nodes, edges, verbs. They do NOT ship the *authoring loop* that drives an
agent through the surface in the right order. Today an LLM (or human)
calling `record_lock` / `add_alter` / `set_reveal_rule` / `record_motif`
in isolation has no scaffolding for "do these in order, gate at the right
moment, don't ship an alter without a voice, don't lock a fact still in
quarry". The KP Protocol itself ships a **16-section drafting discipline**
(§13) and a **§12 pre-scene mandatory checklist** — those are walkable
skills in disguise.

Spec 130 set the precedent with the 5-phase `scene-writer` skill (one
walk per Lifecycle template, `develop.skill_walk` is the runner). Specs
136–141 each deserve a peer walk — a phase-by-phase scaffolding that
turns scattered verbs into one operation an author can trigger by name.

## Done When

- [ ] **Six new walkable skills** registered on the novel ontology, one per
      136–141 spec, each driven by `develop.skill_walk(name, intent_id)`:

      1. **`dual-storyform-author`** (Spec 136) — 5 phases:
         a. `define-set` → `create_storyform_set`
         b. `add-A` → `add_storyform_to_set(role="primary")`
         c. `add-B` → `add_storyform_to_set(role="secondary")`
         d. `verify-inversion` (HARD GATE) → `check_klein_c_inversion`;
            halts on non-inverted slots
         e. `route-first-scenes` → `route_scene_storyform` for the
            opening chapters; emits `bridge_frequency_report` summary.

      2. **`canon-lock-author`** (Spec 137) — 4 phases:
         a. `stamp-status` → `set_canon_status` on the target node
         b. `record-lock` → `record_lock` with source + date
         c. `audit-review` (HARD GATE) → `canon_audit`; halts when
            unmarked > 0 OR open-gap-count > author-confirmed threshold
         d. `index-publish` → `lock_index` rendered as an Artefact.

      3. **`alter-roster-builder`** (Spec 138) — 6 phases:
         a. `system-create` → `create_character_system`
         b. `roster-add` (loop) → `add_alter` per roster row
         c. `voice-bind` (loop) → `assign_voice_to_alter`
         d. `matrix-record` (loop) → `record_alter_conflict`
         e. `mirror-bind` (loop, optional) → `record_mirror`
         f. `discipline-verify` (HARD GATE) → `validate_no_fusion` +
            `conflict_matrix_report` (flags max-pairs); halts on fusion.

      4. **`reveal-rule-author`** (Spec 139) — 4 phases:
         a. `enumerate-facts` → author lists facts requiring tiered rules
         b. `set-rules` (loop) → `set_reveal_rule` per (fact, tier)
         c. `veil-configure` → `check_veil` dry-run with proposed
            hold_until_chapter
         d. `gate-verify` (HARD GATE) → `reveal_gate` over current
            manuscript; halts on premature reveals.

      5. **`r-rule-author`** (Spec 140) — 5 phases:
         a. `pick-predicate` → author selects from 4 PREDICATE_KIND
         b. `params-author` → fills the documented param keys
         c. `register` → `register_project_rule`
         d. `dry-run` → `run_project_rules` over a sample scene-id
         e. `gate-attach` (HARD GATE) → `project_rule_gate` shows
            current critical-count; halts on a regression vs prior count.

      6. **`chapter-briefing-author`** (Spec 141) — 5 phases:
         a. `block-assign` → `assign_chapter_to_block`
         b. `render-briefing` → `render_chapter_briefing`
         c. `gap-resolve` (loop) → walks `missing_specs` + `[L]` gaps
            surfaced in section L
         d. `checklist-run` (HARD GATE) → `briefing_checklist`; halts
            until `ready=True`
         e. `archive-as-artefact` → briefing Artefact stamped
            `canon_status=proposal` (Spec 137).

- [ ] **Skill registration discipline** — each walk lives on
      `novel.ontology.skills` (Spec 016 derive pattern); the docstring
      embeds `Use when:` / `Triggers:` / `Red flags:` so the auto-derived
      SkillDoc is correct out of the box (no hand-edit; Spec 080/081).

- [ ] **One TDD fixture per skill** — each test instantiates the engine,
      runs the walk end-to-end against a small fixture novel, and asserts:
      - phases fire in order
      - hard gates halt on configured failure paths
      - each phase records the documented Artefact / edge

- [ ] **`develop.skill_walk` extension** — the existing runner gains a
      `--dry-run` flag that walks WITHOUT firing verb side-effects (each
      phase reports `would_invoke: <verb>` instead). Lets an author
      preview the walk before committing.

- [ ] TODO row + drift clean.

## Design notes

- **Six walks, one pattern.** Each walk is the same 4-step Lifecycle
  template (Spec 060 templates) — author the phases as a YAML/dict
  literal, register via `as_capability`, no new framework. The
  scene-writer (Spec 130) is the precedent; this scales the pattern.
- **Hard gates are the moat.** A walk without a hard gate is just a
  script; the gate is where the author decides "yes, proceed". Each
  walk ships exactly one hard gate at the phase where reversibility
  drops off (Klein-c verified, fusion validated, reveal-gate green,
  rule-gate green, checklist ready).
- **Dry-run unlocks the prompt loop.** An LLM driver can call
  `skill_walk(..., dry_run=True)` to plan the walk, then re-call without
  the flag to commit. This is the path from "verbs exist" to "an agent
  can drive the whole authoring loop on its own".
- **Why six walks, not one mega-walk?** Each maps to a *concept the
  author already holds in their head* (the dual-storyform, the alter
  roster, the reveal-discipline). A mega-walk would force them into a
  linear order the work doesn't actually have — these clusters are
  often authored in parallel.

## Verb signatures

```python
# Already-existing runner (Spec 018), extended:
def skill_walk(
    intent_id: str,
    name: str,                       # one of the six walk names
    *,
    dry_run: bool = False,           # NEW — preview without side-effects
    starting_phase: str = "",        # resume from a paused phase
    confirm_gate: bool = False,      # explicit gate-pass token
) -> dict:
    """Returns: {
      walk: str,
      phases_run: [{name, verb, status, evidence, artefacts: […]}…],
      current_phase: str,
      hard_gate: {name, passed, advice} | None,
      done: bool,
    }
    """
```

## Test scaffold

```text
tests/test_novel_skill_walks.py  (target ≥ 24 tests; one happy + one fail per walk)
  test_dual_storyform_walk_phases_in_order
  test_dual_storyform_walk_halts_on_klein_c_failure
  test_canon_lock_walk_phases_in_order
  test_canon_lock_walk_halts_on_unmarked_threshold
  test_alter_roster_walk_phases_in_order
  test_alter_roster_walk_halts_on_fusion_flag
  test_reveal_rule_walk_phases_in_order
  test_reveal_rule_walk_halts_on_premature_reveal
  test_r_rule_walk_phases_in_order
  test_r_rule_walk_halts_on_critical_regression
  test_chapter_briefing_walk_phases_in_order
  test_chapter_briefing_walk_halts_when_checklist_not_ready
  test_dry_run_does_not_fire_side_effects
  test_dry_run_reports_would_invoke
  test_resume_from_starting_phase
  test_skill_doc_derived_from_docstring   # Spec 081 derive
  test_skill_walk_records_provenance_artefacts
  …
```

## Open questions

1. Should `dual-storyform-author` validate Klein-c inversion against ALL
   recorded `StoryformTransition`s (Spec 136 synthesis-kind transition
   would intentionally break Klein-c after a certain chapter)?
   **Recommend**: yes, but with the post-transition chapters excluded —
   the inversion holds BEFORE the synthesis-c handoff; the walk reports
   that as `inversion_valid_through_chapter: int`.
2. Should an LLM driver be able to call walks via the wire-contract
   `execute` block (chain via code-mode)? **Recommend**: yes — every
   walk is reachable via `mcp__agency__execute` already since
   `develop.skill_walk` is a normal verb. No extra surface.
3. Hard-gate confirmation token format — boolean flag vs typed token?
   **Recommend**: boolean for v1 (matches Spec 018 today); typed token
   (with reason string) is a Slice-2 once authors hit the "I want a
   reason recorded for the override" case.

## Followup

(Populated when the PR ships.)
