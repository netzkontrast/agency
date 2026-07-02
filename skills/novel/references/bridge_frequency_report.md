<!-- agency-generated: v1 -->
# novel.bridge_frequency_report

Per mode-block share of soft-routed (bridge) scenes (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{blocks: [{label, from_chapter, to_chapter, soft_share, target, deviation, verdict}], curve_intact}``.

## Chain-next

adjust routing / mode-block targets, re-run.

## Details

(no further detail)

## Example

```bash
agency-novel-bridge_frequency_report --intent-id $IID …
```
