---
spec_id: "232"
slug: editorial-pipeline-llm-judge
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "122"
depends_on: ["122", "178", "224", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_editorial_llm_judge.py
---

# Spec 232 — editorial pipeline: optional judged findings

## Why

Spec 122 ships 5 decidable prose checks + 3 editorial-stage gates + 2
walkable skills (developmental-editor / line-editor). The decidable
checks miss judgement-level findings (pace, voice authenticity, theme
landing). Mirroring Spec 178 (analyze judge axis) and Spec 224 (novel
gates judge), the editorial checks gain an optional `judge=True`,
tagged distinctly, feeding the dogfood loop.

## Done When

- [ ] **Each `check_*` gains `judge=True`** — return shape becomes
      `CheckResult = {findings: list[Finding], decidable_count: int,
      judged_count: int}` where `Finding = {kind: Literal["decidable",
      "judged"], severity, locus, message, confidence: float | None}`.
      Invariant: `decidable_count + judged_count == len(findings)` AND
      `all(f.confidence is None for f in findings if f.kind == "decidable")`.
- [ ] **Advisory-only invariant** — judged findings NEVER raise gate
      severity above WARN; only decidable findings can ERROR/block.
      Asserted: `not any(f.severity == "error" for f in findings
      if f.kind == "judged")`.
- [ ] **Developmental-editor + line-editor walks chain optional judge
      phases** — opt-in via `judge=True`; phase output preserves the
      decidable/judged partition so downstream consumers can filter.
- [ ] **Judged findings → Reflections** (Spec 150) — invariant: every
      judged finding emits exactly one Reflection node with
      `scope="editorial_judge"` and back-pointer to the gate run; the
      dogfood loop classifies recurrent patterns.
- [ ] **Output budget honored** (Spec 146) — judged-phase prompt prefix
      is the ontology fragments + style guide, byte-stable per novel.
- [ ] **Failure modes** — Driver unavailable (Spec 147) → judged
      phase SKIPPED with `Codes.DRIVER_UNAVAILABLE` carried as a WARN
      finding, never errors the gate; Driver returns malformed JSON →
      `Codes.JUDGE_PARSE_FAILED`, finding logged but not surfaced
      to the author; cache miss is tolerated (judged passes are
      stochastic, never re-played on cache).
- [ ] Test: gate returns tagged judged finding; decidable unchanged.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a chapter with 2 decidable check failures (POV slip + tense
        drift) and one weak voice-authenticity passage
When:   check_voice_authenticity(judge=True) runs with mocked Driver
        returning {confidence: 0.7, locus: "p3 line 4",
                   message: "voice flattens into reportage"}
Then:   CheckResult.decidable_count == 2 AND
        CheckResult.judged_count == 1 AND
        the judged finding has severity == "warning" (never "error") AND
        a Reflection node with scope="editorial_judge" exists pointing
        at this gate run

Given:  Driver is unreachable
When:   check_pace(judge=True) runs
Then:   findings include exactly the decidable subset AND a WARN entry
        with Codes.DRIVER_UNAVAILABLE — the decidable gate result is
        unchanged from the judge=False call
```

## Interconnects

- Spec 178 + Spec 224 are the pattern · **dogfood** (150).
- **LLM-driver chain** (147) — Driver is the judge backbone; honors
  output_config.format with the Finding schema.
- Spec 146 (output-prefix) — judged-phase prefix is byte-stable.
- Spec 137 (canon-status) — judged findings are `proposal` until the
  author accepts them as actionable.
- Spec 240 (scene-writer iterate-to-gate) — judged findings feed the
  revision loop without blocking it.

## Open questions

1. **Confidence threshold for surfacing.** Show judged findings below
   0.6? **Recommend:** surface all, tag low-confidence visibly — the
   author judges relevance, not the engine.
2. **Reflection-spam guard.** Long manuscripts produce many findings.
   **Recommend:** dedupe Reflections by `(scope, locus_hash,
   message_signature)` within a single gate run.
3. **Decidable + judged on same locus.** Merge findings? **Recommend:**
   keep separate entries; the kind partition is load-bearing.
