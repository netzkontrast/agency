<!-- agency-generated: v1 -->
# analyze.report

Render the Iron-Law quality report (Spec 382 §4) — READ-ONLY markdown.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `findings (wire-shape finding dicts), mode (review/audit/…), scope (str), score (int — the Health Score, Spec 381).` |  |  |

## Returns

{report, mode}.

## Chain-next

document.render / document.sync to persist + round-trip (Spec 292).

## Details

Projects the structured findings: a header with the Health Score, findings sorted by tier (critical→warning→suggestion) each as the Iron Law block (Symptom / Source / Consequence / Remedy), empty tiers omitted, a mermaid Module Dependency Graph in audit mode (R5), and a Summary. The render PATH is here; the template FILE is authored in Spec 384 (adopted via document.render then). Use when: producing the human-readable code-quality report from a review.

## Example

```bash
agency-analyze-report --intent-id $IID …
```
