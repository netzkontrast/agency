<!-- agency-generated: v1 -->
# novel.check_pov_consistency

Per-chapter POV uniformity check across scenes (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, per_chapter: [{chapter_id, povs, mixed}]}``.

## Chain-next

``novel.line_gate``.

## Details

Walks each chapter's Scene nodes via SCENE_OF and groups POV values. A chapter with > 1 distinct POV (excluding scenes that declare ``pov=""``) is a flagged break.

## Example

```bash
agency-novel-check_pov_consistency --intent-id $IID …
```
