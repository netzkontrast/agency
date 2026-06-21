<!-- agency-generated: v1 -->
# analyze.score

Compute the Health Score (Spec 373) from findings × preset — READ-ONLY.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `findings (list of wire-shape finding dicts — severity + risk_code), preset (strict|balanced|legacy-friendly; default balanced).` |  |  |

## Returns

{score, preset, top_leverage:[finding,...], deductions:{tier:int}}.

## Chain-next

analyze.sarif / document.render the report (Spec 374).

## Details

``score = max(0, 100 - Σ deduction(tier, preset))`` — the per-tier deductions are a documented tunable budget (strict/balanced/legacy-friendly, ``data/score-presets.json``), computed live every run, never pinned (rule 8). ``top_leverage`` names the highest-impact fixes (deduction_weight × occurrence_count — Wiegers). An unknown preset falls back to balanced (Spec 373 §2). Pure transform — no graph write; the QualityRun history node is a later slice. Use when: turning a finding set into a tunable Health Score + the highest-leverage fixes (CI gate, report Summary).

## Example

```bash
agency-analyze-score --intent-id $IID …
```
