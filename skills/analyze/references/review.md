<!-- agency-generated: v1 -->
# analyze.review

Headless code-quality review for CI — never pauses; risky remedies auto-declined.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — filesystem scope; '' = current dir), mode (one of review/audit/debt/test/health/sweep), scope (str — informational scope description; '' = auto-detect), host_completion (dict — Spec 279 resume` |  | the host's inference reply, passed back to fold the judgment findings in). |

## Returns

{scope_line, findings:[...], iron_law_passed, mode, headless:True, gated:[...], score, counts, gate, [llm_delegate], judged_files}.

## Chain-next

analyze.sarif(...) for SARIF / code-scanning upload (Spec 382).

## Details

The CI actor's entry point (Spec 380 §3a, Cockburn + Hightower fix). Shares the same engine as develop.review but NEVER blocks on a gate or confirmation prompt: risky remedies are reported in gated:[] and auto-declined, not applied. Runs BOTH passes (Spec 380 core): the decidable scanners + the LLM judgment pass (the reasoning-heavy R2/R3/T1… risks), merged on (risk_code, file, line). Judgment routes through the Spec 352/279 seam (OpenRouter free-first → driver → MCP host-sampling → host-delegate), so no API key is needed; with no backend at all it degrades to decidable-only and surfaces an `llm_delegate` envelope (Hightower CI path). Use when: running code-quality diagnosis in CI or any non-interactive context where blocking for confirmation is forbidden. Do NOT use when: interactive triage or remedy is needed — use develop.review + develop.remediate instead.

## Example

```bash
agency-analyze-review --intent-id $IID …
```
