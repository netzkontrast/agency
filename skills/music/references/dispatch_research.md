<!-- agency-generated: v1 -->
# music.dispatch_research

Fan out to N specialists via agency.research (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `research_id, specialists (defaults to all), album.` |  |  |

## Returns

``{research_id, dispatched_to, count}``.

## Chain-next

``music.capture_claim`` per finding.

## Details

(no further detail)

## Example

```bash
agency-music-dispatch_research --intent-id $IID …
```
