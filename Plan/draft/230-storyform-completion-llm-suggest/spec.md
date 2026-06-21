---
spec_id: "230"
slug: storyform-completion-llm-suggest
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "120"
depends_on: ["120", "219", "147", "129"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_storyform_completion_llm.py
---

# Spec 230 — storyform-completion LLM suggest

## Why

Spec 120 ships the Dramatica engine completion — 8 new checks +
`novel_coherence_check` composite (exact-fail across 11 fixtures) + the
`storyform-build` 6-phase skill. Spec 219 added `suggest_storyform`.
This applies the same Driver to the COMPLETION path: given a partial
storyform, suggest the missing slots that satisfy `novel_coherence_check`
— the iterate-to-rubric pattern (managed-Outcome style) using the
decidable checks as the rubric.

## Done When

- [ ] **`suggest_completion(storyform_id) -> CompletionProposal`** where
      `CompletionProposal = {storyform_id, filled: dict[slot, value],
      iterations: int, coherence_before: int, coherence_after: int,
      stop_reason: Literal["converged","budget","unsatisfiable"]}`.
      Invariant: `coherence_after <= coherence_before` (fewer failing
      checks) — never increases failures.
- [ ] **Convergence invariant** — `stop_reason="converged"` REQUIRES
      `coherence_after == 0`; any other stop_reason carries
      `coherence_after > 0` with the failing-check list attached.
- [ ] **Loop bound is RELATIONAL, not pinned** —
      `iterations <= max_iter` AND each iteration must strictly
      reduce the failing-check count OR the loop short-circuits
      (Codes.COMPLETION_NO_PROGRESS). No magic iteration count in
      the test: assert the inequality, not `iterations == 4`.
- [ ] **`storyform-build` skill chains it** as an optional phase; phase
      output is the CompletionProposal, never the raw Driver transcript.
- [ ] **Output budget honored** (Spec 146); prompt prefix = ontology
      fragments (Spec 129), cache-stable across calls for the same
      storyform shape.
- [ ] **Failure modes** — `unsatisfiable` when the partial storyform
      contains a Dramatica contradiction no completion can resolve;
      `budget` when Driver token budget exhausts before convergence;
      `Codes.DRIVER_UNAVAILABLE` when Spec 147 boundary is not wired.
      Each failure mode emits a Reflection (Spec 150) tagged by reason
      so the dogfood loop can spot recurrent unsatisfiable patterns.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a storyform with OS/Throughline filled but MC/IC absent,
        novel_coherence_check reports 6 failing slots
When:   suggest_completion(storyform_id) runs with mocked Driver
        proposing MC/IC pairs from the ontology fragments
Then:   CompletionProposal.coherence_after < 6 AND
        CompletionProposal.iterations > 0 AND
        stop_reason in {"converged","budget"} AND
        every filled slot satisfies its ontology constraint

Given:  Driver proposes a slot value that CONFLICTS with an existing
        canonical slot
When:   the iteration's coherence check runs
Then:   the proposal is rejected, iteration count still advances,
        and the failing-slot list MUST shrink monotonically across
        accepted iterations (else COMPLETION_NO_PROGRESS)
```

## Interconnects

- **LLM-driver chain** (147) · Spec 219 (suggest_storyform sibling).
- The decidable checks are the rubric — pattern parity with Spec 224.
- Spec 146 (output-prefix) — ontology prefix is byte-stable across
  completions of any storyform sharing the same shape.
- Spec 150 (dogfood) — `unsatisfiable` stop_reason patterns feed
  amendment proposals when a class of storyforms repeatedly fails.
- Spec 137 (canon-status) — completions land as `proposal` until the
  author confirms; never silent canon.

## Open questions

1. **Driver temperature.** Deterministic (T=0) or sampled? **Recommend:**
   T=0 — the rubric is decidable, sampling adds noise without lifting
   convergence rate.
2. **Max iterations default.** **Recommend:** 5 — pattern parity with
   Spec 224; budget-exhaust is rare in practice on the 11 fixtures.
3. **Partial acceptance.** When a slot completion partially satisfies
   coherence, accept or reject? **Recommend:** accept iff the
   failing-check count strictly decreases — the monotone-progress
   invariant above.
