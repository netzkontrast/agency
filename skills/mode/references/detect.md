<!-- agency-generated: v1 -->
# mode.detect

Rank the behavioral modes by decidable trigger overlap with ``context`` (read-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `context (str — free text to match the modes against).` |  |  |

## Returns

``{matches: [{mode, score}], top}`` (``top`` empty if none).

## Chain-next

mode.activate(mode=top, context=...).

## Details

(no further detail)

## Example

```bash
agency-mode-detect --intent-id $IID …
```
