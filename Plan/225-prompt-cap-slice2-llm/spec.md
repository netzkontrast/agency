---
spec_id: "225"
slug: prompt-cap-slice2-llm
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "109"
depends_on: ["109", "147", "082", "201", "146", "150", "167", "149", "229", "226"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/prompt/_main.py
  - tests/test_prompt_cap_slice2.py
---

# Spec 225 — prompt capability Slice 2 (LLM build + optimize)

## Why

Spec 109 (prompt-capability) is Partial — Slice 1 shipped 9 verbs;
Slice 2 names "7 remaining verbs (build, register_builder, optimize,
score_output, analyze_iteration, register_anti_pattern, list_templates,
register_template)". The `optimize` / `score_output` / `analyze_iteration`
verbs are inherently LLM-mediated — they need the Spec 147 Driver. And
109's Followup notes "Approx-token boundary uses 4-chars/token heuristic;
Spec 082 TokenCounter swap deferred" — Spec 201 (API token count) lands
the authoritative count.

## Done When

- [ ] **The 7 Slice-2 verbs ship** with typed return shapes:
      ```python
      BuildResult     = {"prompt": str, "template_id": str, "tokens": int,
                         "cache_safe_prefix_tokens": int}
      OptimizeResult  = {"before": BuildResult, "after": BuildResult,
                         "delta_tokens": int, "delta_quality": float,
                         "target": Literal["tokens","quality","both"],
                         "iterations": int}
      ScoreOutput     = {"score": float, "rubric_hits": list[str],
                         "rubric_misses": list[str], "confidence": float}
      IterationReport = {"iterations": list[ScoreOutput],
                         "converged": bool, "stop_reason": str}
      ```
      `build`/`optimize`/`score_output`/`analyze_iteration` route through
      the Spec 147 Driver with `output_config.format`; `register_*` are
      registry writes returning `{registry_id, hash}`.
- [ ] **TokenCounter swap is the AUTHORITATIVE source** — the 4-chars
      heuristic is gone from prompt code (`grep` over the cap returns
      zero hits). Local cl100k via Spec 082; API count via Spec 201
      when `[anthropic]` extra installed. Invariant: every returned
      `tokens` field is sourced from the live counter, never computed
      from `len(text) // 4`.
- [ ] **Generation honors output-budget discipline** (Spec 146) — built
      prompts carry a `cache_safe_prefix_tokens` field; lint asserts the
      prefix is byte-deterministic (no `datetime.now()`/UUIDs in the
      template's prefix slot).
- [ ] **Optimize-delta invariant** — for `target="tokens"`,
      `result.after.tokens < result.before.tokens` OR `iterations == 0`
      (gave up). For `target="quality"`,
      `result.after.score >= result.before.score`. Never both worsen.
- [ ] **Score-reflection edge** — every `score_output` call emits a
      `Reflection(scope="prompt-score")` whose body is consumable by
      Spec 150's classifier (the dogfood loop sees prompt quality drift).
- [ ] **Failure modes** (touches LLM): `Codes.DRIVER_REFUSAL` propagated
      from Spec 147; `Codes.OPTIMIZE_NO_IMPROVEMENT` when iterations
      exhaust without delta; `Codes.SCORE_UNPARSEABLE` when the Driver's
      structured output fails schema validation (degrade to keyword
      classifier with `confidence=0.3`, never silent zero).
- [ ] **109 row flips toward Shipped** with derived completion %
      (Spec 149 reads the verb count off the live registry).
- [ ] Test: `optimize(target="tokens")` reduces a fixture prompt's
      `tokens` field strictly; `score_output` returns the typed shape;
      TokenCounter swap verified by grep-for-magic-number (zero hits).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a 600-token prompt fixture and target="tokens"
When:   prompt.optimize(prompt_id="fx-1", target="tokens", max_iter=3)
Then:   returns OptimizeResult with after.tokens < before.tokens,
        delta_tokens > 0, iterations <= 3,
        every tokens field sourced from Spec 082/201 (not //4)

Given:  the Driver returns malformed JSON for score_output
When:   prompt.score_output(...) runs
Then:   degrades to keyword classifier, returns ScoreOutput with
        confidence == 0.3, never raises; the failure is recorded as
        a Reflection(scope="driver-refusal") for Spec 150 to see

Given:  a built prompt whose prefix slot contains uuid4()
When:   the build-prefix lint runs (Spec 146 family)
Then:   lint fails with PREFIX_NONDETERMINISTIC at the call site
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `DRIVER_REFUSAL` (Spec 147) | propagate typed; never retry the same call |
| `OPTIMIZE_NO_IMPROVEMENT` | return after with `iterations==0`, never silent zero |
| `SCORE_UNPARSEABLE` | degrade to keyword classifier, `confidence==0.3` |
| `PREFIX_NONDETERMINISTIC` (Spec 146 lint) | hard fail at build site |
| TokenCounter unavailable (`[anthropic]` missing) | fall back to cl100k local; never `len(text)//4` |
| Optimize budget exhausted | return current best with `stop_reason="budget"` |

## Interconnects

- **LLM-driver chain** (147) — `build`/`optimize`/`score_output`/
  `analyze_iteration` are LLM-driven; `output_config.format` enforces
  the typed shape.
- **Output-budget chain** (146) — built prompts honor cache-safe-prefix
  discipline; `cache_safe_prefix_tokens` is a derived field.
- **TokenCounter chain** (082 + 201) — the 4-chars heuristic dies here.
- **Dogfood-loop chain** (150) — score reflections feed amendment
  classification.
- Spec 167 (prompt-quality follow-up) consumes `IterationReport` for
  longitudinal accept-rate.
- Spec 149 (derived docs) reads verb count for the 109 row + completion %.
- Spec 229 (session-driver Slice 2) walkable skills compose these prompts.
- Spec 226 (thinking cap Slice 2) shares the Driver wiring pattern;
  parity test asserts both caps emit byte-equal typed shapes for
  equivalent inputs.
- The prompt cap is the engineering surface the whole charter leans on.

## Open questions

1. Optimize for tokens or quality? **Recommend**: both, exposed as one
   verb with `target: Literal["tokens","quality","both"]` (the typed
   return shape carries both deltas). One verb keeps the surface lean;
   the typed return distinguishes intent.
2. **Score rubric source.** Hand-authored or derived from prior
   Reflections? **Recommend**: hand-authored v1 (vendored
   `prompt.score.rubric.md`), promote to derived-from-Reflections in
   Slice 3 once Spec 150's accept-rate exceeds 0.5.
3. **Convergence criterion for `analyze_iteration`.** Fixed
   `max_iter` or quality-delta floor? **Recommend**: both — stop on
   `max_iter` OR `delta_quality < 0.02` for 2 consecutive iterations;
   the typed `stop_reason` field names which fired.
