<!-- agency-generated: v1 -->
# novel.reveal_timeline_report

The per-tier "who knows what when" map (transform) — every rule sorted by ``may_know_from_chapter`` (the KP §6.2 Reveal-Timeline).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, tier (optional filter).` |  |  |

## Returns

``{timeline: [{fact, tier, may_know_from_chapter, must_not_before, channel}], by_tier}``.

## Chain-next

``novel.reveal_gate(novel_id)`` before publication.

## Details

(no further detail)

## Example

```bash
agency-novel-reveal_timeline_report --intent-id $IID …
```
