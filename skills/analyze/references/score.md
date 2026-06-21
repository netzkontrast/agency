<!-- agency-generated: v1 -->
# analyze.score

Compute the Health Score (Spec 381) from findings × preset/config — READ-ONLY.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `findings (list of wire-shape finding dicts — severity + risk_code), preset (strict|balanced|legacy-friendly; '' → config strictness), config (dict — the quality` |  | block; optional). |

## Returns

{score, preset, top_leverage, deductions, config_notes, scored_findings}.

## Chain-next

analyze.sarif / document.render the report (Spec 382).

## Details

``score = max(0, 100 - Σ deduction(tier, preset))`` — the per-tier deductions are a documented tunable budget (strict/balanced/legacy-friendly, ``data/score-presets.json``), computed live every run, never pinned (rule 8). ``top_leverage`` names the highest-impact fixes (deduction_weight × occurrence_count — Wiegers). An unknown preset falls back to balanced. §2 config: an optional ``quality:`` block tunes the bar — ``disable`` (drop risks), ``focus`` (keep ONLY these), ``ignore`` (glob-exclude files), ``severity`` (override a risk's tier), ``strictness`` (the preset when ``preset`` is not given explicitly). Validation is surfaced in ``config_notes``, never fatal (focus+disable → both ignored; bad strictness → balanced). Pure transform — no graph write; the QualityRun history node is a later slice. Use when: turning a finding set into a tunable Health Score + the highest-leverage fixes (CI gate, report Summary).

## Example

```bash
agency-analyze-score --intent-id $IID …
```
