<!-- agency-generated: v1 -->
# novel.query_ready_gate

Composite gate: status ≥ beta + content-clean (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks}`` or typed GATE_FAILED.

## Chain-next

``novel.render_query_letter`` then agent submission.

## Details

Composes: Novel.status reaches {beta, querying, published} AND aggregate chapter body passes check_content_warnings (empty warnings list).

## Example

```bash
agency-novel-query_ready_gate --intent-id $IID …
```
