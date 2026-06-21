<!-- agency-generated: v1 -->
# analyze.review

Headless code-quality review for CI — never pauses; risky remedies auto-declined.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — filesystem scope; '' = current dir), mode (one of review/audit/debt/test/health/sweep), scope (str — informational scope description; '' = auto-detect).` |  |  |

## Returns

{scope_line, findings:[...], iron_law_passed, mode, headless:True, gated:[...]}.

## Chain-next

analyze.sarif(...) for SARIF / code-scanning upload (Spec 357).

## Details

The CI actor's entry point (Spec 355 §3a, Cockburn + Hightower fix). Shares the same decidable engine as develop.review but NEVER blocks on a gate or confirmation prompt: risky remedies are reported in gated:[] and auto-declined, not applied. Decidable-only output when no LLM key (Hightower fix — the CI degradation path). Use when: running code-quality diagnosis in CI or any non-interactive context where blocking for confirmation is forbidden. Do NOT use when: interactive triage or remedy is needed — use develop.review + develop.remediate instead.

## Example

```bash
agency-analyze-review --intent-id $IID …
```
