<!-- agency-generated: v1 -->
# document.sync

Ingest every CHANGED markdown file under ``path`` (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — file or directory), audit (bool).` |  |  |

## Returns

``{root, ingested: [...], skipped: [...]}``.

## Chain-next

commit the round-tripped graph state.

## Details

The batch, idempotent entry point — the hook target for the ``document.sync`` pre-commit step (verb-now, hook-later). A file path ingests that one file; a directory walks ``**/*.md``. Unchanged files (``action == 'unchanged'``) are skipped.

## Example

```bash
agency-document-sync --intent-id $IID …
```
