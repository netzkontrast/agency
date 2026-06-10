<!-- agency-generated: v1 -->
# novel.check_voice_consistency

Per-chapter voice-signature outlier check (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `bodies (list[str] — one per chapter, in order), z_threshold (float — std deviations).` |  |  |

## Returns

``{passed, signatures, outliers: [{index, feature, z}]}``.

## Chain-next

``novel.line_gate`` for per-chapter line-level scrutiny.

## Details

Computes a 3-feature signature per body (avg sentence length / filter-word density / flowery-attribution density), then flags any chapter whose feature z-score exceeds ``z_threshold`` (default 2.0 — the documented tunable per spec Open Q1).

## Example

```bash
agency-novel-check_voice_consistency --intent-id $IID …
```
