---
spec_id: "258"
slug: dogfood-classifier-quality-loop
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "150"
depends_on: ["150", "147", "181", "199", "256", "264"]
vision_goals: [6]
affects:
  - agency/capabilities/dogfood/_main.py
  - tests/test_dogfood_quality_loop.py
---

# Spec 258 — dogfood classifier: rubric-eval quality loop

## Why

Spec 150 anchors the dogfood-loop chain — classifier emits amendment
proposals. Proposal QUALITY needs measurement; without it, the
classifier ships noise and the loop GOALS.md Goal 6 promises is "wired
but not load-bearing". The `claude-api` skill's Managed-Agents Outcome
surface (gradeable rubric, iterate-to-satisfied) is the natural
quality engine: the classifier proposes; a rubric grades "cites ≥1
reflection · names a real spec_id · op valid · rationale non-empty";
iterations satisfy or fail; the loop measures itself. The accept-rate
becomes the dogfood loop's vital sign — if it drops, something
upstream (embedder, rubric, model) regressed.

## Done When

- [ ] **Optional Managed-Agents Outcome path** — `parse_amendment(...,
      outcome=True)` uses a vendored `amendment.rubric.md` as a
      gradeable Outcome (claude-api skill). Rubric criteria are
      machine-checkable predicates, not free-form prose.
- [ ] **Typed `ProposalQuality` return shape**:
      ```python
      class ProposalQuality(TypedDict):
          proposal: AmendmentProposal      # the candidate
          rubric_scores: dict[str, bool]   # criterion -> pass
          iterations: int                  # how many Outcome rounds
          satisfied: bool                  # final verdict
          model: str                       # which model graded
          billed_tokens: int               # cost of the eval
      ```
- [ ] **Quality metric derived** (Spec 149) — `accept_rate =
      satisfied_count / total_proposals` over a rolling window; emitted
      as a graph node so the alignment matrix (Spec 191) reads it
      live. Regression alarm when `accept_rate` drops by > 25% of
      its rolling 14-day median.
- [ ] **Embedder upgrade (Spec 181) feeds candidate quality** — better
      reflection retrieval ⇒ proposals cite stronger evidence ⇒
      rubric pass rate climbs. The dependency is measurable: track
      correlation `(retrieval_recall_at_5, accept_rate)` over time.
- [ ] **Trigger validation via Spec 199** — proposals that propose
      new verbs/skills run through publish-roundtrip dry-run before
      acceptance; a proposal that creates a verb with a name
      collision (Spec 067) fails the rubric automatically.
- [ ] **Measurable invariants** (computed, never pinned):
      - `accept_rate in [0.0, 1.0]` and is reported, not asserted to a
        specific value
      - `iterations <= max_iterations` (config default 5; cost cap)
      - `satisfied == True ⇒ all(rubric_scores.values())` (invariant
        relationship — satisfaction must be grounded)
      - every `ProposalQuality` with `satisfied=False` produces a
        reflection naming WHICH criterion failed (debuggability)
- [ ] Test: outcome iterates a vague proposal to a sharp one (mocked);
      accept-rate derived correctly; regression alarm fires on
      synthetic drop.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  classifier emits a proposal {op:"amend", spec_id:"014",
        rationale:"loop should classify more"} — vague, no citation
When:   parse_amendment(..., outcome=True) runs the rubric loop with
        max_iterations=5
Then:   iteration 1 fails {cites_reflection:False, rationale_specific:False}
        iteration 2 retrieves 2 reflections, adds citations
        iteration 3 sharpens rationale to name the missing classifier path
        iteration 3 satisfies all 4 criteria → ProposalQuality{
        satisfied:True, iterations:3, billed_tokens:~4200}
        AND the proposal is enqueued as a PR-draft candidate

Given:  rolling 14-day accept_rate median is 0.62; today's window is 0.41
When:   Spec 149 derive-docs runs
Then:   regression alarm fires (0.41 < 0.62 * 0.75); a reflection node
        is emitted naming "accept_rate regression" with the per-criterion
        breakdown so the next session can diagnose

Given:  classifier proposes {op:"new_verb", name:"reflect.note"} — name
        already exists
When:   Spec 199 trigger validation runs as a rubric criterion
Then:   rubric fails {name_unique:False}; proposal rejected without
        burning Outcome iterations; reflection records the collision
```

## Failure modes (Nygard)

| Failure | Loop response |
|---|---|
| Classifier model refuses (`stop_reason: "refusal"`) | Route through Spec 256 fallback; if exhausted, proposal is dropped and a `Codes.PROPOSAL_REFUSED` reflection is recorded |
| Rubric Outcome never satisfies within `max_iterations` | Return `satisfied:False`; reflection names final failing criteria; do NOT silently accept |
| Embedder regression upstream (Spec 181) drops recall | `accept_rate` drops; regression alarm names the embedder change as the suspect via correlation |
| Rubric criterion drifts from rendered doc | Spec 149 doc-drift catches it; the rubric file carries a `<!-- doc-source -->` marker pointing at the canonical criterion list |
| Outcome graded by Fable 5, retention misconfigured | Spec 170 doctor pre-flights; never burns a request |
| Same proposal looped repeatedly without progress | Dedup by content-hash; second identical attempt is short-circuited to the cached `ProposalQuality` |

## Interconnects

- Spec 150 (parent classifier) — this spec adds the quality layer.
- Spec 147 (AnthropicDriver) — the Outcome surface ships through the
  canonical driver; refusal fallbacks (256) apply.
- Spec 181 (embedder upgrade) — upstream input that correlates with
  accept_rate.
- Spec 199 (publish roundtrip) — trigger validation as a rubric
  criterion.
- Spec 256 (refusal fallback) — required for the loop to survive
  Fable 5 safety classifier hits without breaking.
- Spec 264 (self-improvement meta-cap) — consumes `accept_rate` as a
  signal of which gap to attack next.
- Spec 261 (charter closing audit) — `accept_rate` is one of the
  closure dashboard's vital signs.
- **Dogfood-loop chain** completion.

## Open questions

1. **Rubric criteria — fixed or evolved?** **Recommend**: fixed set
   at v1 (4 criteria above), but the rubric file itself is a graph
   Artefact so future criteria additions are auditable and proposed
   THROUGH the loop (recursive dogfooding).
2. **Should accept_rate be reported per-source (verb that emitted
   the reflection)?** **Recommend**: yes — a single regression source
   is more actionable than an aggregate drop.
3. **Cost cap on the Outcome iterations?** **Recommend**:
   `max_iterations=5` and `max_billed_tokens=20000` per proposal;
   exceeding either short-circuits with `satisfied:False, reason:
   "cost_cap"` so the loop never runs away.
