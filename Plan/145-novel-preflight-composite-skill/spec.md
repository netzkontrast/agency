---
spec_id: "145"
slug: novel-preflight-composite-skill
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["122", "130", "137", "139", "140", "141", "142", "144"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/develop/_main.py
  - tests/test_novel_preflight_skill.py
domain: novel / workflow / composite-skill
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/03_anteile-profile-sprach-dna.md (§12 Pre-scene mandatory checks)"
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§9.M pre-draft checklist, §13 drafting discipline)"
---

# Spec 145 — Novel pre-flight composite skill

## Why

The Kohärenz Protokoll source has TWO concentric pre-flight checklists
that an author runs **before every scene**: §9.M's 7-item pre-draft
checklist (briefing-level) and §12's 7-item mandatory-checks list
(alter-level). Together they're the daily-driver — the operation an
author runs more often than any other single thing in the project.

After 130–144 ship, the surface to execute each item exists as a
discrete verb (`briefing_checklist` · `run_project_rules` · `check_veil`
· `check_reveal_timing` · `canon_audit` · `check_alter_recognition` ·
`voice_drift_audit`). But invoking 7+ verbs by hand before every scene
is exactly the friction Spec 130 was meant to absorb at the *scene*
level. This spec absorbs it at the *pre-scene gating* level — one
walkable composite that an LLM driver or human triggers once and gets a
single `{ready, blockers, warnings}` verdict.

This is also the cleanest answer to the cascading-walk question Spec
142 leaves open: rather than chain 142's six walks in some order, the
pre-flight composite reads only the *gating questions* — it doesn't
re-author anything, it audits readiness across the whole stack.

## Done When

- [ ] **`novel-preflight` walkable skill** registered, runnable as
      `develop.skill_walk("novel-preflight", intent_id, scene_id=…)`.
      Five phases, all read-only (no mutating verbs called; pre-flight
      is an audit, not an action):

      1. **`briefing-ready`** → `briefing_checklist(chapter_id)` (Spec 141)
      2. **`canon-clean`** → `canon_audit(novel_id)` + filters
         `[L]` gaps touching the current chapter (Spec 137)
      3. **`reveal-clear`** → `check_veil(novel_id)` (chapter ≤ veil)
         + `reveal_timeline_report(novel_id, tier="all")` filtered to
         rules that would be relevant THIS chapter (Spec 139)
      4. **`r-rules-dry-run`** → `run_project_rules(scene_id)` on a
         draft-stub or last-known draft body; collects the finding
         counts (Spec 140)
      5. **`voice-ready`** (HARD GATE) → checks fronting alter is
         bound (`VOICED_BY` present), `check_alter_recognition`
         passes a draft-stub, taboo-rules are non-empty (Spec 138/144).
         Halts until all sub-checks ok OR explicit override.

- [ ] **Composite verdict shape** — the walk's final return:
      ```
      {
        scene_id: str,
        chapter_id: str,
        ready: bool,
        verdicts: {
          briefing_ready: {passed, missing: [str…], advice: str},
          canon_clean:    {passed, open_gaps: int, unmarked: int, advice: str},
          reveal_clear:   {passed, premature_facts: [str…], veil_ok: bool},
          r_rules_clean:  {passed, critical: int, medium: int, low: int},
          voice_ready:    {passed, alter_id: str, taboo_count: int,
                           recognition_ok: bool},
        },
        blockers: [{phase, reason, advice}…],       # what must change
        warnings: [{phase, reason, advice}…],        # medium/low findings
        artefact_id: str,                            # pre-flight Artefact recorded
      }
      ```
- [ ] **`novel.preflight_report(scene_id)`** — non-walk convenience
      verb returning the same verdict shape, for callers that don't
      want the walk-runner overhead (CI, the editorial gate).
- [ ] **Editorial pipeline integration** (Spec 122) — when the editorial
      gates run, the pre-flight runs first; a critical pre-flight
      finding short-circuits the editorial pass with the pre-flight
      verdict as the failure reason. Mirrors Spec 140's
      `project_rule_gate` behavior — pre-flight failures are *blocking
      gate-fails*, not warnings.
- [ ] **`scene-writer` (Spec 130) phase 0 extension** — a new phase-0
      `preflight` chains BEFORE assemble. Pre-flight failure halts the
      walk; the orchestrator must address blockers first. Backward
      compatible behind a flag (`preflight=True` default for scenes
      whose novel has any of 137–141 nodes present; false otherwise).
- [ ] **Idempotent + cheap** — every sub-check is read-only; the whole
      walk runs in < 200ms on a 40-chapter graph (Spec 053 fast-loop
      doctrine — pre-flight must NOT slow the inner authoring loop).
- [ ] TODO row + drift clean.

## Design notes

- **Composite over master.** This is the *daily driver*; Spec 142's
  six walks are the *authoring tools*. Don't conflate them. The
  pre-flight asks "can I start drafting now?"; 142's walks ask "how do
  I author this thing?".
- **Read-only by design.** A walkable skill that MUTATES gives the
  author no escape valve when a check fires falsely. Pre-flight is an
  audit that surfaces — the author decides whether to fix or override.
  Spec 040 dispatch-decision rule S6 (mutating-disqualifier) extends
  here: this walk is the canonical "diagnose first, act later" tool.
- **Why one HARD GATE, not five?** The first four phases are
  informational + advisory — they should ALL show their findings even
  when one fails (the author wants the full surface to make decisions).
  The fifth (voice-ready) is the actual "would a draft be coherent"
  question; it's the only one that blocks. Mirrors Spec 140's
  `block_at="critical"` semantics.
- **Why integrate with 122 AND 130?** Editorial (122) is post-draft;
  scene-writer (130) is during-draft. Pre-flight is pre-draft. The
  three together close the loop: pre-flight gates entering the
  drafting walk; scene-writer drives the draft; editorial gates exit.
- **The override path is doctrine, not a hack.** A confirmed override
  records a Reflection with the author's stated reason (Spec 058's
  reflection-link-lint enforces both SERVES + OBSERVED_DURING). Future
  audits can census how often a pre-flight check is overridden,
  surfacing places the check is mis-tuned.

## Verb signatures

```python
def preflight_report(scene_id: str) -> dict:
    """Non-walk variant of the composite. Identical return shape to the walk.
    Returns: <see "Composite verdict shape" above>
    """

# develop.skill_walk reuses Spec 142's runner; this spec registers a new
# walk on novel.ontology.skills:
NOVEL_PREFLIGHT_SKILL = {
    "name": "novel-preflight",
    "phases": [
        {"name": "briefing-ready",  "verb": "novel.briefing_checklist"},
        {"name": "canon-clean",     "verb": "novel.canon_audit"},
        {"name": "reveal-clear",    "verb": "novel.reveal_timeline_report"},
        {"name": "r-rules-dry-run", "verb": "novel.run_project_rules"},
        {"name": "voice-ready",     "verb": "novel.check_alter_recognition",
         "hard_gate": True},
    ],
    "input_keys": ["scene_id"],
}
```

## Test scaffold

```text
tests/test_novel_preflight_skill.py  (target ≥ 18 tests)
  test_preflight_walk_runs_all_five_phases
  test_preflight_walk_runs_in_order
  test_preflight_walk_phases_are_read_only
  test_preflight_walk_halts_only_on_voice_gate
  test_preflight_walk_collects_warnings_from_other_phases
  test_preflight_walk_records_artefact
  test_preflight_walk_under_200ms_on_40_chapter_fixture
  test_preflight_report_verb_returns_same_shape_as_walk
  test_preflight_briefing_ready_reports_missing
  test_preflight_canon_clean_filters_to_current_chapter
  test_preflight_reveal_clear_includes_veil_status
  test_preflight_r_rules_dry_run_separates_critical_medium_low
  test_preflight_voice_ready_passes_with_bound_alter
  test_preflight_voice_ready_fails_without_VOICED_BY
  test_preflight_voice_ready_fails_with_empty_taboo_rules
  test_editorial_pipeline_short_circuits_on_preflight_critical
  test_scene_writer_phase0_preflight_default_on_with_KP_nodes
  test_scene_writer_phase0_preflight_default_off_without_KP_nodes
  test_override_records_reflection_with_serves_and_observed_during
```

## Open questions

1. Should `preflight_report` accept `chapter_id` as an alternative to
   `scene_id` (for novelists who want a chapter-wide preview)?
   **Recommend**: yes — accept either; when `chapter_id` is given,
   run the per-scene check on every scene in the chapter and aggregate.
2. Should pre-flight cache results within an intent? **Recommend**: no —
   the operation is < 200ms by design; caching adds invalidation
   complexity without meaningful win.
3. What happens when 130's phase-0 pre-flight defaults to ON but the
   novel has *some* of 137–141 nodes but not all? **Recommend**: ON if
   ANY are present — the cost of a no-op phase for missing surfaces is
   small (`briefing_checklist` returns "no briefing required" when no
   ModeBlock is bound), and progressive enrichment is the author's
   typical mode.
4. Should the pre-flight override emit a MonitorEvent (Spec 021)?
   **Recommend**: yes — overrides are exactly the kind of editorial
   decision a watching analytics layer wants to count.

## Followup

(Populated when the PR ships.)
