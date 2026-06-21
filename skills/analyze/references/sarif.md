<!-- agency-generated: v1 -->
# analyze.sarif

Render Findings as SARIF 2.1.0 for code-scanning — READ-ONLY (Spec 382 §1).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `findings (list of wire-shape finding dicts), max_results (int — 0 = uncapped).` |  |  |

## Returns

{sarif, rule_count, result_count, total, truncated}.

## Chain-next

upload `sarif` to GitHub code-scanning in CI (Spec 382 §3).

## Details

Straight from the structured findings, NO parsing (brooks' report-parse is dropped — findings are born structured). The ``rules`` set is DERIVED from the live decay-risk registry (``decay-risks.json`` + any custom ``Cx``), so it never drifts (rule 8); ``level`` maps from the finding's tier (critical→error, warning→warning, suggestion→note); the ``message`` is the Iron Law (Symptom + Consequence + Remedy). ``max_results`` caps the emit with a truncation locator ("N of M shown") — never a silent drop (#9); the full set stays in the graph. Use when: emitting code-quality findings for GitHub code-scanning / a CI SARIF artefact.

## Example

```bash
agency-analyze-sarif --intent-id $IID …
```
