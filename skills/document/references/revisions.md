<!-- agency-generated: v1 -->
# document.revisions

Read a Document's keep-both revision history (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `document_id (str).` |  |  |

## Returns

``{document_id, count, latest, history}``.

## Chain-next

``document.render`` to re-project, or diff sources.

## Details

Proves the bi-temporal keep-both contract: every ingest/render appends a revision; nothing is overwritten. ``latest`` is the newest by ``recorded_at``; ``history`` is latest-first.

## Example

```bash
agency-document-revisions --intent-id $IID …
```
