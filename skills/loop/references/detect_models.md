<!-- agency-generated: v1 -->
# loop.detect_models

Probe the model allowlist by PATH — metadata only, never secrets (369).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `store_path (str — optional config path to persist the available set).` |  |  |

## Returns

``{models, available}``.

## Chain-next

loop.register_model(...) to add a custom model.

## Details

(no further detail)

## Example

```bash
agency-loop-detect_models --intent-id $IID …
```
