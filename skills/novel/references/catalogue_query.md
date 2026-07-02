<!-- agency-generated: v1 -->
# novel.catalogue_query

Cross-work catalogue query (transform) — every scene across the author's novels reached by TRAVERSING the declared edges (Novel → CHAPTER_OF → SCENE_OF; Motif → ECHOES_IN), never a label scan with a Python foreign-key filter (the Spec 125 dormant-edge anti-pattern).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `author, motif (optional slug — scenes echoing it), canon_status (optional [K]/[V]/[S]/[L] filter), fields (csv projection of row keys), max_rows, cursor.` |  |  |

## Returns

``{prefix: {author_id, schema_version, capability_set_hash}, body: {query, rows, total, shown, edges_traversed, next_cursor}}``.

## Chain-next

re-call with ``cursor=next_cursor`` for the next page.

## Details

(no further detail)

## Example

```bash
agency-novel-catalogue_query --intent-id $IID …
```
