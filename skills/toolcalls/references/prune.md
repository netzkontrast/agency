<!-- agency-generated: v1 -->
# toolcalls.prune

Clear the ephemeral capture store (after it has been distilled/exported).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `(none).` |  |  |

## Returns

``{pruned: <rows removed>}``.

## Chain-next

terminal — the durable signal lives in the export artefact.

## Details

(no further detail)

## Example

```bash
agency-toolcalls-prune --intent-id $IID …
```
