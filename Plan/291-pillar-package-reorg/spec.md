---
spec_id: "291"
slug: pillar-package-reorg
status: draft
last_updated: 2026-06-13
owner: "@agency"
vision_goals: [4]
depends_on: ["286"]
---

# Spec 291 — Pillar-package reorganization + intent/thinking dedup

> Owner directive (2026-06-13), after the 286 OOP refactor merged. Make the
> code tree literally **be** the four concepts (CORE.md §"Four complete
> pillars"), and remove the `intent`↔`thinking` duplication.

## Target structure

`agency/capabilities/<cap>/` (flat) → **`agency/<pillar>/<cap>/`**, and each
pillar package absorbs its substrate core (the path the owner chose forces this:
`agency/intent/` can't coexist with `agency/intent.py`):

```
agency/
  intent/      _core.py  ← was intent.py (Intent node: capture·confirm·supersede + SERVES)
               thinking/  analyze/  research/  prompt/      ← caps (intent+thinking MERGED → thinking)
  memory/      _core.py  ← was memory.py (+ ontology.py?)
               reflect/  document/  dogfood/
  lifecycle/   _core.py  ← was lifecycle.py (+ skill.py walker?)
               develop/  gate/  delegate/  subagent/  jules/  workspace/  branch/
  capability/  _core.py  ← was capability.py + _invoke.py + _verb.py
               plugin/  skill_generator/  skills/  music/  novel/  shell/
  engine.py · toolresult.py · cli.py · install.py · _wire_envelope.py …  ← cross-pillar, stay at root
```

## Decisions

- **Pillar package = substrate `_core` + its capabilities.** The pillar dir owns
  the concept end to end.
- **Re-home (5 → intent):** intent · thinking · analyze · research · prompt — the
  *sensemaking / sharpen-the-WHY* suite.
- **Dedup — `intent` + `thinking` collapse into ONE `thinking` capability.** They
  duplicate the 8 critical-thinking methods (assumptions · decompose ·
  first_principles · inversion · premortem · second_order · steelman · tradeoffs).
  `thinking` is the superset (adds red_team · socratic · apply_full_review);
  fold `intent.suggests` (chain-next projection) into it (or relocate — it is not
  a thinking method). **The merged cap is `thinking`; the `intent` capability is
  removed.** (`intent_bootstrap` + the substrate Intent node are untouched —
  they live in `agency/intent/_core.py`.)
- **Discovery loader** scans the 4 pillar dirs (+ each `_core`), not
  `agency/capabilities/`.
- **Cross-pillar substrate** (`engine` · `toolresult` · `cli` · `install` ·
  wire/envelope/host helpers) stays at `agency/` root.
- **Tool-name prefix → the PILLAR** (owner directive 2026-06-13): replace the
  uniform `capability_` prefix with the home pillar — **`<pillar>_<cap>_<verb>`**
  (`pillar` ∈ intent · capability · lifecycle · memory). Examples:
  `capability_analyze_quality` → `intent_analyze_quality`; `capability_reflect_note`
  → `memory_reflect_note`; `capability_jules_dispatch` → `lifecycle_jules_dispatch`;
  capability-pillar caps keep a `capability_` prefix that now *means the pillar*
  (`capability_plugin_lint`). The name encodes the home concept at the wire — a
  legibility + token win (Goal 1 / Spec 067), and it mirrors the
  `<pillar>_<cap>_<verb>` symmetry of the new package tree (`agency/<pillar>/<cap>/`).
  Collision-free (pillar+cap+verb unique). **Intended wire-name change** (not
  behaviour-preserving): every caller / skill / code-mode block / test that
  references `capability_…` updates — **including the Phase-C acceptance suite**
  (it identifies cap-verbs by the `capability_` prefix; co-evolve to: a cap-verb
  is `{intent,capability,lifecycle,memory}_<cap>_<verb>` — 3+ segments — distinct
  from the wire verbs {search, get_schema, execute} and the substrate onboarding
  tools {agency_welcome, agency_install, agency_doctor, intent_bootstrap}).

## Behaviour contract (the gate)

- **Reorg is behaviour-preserving:** verb names are `capability_<cap>_<verb>` —
  a cap's *location* doesn't change its name. Wire contract, verb count, and
  provenance unchanged. The Phase-C **Gherkin acceptance suite** (9 scenarios)
  must stay green throughout.
- **Dedup is an INTENDED surface change** (not preserving): the duplicated
  `intent.*` critical-thinking verbs collapse — callers move to `thinking.*`.
  The acceptance suite asserts *relationships* (verb surface substantial, the
  thinking methods reachable), not the pinned `intent.*` names, so it tolerates
  the rename. Update the `intent_path_analysis`/critical-thinking callers.

## Execution — incremental, one pillar at a time (like 286), each gated

1. **memory pillar** (smallest, 3 caps): `agency/memory/_core.py` + reflect/document/dogfood; loader handles both old+new during transition.
2. **lifecycle pillar** (7 caps).
3. **capability pillar** (6 caps).
4. **intent pillar** (last — carries the dedup): absorb `intent.py`→`_core`,
   move analyze/research/prompt, MERGE intent+thinking → `thinking`.
5. Delete the empty `agency/capabilities/`; final loader scans only the 4 pillars.

**Each slice (owner directive 2026-06-13):**
1. reorganize (move + absorb `_core` + update imports/loader; on the intent slice, the dedup),
2. **run `/simplify`** on the touched code — reuse/simplification/efficiency/altitude cleanups (the reorg is the moment to delete the duplication the moves expose, not just relocate it),
3. green **Gherkin acceptance** suite + clean-OOP review,
before the next slice.

## Followup — Implementation Status (2026-06-13)
- **Status: draft.** Specced by the Vision owner after the owner directive.
  Execution is a code refactor (refactor-agent territory); the Review-partner
  gates via the acceptance suite. Phase B living specs regenerate against the
  reorganized tree once it lands (the `intent/` pillar group then appears with
  the merged `thinking` cap).
