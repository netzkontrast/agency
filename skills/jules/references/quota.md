<!-- agency-generated: v1 -->
# jules.quota

Count sessions created today (UTC).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `daily_limit (int — caller-supplied budget; 0 = no headroom calc).` |  |  |

## Returns

``{used, daily_limit, headroom}`` (headroom only when ``daily_limit > 0``).

## Chain-next

gate further ``jules.dispatch`` calls on ``headroom > 0``.

## Details

The API has no quota surface; this is operational hygiene (lesson-15 §6).

## Example

```bash
agency-jules-quota --intent-id $IID …
```
