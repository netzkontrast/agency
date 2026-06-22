<!-- agency-generated: v1 -->
# loop.recommend_council

Report verdict-source coverage + a cross-family recommendation (365).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str), host_family (str — the host's model family).` |  |  |

## Returns

``{members, verdict_sources_ok, missing, recommended, ...}``.

## Chain-next

add a judge member for any gate missing a verdict source.

## Details

(no further detail)

## Example

```bash
agency-loop-recommend_council --intent-id $IID …
```
