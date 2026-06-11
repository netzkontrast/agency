---
spec_id: "219"
slug: novel-storyform-llm-assist
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "103"
depends_on: ["103", "147", "129", "136", "146", "150", "217"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_storyform_llm.py
---

# Spec 219 — novel storyform LLM-assisted authoring

## Why

Spec 103 ships the Dramatica engine (11 decidable + 2 hybrid checks) +
the 304-entry ontology. Authoring a storyform — picking the 75+ NCP
storypoints coherently — is hard, and currently the author fills it by
hand against the checks. With the Spec 147 Driver + the prompt
fragments (Spec 129), `suggest_storyform(premise)` can propose a
coherent NCP the decidable checks then validate, and (with Spec 136)
suggest the dual-storyform inversion partner. The decidable checks
are the rubric — a Managed-Outcome-style loop fits.

## Done When

- [ ] **`suggest_storyform(premise, ...)`** drives the Spec 147 Driver
      with the premise + the Spec 129 fragments to propose an NCP;
      `novel_coherence_check` (Spec 120) validates it; failures feed
      back for a bounded re-propose.
- [ ] **Typed return shape**:
      ```python
      SuggestStoryformResult = {
        "intent_id":      str,
        "storyform":      dict,        # the 75+ NCP storypoints
        "coherent":       bool,        # decidable verdict from Spec 120
        "iterations":     int,         # propose→check→repair count
        "checks":         list[dict],  # [{name, pass, evidence}] from Spec 103
        "dual_partner":   dict | None, # Spec 136 inversion partner if requested
        "driver":         Literal["spec147","fake"],
        "refusal":        dict | None, # DriverError if surfaced
      }
      ```
- [ ] **Dual-storyform suggestion** (Spec 136) — propose the Klein-c
      inversion partner for a given storyform.
- [ ] **The ontology prefix is cache-stable** (Spec 146) across
      suggestions — the 304-entry ontology + the Spec 129 fragments
      form a frozen prefix; `usage.cache_read_input_tokens > 0` on
      the second proposal.
- [ ] **Invariant — every shipped suggestion is coherent.** Assert
      `result.coherent is True` for every returned storyform; if the
      bounded loop exhausts without convergence, surface a typed
      refusal rather than ship an incoherent NCP (CLAUDE.md rule 8 —
      a relationship, not a pinned iteration count).
- [ ] **Invariant — iteration bound is RELATIONAL.** Assert
      `result.iterations <= MAX_REPAIR_ROUNDS` (configured tunable, not
      a pinned snapshot); on overshoot, return
      `Codes.STORYFORM_NONCONVERGENT` with the last failing check set.
- [ ] **Invariant — check coverage equals registry.** The `checks`
      list MUST contain one entry per decidable check the Spec 103
      registry exposes, derived live — never a hand-authored count.
- [ ] **Invariant — dual-partner inverts on the Klein-c axis.** When
      `dual_partner` requested, assert `partner.mc_resolve !=
      original.mc_resolve` AND `partner.os_outcome !=
      original.os_outcome` (the inversion is structural, derived from
      Spec 136 rules).
- [ ] **Degrades** to the manual checks without `[anthropic]` (Spec 103).
- [ ] **Failure modes**:
      - `Codes.DRIVER_REFUSAL` propagated from Spec 147 — recorded as
        Artefact(kind="storyform-refusal"); caller decides retry;
      - `Codes.STORYFORM_NONCONVERGENT` when the repair loop exceeds
        budget; last-known-failing checks attached;
      - `Codes.ONTOLOGY_MISSING` when a proposed storypoint label is
        not in the 304-entry ontology (the Driver hallucinated a term).
- [ ] Test: a suggested storyform passes coherence (mocked Driver);
      the inversion partner check holds; non-convergent loop surfaces
      typed code; hallucinated storypoint raises `ONTOLOGY_MISSING`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  premise "a war photographer returns home and cannot stop
        seeing the dead" and a fresh intent
When:   suggest_storyform(premise, dual=True) is called and the
        Spec 147 driver is mocked to return a near-coherent NCP that
        fails the "OS-throughline-consistency" check on round 1
Then:   the verb feeds the failing check back to the Driver
        AND round 2 returns a coherent storyform
        AND result.iterations == 2
        AND result.coherent is True
        AND result.dual_partner inverts on mc_resolve
        AND the second call within the session hits prefix cache
            (usage.cache_read_input_tokens > 0)

Given:  the Driver returns a storypoint label "Stagnation" that is
        not in the 304-entry ontology
When:   suggest_storyform validates the proposal
Then:   returns Codes.ONTOLOGY_MISSING naming the unknown label
        AND records an Artefact(kind="storyform-hallucination")
            SERVES intent

Given:  MAX_REPAIR_ROUNDS=5 and the loop fails 5 successive rounds
When:   suggest_storyform exhausts the budget
Then:   returns Codes.STORYFORM_NONCONVERGENT
        AND attaches the last failing check set as evidence
        AND does NOT ship an incoherent storyform
```

## Failure modes

LLM-touching: Spec 147 propagates refusal/overflow codes; the bounded
repair loop catches non-convergence rather than retrying forever.
Ontology drift is a real failure surface — the Driver may invent
plausible-sounding storypoint labels; the validator MUST check every
proposed label against the live 304-entry registry, not a frozen copy.
On `DRIVER_REFUSAL` the loop halts and records the refusal Artefact;
the caller decides whether to re-prompt with a softened premise.

## Interconnects

- **LLM-driver chain** (147) · Spec 129 (fragments) · Spec 136
  (dual-storyform) for the inversion partner.
- Spec 146 (output-prefix) — ontology + fragments form the cache-stable
  prefix; suggestions reuse it.
- Spec 217 (build walkable) calls this verb at the storyform phase.
- Spec 218 (lifecycle output-budget) — the proposed storyform body
  honors the same prefix/body envelope.
- Spec 150 (dogfood classifier) — recurring non-convergence patterns
  become amendment proposals against Spec 103's check set.
- Spec 222 (catalogue graph-query) — cross-work storyform queries
  ("every novel where MC-resolve=Steadfast") share the same NCP nodes.
- Spec 224 (gates LLM-judge) — the judge rubric can score the same NCP
  for developmental quality, complementing coherence.
- Spec 252 (novel skill-walks managed) wraps this verb when the walk
  runs on the Managed-Agents path.

## Open questions

1. One-shot or iterate-to-coherent? **Recommend**: iterate (the checks
   are the rubric — a managed-Outcome-style loop fits); bound the loop
   on `MAX_REPAIR_ROUNDS` and surface `STORYFORM_NONCONVERGENT` rather
   than ship an incoherent NCP.
2. Cache the ontology prefix per-session or per-intent? **Recommend**:
   per-session — the ontology rarely changes mid-session, and Spec 146
   prefix-stability assertions hold across intents within the session.
3. Should `dual_partner` be eager or on-demand? **Recommend**:
   on-demand via `dual=True` — most callers want a single storyform;
   the partner doubles Driver cost when unused.
4. Where do recurring non-convergence patterns surface? **Recommend**:
   to Spec 150 as Reflections (`scope="storyform-noncoverage"`); the
   dogfood classifier promotes them to amendment proposals against
   the Spec 103 check set.
