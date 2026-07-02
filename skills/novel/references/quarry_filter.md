<!-- agency-generated: v1 -->
# novel.quarry_filter

List the Steinbruch (transform): quarry-status nodes — deprecated material an author may still mine, never auto-canon.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, kind (optional node-kind filter).` |  |  |

## Returns

``{nodes: [{node_id, kind, name_or_slug, canon_status}], count}``.

## Chain-next

``novel.promote_from_quarry(node_id, source)``.

## Details

(no further detail)

## Example

```bash
agency-novel-quarry_filter --intent-id $IID …
```
