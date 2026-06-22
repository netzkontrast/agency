<!-- agency-generated: v1 -->
# develop.review

Diagnose code decay using the brooks Iron Law — INTERACTIVE (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `mode (one of review/audit/debt/test/health/sweep; default "review"), scope ('' = auto-detect from git; explicit path or scope string), driver (judgment backend` |  | subagent|jules|openrouter; default subagent), host_completion (Spec 279 resume — the subagent's inference reply, passed back to fold + gate the judgment findings). |

## Returns

{scope_line, findings:[...], iron_law_passed, mode, judgment:{...}, [llm_delegate]}. When no backend is wired yet, returns an `llm_delegate` envelope (model_hint "subagent") for the host to fulfil and resume via host_completion.

## Chain-next

develop.remediate(review_id) to apply fixes; analyze.sarif(...) for SARIF / CI output (Spec 382).

## Details

Runs BOTH passes (Spec 380 core): the decidable scanners + the LLM JUDGMENT pass (the reasoning-heavy R2/R3/T1… risks), then — unlike the headless analyze.review — pauses for a FINAL HUMAN-APPROVAL elicit before the judgment findings are accepted. The judgment backend is FIRST-CLASS and selectable via ``driver`` — all three route through the one Spec 352/279 seam (no external key required): - ``subagent`` (default) — a Claude agent the host dispatches; the delegate envelope is tagged ``model_hint="subagent"``. - ``jules`` — a remote Jules agent (envelope ``model_hint="jules"``). - ``openrouter`` — an OpenRouter free model when ``OPENROUTER_API_KEY`` is set (the seam routes free-first for plain text); else it delegates tagged ``model_hint="openrouter"``. Decidable findings always stand; only the LLM-PROPOSED judgment findings are gated by your approval (reject → dropped). Use when: diagnosing code decay or maintainability using the Iron Law (Symptom → Source → Consequence → Remedy) across six scopes (PR review · architecture audit · tech debt · test quality · health dashboard · full sweep), WITH a human approving the judgment. Do NOT use when: you want to apply fixes (use develop.remediate); you want non-interactive CI output (use analyze.review — it never pauses).

## Example

```bash
agency-develop-review --intent-id $IID …
```
