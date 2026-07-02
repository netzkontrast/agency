<!-- agency-generated: v1 -->
# novel.plant_anchor

Plant a named foreshadowing anchor in a scene (effect) — earliest plant kept; re-planting adds a PLANTS edge without moving the origin.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, name (e.g. "734", "Telefon-Stille").` |  |  |

## Returns

``{anchor_id, name, planted_chapter}``.

## Chain-next

``novel.pay_off_anchor`` at the payoff scene; ``novel.anchor_status_report`` for the audit.

## Details

(no further detail)

## Example

```bash
agency-novel-plant_anchor --intent-id $IID …
```
