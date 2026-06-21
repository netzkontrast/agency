<!-- agency-generated: v1 -->
# develop.review

Diagnose code decay using the brooks Iron Law — READ-ONLY (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `mode (one of review/audit/debt/test/health/sweep; default "review"), scope ('' = auto-detect from git; explicit path or scope string).` |  |  |

## Returns

{scope_line, findings:[...], iron_law_passed, mode}. Token-bounded preview (≤20 findings); full detail records via the decidable phase of the quality-{mode} skill walk.

## Chain-next

develop.remediate(review_id) to apply fixes; analyze.sarif(...) for SARIF / CI output (Spec 382).

## Details

Runs the decidable analysis pass for the requested mode, tags findings with decay risk codes (Spec 360 _decay.tag), and checks the Iron Law gate (all brooks findings must carry consequence + remedy — Wiegers fix). Use when: diagnosing code decay or maintainability using the Iron Law (Symptom → Source → Consequence → Remedy) across six scopes (PR review · architecture audit · tech debt · test quality · health dashboard · full sweep). READ-ONLY — no files mutated. Do NOT use when: you want to apply fixes (use develop.remediate); you want raw decidable findings without Iron Law enrichment (use analyze.run).

## Example

```bash
agency-develop-review --intent-id $IID …
```
