<!-- agency-generated: v1 -->
# frugal.set_level

Persist the frugal level (durable across processes via the Spec 334 config).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `level (str — off|lite|full|ultra; an invalid value falls back to full).` |  |  |

## Returns

``{level}`` — the normalized, persisted level.

## Chain-next

the new level governs the SessionStart inject + the per-verb stamp.

## Details

(no further detail)

## Example

```bash
agency-frugal-set_level --intent-id $IID …
```
