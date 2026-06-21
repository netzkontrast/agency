---
spec_id: "245"
slug: sensitivity-managed-reader
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "135"
depends_on: ["135", "147", "180", "150", "146", "252", "247"]
vision_goals: [4, 8]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_sensitivity_managed.py
---

# Spec 245 — sensitivity reader: Managed-Agent role

## Why

Spec 135 ships SensitivityFinding + the 4-phase walk (scan → review →
revise → sign-off). Phase 2 (review) is the human reader's slot —
elevating `info` findings. With Spec 147 + Managed-Agents (Spec 180
pattern), the review can dispatch to a sensitivity-reader Agent
configured with a specific lens (cultural, disability, gender etc.) —
output is always `proposal` findings the human confirms.

## Done When

- [ ] **`sensitivity_review_managed(scene_id, lens="cultural"|"disability"|
      "gender"|"trauma"|str) -> SensitivityReviewProposal`** — typed return
      `SensitivityReviewProposal{ scene_id, lens, findings:
      list[SensitivityFinding{span: SpanRef, severity: Literal["info",
      "warn", "block"], category: str, rationale: str, suggested_revision:
      str | None}], status: Literal["proposal"], driver_model: str,
      session_id: ManagedSessionId, judged_at: datetime }`. Dispatches a
      Managed-Agent session per Spec 180; all findings land tagged
      `judged` and `status="proposal"`.
- [ ] **Invariant: every finding is advisory until human confirm** —
      `all(f.status == "proposal" for f in findings)` AND no finding with
      `severity > info` writes a Lock without `confirm_finding()` (the
      135 doctrine). Property test asserts elevation requires explicit
      author action across a fixture sweep.
- [ ] **Invariant: lens scoping is honoured** —
      `all(f.category in LENS_CATEGORIES[lens] for f in findings)`; a
      cultural-lens dispatch never returns a disability finding. The
      LENS_CATEGORIES map is derived from registered lens definitions,
      not hand-pinned.
- [ ] **Invariant: dogfood feedback is structural** — when ≥ N (default
      3) findings share `(category, suggested_revision_pattern)` across
      scenes in the same novel, a Spec 150 amendment proposal is minted;
      relationship `proposals_minted == count(recurring_clusters)`.
- [ ] **Failure modes**: Managed-Agent `SESSION_TIMEOUT` → return
      partial findings + `status="proposal_incomplete"`, never silent
      drop; Driver `REFUSAL` on graphic content → emit single finding
      with `category="refusal"` + log to Spec 150 (refusals are signal);
      `RATE_LIMITED` → retry-with-jitter per Spec 147; cache prefix
      invalidated by lens-config drift → re-emit with sorted lens-config
      for byte-stability (Spec 146); empty scene → zero findings, NOT
      error (visibility over silence).
- [ ] Test: dispatch returns scoped findings (mocked session); recurring
      cluster mints an amendment.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a scene depicting a disabled character's medical exam, with
        prior session findings flagging "infantilizing register" in 2
        other scenes
When:   sensitivity_review_managed(scene_id, lens="disability")
        dispatches; the Managed-Agent reviews with disability-lens
        prompt; returns 4 findings (1 warn, 3 info)
Then:   every finding carries status="proposal" + category in
        LENS_CATEGORIES["disability"]; no Lock is minted automatically;
        the "infantilizing register" cluster (now 3 occurrences) mints
        a Spec 150 amendment proposal for the project's R-rule set
        (Spec 250); author confirms the warn finding via
        confirm_finding() before it elevates
```

## Interconnects

- Spec 180 (Managed-Agent fan-out) is the dispatch pattern.
- **LLM-driver chain** (147) — Managed-Agents bridge; human-in-loop
  preserved by Spec 135 doctrine.
- **Output-budget chain** (146) — scene-context payload obeys envelope;
  lens-config sits in the cacheable prefix.
- **Dogfood-loop chain** (150) — recurring findings classify into
  R-rule amendment proposals (Spec 250).
- Spec 252 (managed skill walks) — sensitivity-review can run as a
  walk phase under the same Managed-Agent driver.
- Spec 247 (canon-lock approval) — elevated findings flow through the
  propose → approve → canon discipline.

## Open questions

1. **Lens composition.** Allow `lens=["cultural","gender"]` multi-lens
   dispatch? **Recommend**: yes — but mint one Managed-Agent session per
   lens (parallel via Spec 180), merge findings client-side, dedupe by
   (span, category). Single multi-lens prompt dilutes the prefix.
2. **Severity ceiling for the Driver.** Cap Driver-minted severity at
   `warn` to force human review for `block`? **Recommend**: yes — the
   Driver NEVER mints `block` directly; only the author can elevate
   `warn` → `block` via confirm. Preserves 135 doctrine literally.
3. **Reviewer model selection.** Pin to a specific model or let Spec 147
   pick? **Recommend**: let Spec 147 pick by default, but allow
   `model_override` for reproducibility audits — sensitivity findings
   are a context where model drift matters.
