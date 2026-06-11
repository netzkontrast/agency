---
spec_id: "217"
slug: novel-master-llm-build
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "101"
depends_on: ["101", "147", "145", "203"]
vision_goals: [4, 8]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_master_llm.py
---

# Spec 217 — novel master: LLM-build walkable

## Why

Spec 101 is the novel-complete-build master. The downstream waves
(120-145) built a deep graph surface (storyform, prose, worldbuilding,
codex, KP features) but there is no top-level walkable that drives a
whole novel from premise to manuscript, dispatching the creative steps
to the Spec 147 Driver and the decidable steps to the shipped verbs.
The novel-preflight (Spec 145) is the per-scene gate; this is the
book-level orchestrator.

## Done When

- [ ] **`build-novel(intent_id, premise, ...)` walkable** chains
      premise → storyform → structure → worldbuilding → chapter-briefing
      → scene-writing → editorial → manuscript; creative phases via Spec
      147, decidable via shipped verbs, hard gates where reversibility
      drops. Returns one phase at a time (Lifecycle template — CORE
      §47-62) so context stays bounded.
- [ ] **Typed phase return**:
      ```python
      BuildNovelPhase = {
        "phase":      Literal["premise","storyform","structure",
                              "worldbuilding","brief","scene","editorial",
                              "manuscript"],
        "intent_id":  str,
        "artefact_id": str | None,    # PRODUCES edge written this phase
        "gate":       Literal["soft","hard","none"],
        "driver":     Literal["decidable","spec147","fake"],
        "next":       str | None,     # next-phase verb to call
      }
      ```
- [ ] **Invariant — phase count ≥ named-creative-step count.** The walk
      MUST emit one phase per named creative step (no silent skipping);
      assert `len(emitted_phases) >= len(CREATIVE_STEPS)` derived from
      the registry, not a pinned number (CLAUDE.md rule 8).
- [ ] **Invariant — moat coverage equals scene count.** For a fixture
      novel of N scenes, `graph_query("Scene SERVES Novel WHERE
      novel_id=X")` returns exactly N nodes AND every Scene has a
      PRODUCES-from edge to a Brief AND a PASSES-GATE edge from a
      preflight Artefact. No orphans.
- [ ] **Invariant — driver split is decidable-majority.** Across one
      build, `count(driver="decidable") > count(driver="spec147")` —
      decidable steps stay the substrate, LLM steps stay the leaves.
- [ ] **Hard-gate set is enumerated, not implicit.** The walk publishes
      `HARD_GATES = {"storyform-coherence","preflight-block",
      "manuscript-export"}`; CI asserts the live set equals the
      enumerated set (drift fence).
- [ ] **Failure modes**:
      - `Codes.DRIVER_REFUSAL` (Spec 147) at any creative phase → walk
        records the refusal Artefact, returns the phase with
        `driver="fake"` fallback when CI, else surfaces to caller;
      - `Codes.PREFLIGHT_BLOCKED` at scene phase → walk halts at that
        scene (hard gate), other scenes unblocked;
      - `Codes.BUILD_PHASE_MISMATCH` when caller invokes a phase verb
        out of order (e.g. `scene` before `brief`).
- [ ] **Graph-query (Spec 203) answers "every scene SERVING this novel
      + its storyform + its gate"** in ONE call (no Python post-filter).
- [ ] Test: the walk drives the pipeline on a fixture novel (LLM phases
      mocked); moat query returns the chain; out-of-order invocation
      raises typed code; injected driver-refusal at scene phase records
      the refusal Artefact without losing prior phases.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  premise "a translator in 1920s Shanghai stumbles onto a
        cipher" and a fresh intent
When:   build-novel walks premise → ... → manuscript with the Spec 147
        driver mocked to return canned storyform + scene drafts
Then:   each phase returns one BuildNovelPhase with a PRODUCES Artefact
        AND the final manuscript phase emits a FormatArtefact
        AND graph_query("Scene SERVES Novel{id:X}") returns N scenes
        AND every scene has a PASSES-GATE edge from a Spec 145 preflight

Given:  the Spec 147 driver raises DRIVER_REFUSAL at the scene phase
When:   build-novel resumes from that phase
Then:   the refusal is recorded as Artefact(kind="driver-refusal")
        AND prior phase Artefacts remain intact (no rollback)
        AND the walk surfaces Codes.DRIVER_REFUSAL to the caller

Given:  a caller invokes the manuscript phase before the editorial phase
When:   build-novel.advance(phase="manuscript") runs
Then:   returns Codes.BUILD_PHASE_MISMATCH naming the missing phase
```

## Failure modes

LLM-touching phases (storyform suggest, scene generate, editorial judge)
all propagate Spec 147's typed refusal/overflow codes. The walk treats
each as recoverable at the phase boundary — never mid-phase — and writes
a refusal Artefact so the moat stays whole. Pandoc/weasyprint at the
manuscript phase delegates to Spec 223's typed export failures.

## Interconnects

- **LLM-driver chain** (147) · Spec 145 (preflight) is the per-scene
  gate this composes · Spec 203 (graph query).
- Spec 218 (lifecycle output-budget) — every phase return uses the
  prefix/body envelope so a wrapping driver caches the walk metadata.
- Spec 219 (storyform LLM-assist) feeds the storyform phase.
- Spec 220 (prose driver wet) lands the scene-generate phase.
- Spec 222 (catalogue graph-query) consumes the same `Scene SERVES
  Novel` moat for cross-work queries.
- Spec 223 (manuscript managed export) is the manuscript-phase driver.
- Spec 224 (gates LLM-judge) optionally augments the gate phase.
- Spec 252 (novel skill-walks managed) wraps the walk for the
  Managed-Agents path.
- Spec 264 (self-improvement meta-cap) treats `build-novel` as a
  promote-candidate composite.

## Open questions

1. Mega-walk or compose? **Recommend**: compose the existing skills
   (scene-writer 130, preflight 145, editorial 122) — `build-novel`
   orchestrates them; reuses their existing tests rather than
   duplicating gate logic.
2. Resume semantics — should `build-novel` accept `resume_from=phase`
   or always start at premise? **Recommend**: accept `resume_from`
   keyed off intent_id; the walk reads the last PRODUCES Artefact and
   advances. Idempotent re-runs are cheap (prefix-cached).
3. Hard-gate failure surface — halt the walk or queue the failure and
   continue independent phases? **Recommend**: halt at first hard-gate
   failure for v1 (predictable); a `--parallel-scenes` flag is a
   Slice-2 once provenance under parallel writes is proven (Spec 235
   neighbors path).
