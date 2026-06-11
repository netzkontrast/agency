---
spec_id: "264"
slug: self-improvement-meta-cap
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "150"
depends_on: ["150", "258", "183", "261", "270", "256"]
vision_goals: [6]
affects:
  - agency/capabilities/develop/_main.py
  - tests/test_self_improvement.py
---

# Spec 264 — self-improvement meta-cap (close the loop end-to-end)

## Why

Spec 150 ships the amendment classifier. Spec 258 measures classifier
quality. Spec 183 detects verb opportunities. Spec 261 audits charter
closure. Each is a piece of the dogfood loop; none of them composes
the pieces into a single driveable surface. This meta-cap composes
them: `develop.self_improve()` finds the highest-leverage gap (lowest
`closure_pct` axis, highest reflection density), proposes a spec
amendment to close it, opens a PR draft. This is what GOALS.md Goal 6
("doctrine evolves through dogfooding") looks like as a verb you can
invoke — and the closing test is recursive: `self_improve` can propose
enhancements to itself.

## Done When

- [ ] **`develop.self_improve(window: str = "7d")`** runs the cycle:
      1. detect opportunities (Spec 183) — read reflections + closure
      2. score candidates by (uncovered_axis_priority,
         reflection_count_in_window, classifier_accept_rate)
      3. pick the top candidate gap
      4. classify reflections (Spec 150) into amendment proposals
      5. gate via rubric (Spec 258)
      6. produce ONE proposed spec amendment
      7. open a PR draft (via gh CLI; never auto-merge)
- [ ] **Typed `SelfImproveOutcome` return shape**:
      ```python
      class SelfImproveOutcome(TypedDict):
          window: str
          candidates_scored: int       # how many gaps considered
          chosen_gap: dict             # {spec_id, axis, score}
          proposal: dict | None        # AmendmentProposal or None
          pr_url: str | None           # GitHub PR draft URL
          reflection_id: str           # provenance node
          billed_tokens: int           # full-cycle cost
      ```
- [ ] **Driver-mediated proposal authoring** via Spec 147 — the spec
      body itself is drafted by the canonical driver against a
      vendored spec-template + the relevant reflections as evidence.
- [ ] **Human approves before merge** — never silent canon (Spec 137).
      PR draft is the gate; the human is in the loop by construction.
- [ ] **The meta-cap is recursively applied** — `self_improve` is
      itself one of the candidates it considers. The test verifies
      the recursion terminates (self-proposals are gated through the
      same rubric, never auto-merged).
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `proposal is not None ⇒ pr_url is not None` (every proposal
        gets a PR draft; never a proposal in limbo)
      - `pr_url is None ⇒ chosen_gap names a reason`
        (e.g. `{reason: "no_proposal_satisfied_rubric"}`)
      - `chosen_gap.score >= second_best.score` (the pick is the
        highest-leverage gap — invariant relationship)
      - `billed_tokens <= max_self_improve_tokens` (cost cap)
      - cycle-time `< 90s` p95 (cycle measured wall-clock; a budget,
        not a snapshot)
- [ ] Test: end-to-end cycle on a fixture (synthetic reflections +
      uncovered cells) proposes a sensible amendment; recursive
      self-proposal terminates (no infinite loop); rubric-failed
      proposal produces `pr_url: None` with a named reason.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  current state — closure_pct=0.71 (Spec 261); 3 reflections in
        the last 7d about Spec 042's missing derivability hook;
        classifier accept_rate=0.65 (healthy)
When:   develop.self_improve(window="7d") runs
Then:   candidates_scored=42 (every uncovered cell × reflection density)
        AND chosen_gap={spec_id:"042", axis:"derivability+drift",
        score:0.88}
        AND proposal={op:"new_enhancement_spec", parent:"042",
        rationale:"...", cited_reflections:[r1, r2, r3]}
        AND pr_url="https://github.com/.../pull/NNN" (draft, labeled
        "self-improvement", awaiting human review)
        AND reflection_id points at the cycle's provenance node

Given:  no candidate satisfies the rubric (Spec 258 grade fails on
        all top-3 proposals)
When:   self_improve runs
Then:   SelfImproveOutcome{proposal:None, pr_url:None,
        chosen_gap:{..., reason:"no_proposal_satisfied_rubric"}}
        AND a reflection records "self_improve found no
        rubric-satisfied proposal" so the next session sees the
        signal (likely classifier or rubric regression)

Given:  self_improve's own enhancement is the top-scored gap
When:   the cycle runs and the rubric passes for the self-proposal
Then:   PR draft opens proposing an enhancement to self_improve itself
        AND the recursion is bounded by the rubric (a self-proposal
        cannot bypass its own grading) — termination invariant holds
```

## Failure modes (Nygard)

| Failure | Meta-cap response |
|---|---|
| Classifier refusal (`stop_reason: "refusal"`) | Spec 256 fallback; on exhaustion, cycle aborts with `reason:"classifier_refused"` |
| GitHub API unavailable | Proposal produced + persisted as graph Artefact; `pr_url: None` with `reason:"github_unavailable"`; next cycle can retry PR creation |
| Rubric never satisfied | `proposal: None, pr_url: None`; signal that classifier/rubric needs attention (Spec 258 quality loop) |
| Cycle exceeds token budget | Abort with `reason:"budget_exhausted"`; partial work persisted in reflection so cost isn't lost |
| Infinite recursive self-improvement | Bounded by rubric grading + per-window dedup (same chosen_gap within window short-circuits) |
| PR draft would conflict with an open draft on same gap | Skip with `reason:"open_pr_exists"`; do NOT spam duplicate drafts |
| Wall-clock exceeds 90s p95 | Per-step timeouts within the cycle; partial state persists; reflection records the slow step for tuning |

## Interconnects

- Spec 150 + 258 + 183 + 261 — composed here.
- Spec 270 (stop-condition verification) — the meta-cap's purpose is
  to flip the stop predicate toward `closure: True`; it watches the
  predicate as its own success signal.
- Spec 256 (refusal fallback) — required for the cycle's classifier
  call to survive Fable 5 safety hits.
- Spec 147 (AnthropicDriver) — the proposal-authoring engine.
- **Dogfood-loop chain** closure (the operational vertex; everything
  else feeds in).

## Open questions

1. **How often does self_improve run — manually, scheduled, or
   triggered by closure drops?** **Recommend**: manual + triggered
   on `closure_pct` regression > 2 percentage points (Spec 261).
   Scheduled runs risk noise; user-triggered + alarm-triggered keeps
   it cheap and relevant.
2. **What's the dedup window for the same chosen_gap?** **Recommend**:
   the cycle's input `window` parameter (default 7d) — re-proposing
   the same gap within the same window is wasted work; outside the
   window, it may legitimately re-surface.
3. **Should self_improve produce one proposal or up to N?**
   **Recommend**: ONE per cycle — focus + reviewability beats
   throughput; the loop runs again next cycle if more gaps remain.
