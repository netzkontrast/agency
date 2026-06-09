<!-- agency-generated: v1 -->
# music.mono_fold_check

Phase-cancellation check via AudioDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, path.` |  |  |

## Returns

``{album, path, cancellation_db, phase_safe}``.

## Chain-next

rebalance the mix on phase_safe=False.

## Details

(no further detail)

## Example

```bash
agency-music-mono_fold_check --intent-id $IID …
```
