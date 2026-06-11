---
spec_id: "243"
slug: structure-templates-llm-anchor
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "133"
depends_on: ["133", "147", "217", "150", "146", "137", "237"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_structure_llm_anchor.py
---

# Spec 243 — story-structure LLM anchoring

## Why

Spec 133 ships 5 vendored templates (Save the Cat / Three-Act / Hero's
Journey / Story Circle / Snowflake) + `apply_structure` + `anchor_beat`
+ `check_structure_coverage` (flags `|actual-target| > 0.10`). Anchoring
each beat to a chapter is currently manual. With Spec 147, the Driver
can SUGGEST anchors for unanchored beats by matching beat descriptions
against chapter summaries — author confirms, never auto-anchors.

## Done When

- [ ] **`suggest_beat_anchors(novel_id, template_id) -> BeatAnchorProposal`** —
      typed return `BeatAnchorProposal{ proposals: list[{beat_id, chapter_id,
      confidence: float, rationale: str, evidence_span: SpanRef}], status:
      Literal["proposal"], driver_model: str, judged_at: datetime }`. Driver
      uses `output_config.format` for structured output (Spec 147).
- [ ] **Invariant: anchor proposals are advisory** — every proposal lands
      with `status="proposal"` (Spec 137); zero proposals auto-promote to
      `canon`. Test asserts `all(p.status == "proposal" for p in proposals)`
      across a property sweep.
- [ ] **Invariant: coverage re-check follows every anchor confirmation** —
      `check_structure_coverage` runs as a post-confirm hook; verdict
      delta is recorded on the beat-anchor edge. Relationship:
      `coverage_runs_count == confirmed_anchors_count` over the session.
- [ ] **Invariant: confidence monotonic with evidence overlap** —
      proposals with overlapping evidence spans across two beats have
      `confidence_a + confidence_b <= 1.0 + tolerance`; a property test
      generates pairs and asserts the relationship.
- [ ] **`build-novel` (Spec 217) chains it** as an optional phase, gated by
      a `--llm-anchor` flag; the decidable pass remains the default.
- [ ] **Failure modes**: Driver `REFUSAL` → no proposals minted, walk
      continues with manual anchoring; `RATE_LIMITED` → retry-with-jitter
      per Spec 147; `BAD_REQUEST` on schema-violating output → reject,
      log to dogfood (Spec 150); empty chapter summaries → proposals
      flagged `confidence=0` rather than omitted (visibility over silence).
- [ ] Test: fixture novel + template yields anchors that pass coverage.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a novel with 12 chapters, a Save-the-Cat template, 3 beats
        already anchored manually, 12 beats unanchored
When:   suggest_beat_anchors(novel_id, "save-the-cat") runs with the
        AnthropicDriver (Spec 147), output_config.format on
        BeatAnchorProposal
Then:   return.proposals has len <= 12 (unanchored only);
        every proposal carries status="proposal" + rationale + evidence_span;
        coverage_check re-runs only after author confirm_anchor(); and
        no beat-edge is written to the graph with provenance=auto
```

## Interconnects

- **LLM-driver chain** (147) — uses canonical AnthropicDriver surface.
- **Dogfood-loop chain** (150) — rejected proposals + reason classify
  into amendment proposals (e.g. "beat description too abstract for
  matching" → template-prose amendment).
- **Output-budget chain** (146) — proposal payload obeys the response
  envelope; the template prefix is cacheable, the per-novel body is not.
- Spec 217 (build walkable) chains it as an optional `--llm-anchor` phase.
- Spec 137 (canon locks) — proposals flow through the same propose/approve
  workflow; canon promotion mints a Lock.
- Spec 237 (scene-brief cache) — beat descriptions share the cache-prefix
  discipline since they recur across anchor calls.

## Open questions

1. **Per-template cap on proposed anchors.** Cap proposals per template
   to avoid flood? **Recommend**: derive — propose at most one proposal
   per unanchored beat; never multi-anchor a beat in a single call.
2. **Confidence threshold for surfacing.** Suppress low-confidence
   proposals? **Recommend**: surface all proposals but sort
   descending; let the author skim and reject. Suppression hides
   useful failure data from the dogfood loop (150).
3. **Re-anchoring of confirmed beats.** Allow re-suggest after manual
   confirm? **Recommend**: yes, but only with explicit `force=True`;
   default skips already-anchored beats to keep the proposal set small.
