<!-- agency-generated: v1 -->
# novel.record_leerstelle

Register a DELIBERATE Iser gap (effect) — so a reviewer sees the indeterminacy is intentional, not a defect.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, kind (fragmented-perspective | contradictory-footnote | temporal-scramble | pronoun-shift), note.` |  |  |

## Returns

``{leerstelle_id, scene_id, kind}``.

## Chain-next

``novel.leerstellen_report(novel_id)``.

## Details

(no further detail)

## Example

```bash
agency-novel-record_leerstelle --intent-id $IID …
```
