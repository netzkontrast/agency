<!-- agency-generated: v1 -->
# thinking.apply_full_review

Run the 8 founding methods in sequence; produce thinking-analysis artefact (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `subject (defaults to serving intent), depth (one of ANALYSIS_DEPTH; documents the rigor level).` |  |  |

## Returns

``{result, artefact}`` thinking-analysis artefact.

## Chain-next

``thinking.tradeoffs`` if multiple recommendations compete, OR commit + ``dogfood.record_decision``.

## Details

(no further detail)

## Example

```bash
agency-thinking-apply_full_review --intent-id $IID …
```
