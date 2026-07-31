<!-- agency-generated: v1 -->
# novel.record_motif_echo

Log a motif echo in a scene (effect); mints the Motif on first sight (its ``first_event_chapter`` = this scene's chapter).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, motif_slug (e.g. rauschen|form|klick|phantom| resonanz — open set).` |  |  |

## Returns

``{motif_id, scene_id, motif_slug}``.

## Chain-next

``novel.motif_echo_report(novel_id)`` for the cap audit.

## Details

(no further detail)

## Example

```bash
agency-novel-record_motif_echo --intent-id $IID …
```
