<!-- agency-generated: v1 -->
# novel.archive_codex_entry

Flag a CodexEntry as archived (effect, soft-delete).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `entry_id, reason (optional — recorded in `archived_reason`).` |  |  |

## Returns

``{entry_id, archived: True}``.

## Chain-next

``novel.list_codex_entries`` to verify the prune.

## Details

Archived entries are skipped by ``match_codex_entries`` and ``list_codex_entries``. They remain in the graph for provenance.

## Example

```bash
agency-novel-archive_codex_entry --intent-id $IID …
```
