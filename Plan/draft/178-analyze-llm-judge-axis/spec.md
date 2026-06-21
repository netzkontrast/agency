---
spec_id: "178"
slug: analyze-llm-judge-axis
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "042"
depends_on: ["042", "147", "166", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/analyze/_judge.py  (NEW)
  - tests/test_analyze_judge.py
---

# Spec 178 — analyze LLM-judge axis (judgement findings)

## Why

Spec 042 ships 4-axis DECIDABLE analysis (quality/security/performance/
architecture) — deliberately no LLM judgement. But many real findings
need judgement (is this abstraction premature? is this naming
misleading?) that decidable rules can't reach. With the Spec 147
Driver, analyze can add an OPTIONAL judgement axis whose findings are
clearly tagged `judged` (not `decidable`), so the two never blur — the
decidable axes stay the trustworthy core, judgement augments.

## Done When

- [ ] **`analyze.run(..., judge=True)`** adds a `judged` axis — the Spec
      147 Driver scores the target against a rubric, returning a typed
      shape:
      ```python
      JudgedFinding = {
        "axis":         Literal["judged"],          # never "decidable"
        "rubric_id":    str,                        # vendored rubric file
        "file":         str,
        "line_range":   tuple[int, int] | None,
        "severity":     Literal["info","warn","error"],
        "confidence":   float,                      # 0..1; Driver-reported
        "rationale":    str,                        # ≥ 40 chars
        "driver_model": str,                        # for provenance
      }
      ```
- [ ] **Invariant — strict tag separation.** `count(findings, axis="judged")`
      and `count(findings, axis ∈ decidable_axes)` are reported as
      DISJOINT subtotals; the union never overwrites either. A test
      asserts the decidable subtotal is byte-identical with `judge=True`
      vs `judge=False` on the same input.
- [ ] **Invariant — provenance moat.** Every `JudgedFinding` produces
      exactly one `Reflection` node with PRODUCES-from edges to the
      Driver `Invocation` (Spec 150 consumes these).
- [ ] **Invariant — bounded cost.** Per-file token spend ≤ a documented
      cap (`judge_tokens_per_file`, default 4000); a run aggregates
      `sum(usage.input_tokens + usage.output_tokens)` and warns above
      the cap × file-count.
- [ ] **Degrades cleanly** without `[anthropic]` (judge axis absent;
      decidable axes byte-identical to Spec 042 baseline).
- [ ] **Judged findings become `Reflection`s** feeding Spec 150's
      classifier (dogfood loop).
- [ ] Test: judge axis returns tagged findings (mocked Driver);
      decidable counts unchanged with/without judge.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a file with a 3-level Strategy hierarchy used by one caller
When:   analyze.run(path=..., judge=True, rubric="premature-abstraction")
Then:   returns Result{
            decidable: {quality: 2, security: 0, ...},
            judged:    [JudgedFinding{
                          rubric_id: "premature-abstraction",
                          severity:  "warn",
                          confidence: 0.78,
                          rationale: "Strategy hierarchy has 1 caller; ..."
                       }]
        }
        AND decidable subtotal == analyze.run(path=..., judge=False).decidable
        AND each JudgedFinding has a PRODUCES edge to a Reflection node
```

## Failure modes (Nygard)

| Failure | Axis response |
|---|---|
| `DriverError.REFUSAL` | drop the file's judged findings; decidable axis unaffected; emit Reflection(`scope="judge-refusal"`) |
| `DriverError.RATE_LIMITED` | retry with backoff per Spec 147; if budget exhausted, mark `judged` axis `partial=True` |
| `DriverError.TIMEOUT` | skip the file; aggregate `skipped_files` count in the report |
| Output schema violation | typed `Codes.JUDGE_BAD_SHAPE`; never merge into decidable counts |
| Token cap exceeded | warn + truncate to first-cap files; report carries `truncated_at=N` |

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop chain** (150).
- Spec 166 (extras) is the decidable-analyzer sibling and the
  fallback path when `[anthropic]` is absent.
- Spec 146 (output-prefix) governs the rubric-prompt cache discipline.
- Spec 179 (document-render LLM narrative) shares the
  "tag LLM-generated content distinctly" pattern; align tag vocabulary
  (`judged` vs `narrated`).
- Spec 183 (intent-chain opportunity detector) consumes `judged`
  Reflections as a candidate source for "promote-to-verb" proposals.
- Spec 170 (doctor) reports judge-axis readiness.

## Open questions

1. **Judge per-file or per-finding?** **Recommend**: per-file with a
   bounded finding cap (default 5 findings/file) — keeps token cost
   predictable; per-finding mode is a Slice-2 if recall demands it.
2. **Rubric vendoring location.** **Recommend**:
   `agency/capabilities/analyze/_rubrics/<rubric_id>.md` — co-located
   with the axis code; CI lints each rubric for the four required
   sections (`Criteria`, `Severity ladder`, `Cite-back format`,
   `Out-of-scope`).
3. **Confidence threshold for emission.** **Recommend**: emit all
   findings; let downstream Spec 150 classifier filter by confidence —
   the raw stream is the dogfood signal.
