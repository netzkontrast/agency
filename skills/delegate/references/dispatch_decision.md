<!-- agency-generated: v1 -->
# delegate.dispatch_decision

Apply the dispatch-vs-inline heuristic and return a recommendation.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `file_count (S2), exploration_needed (S3), parallelism (S4), est_duration_min (S5), expected_return_tokens (S1), mutates (S6 disqualifier), read_only (S7), driver_hint (S8), context_overlap (S9), cache_warmth (S10), local_budget_relevant (S11), use_llm (S12 — optional; consult the ``llm`` Driver after the heuristic; requires OPENROUTER_API_KEY), task_description (plain text fed to the LLM when use_llm=True), llm_confidence_threshold (float, default 0.75; LLM override only applied when its confidence exceeds this value).` |  |  |

## Returns

``{recommendation, driver, rationale, token_cost_estimate, local_budget_token_estimate, signals_fired}`` — the six-field payload documented in Spec 040 §"Done When". ``signals_fired`` reports which of the 11 (+ optional S12) swung the decision.

## Chain-next

when ``recommendation == 'dispatch'``, call ``delegate.fan_out`` (driver=, driver_verb=, items=, quota=); when ``inline``, execute in-process.

## Details

See ``skills/dispatch-decision/references/heuristics.md`` for the full eleven-signal rule table + the two budget models (local vs. Jules).

## Example

```bash
agency-delegate-dispatch_decision --intent-id $IID …
```
