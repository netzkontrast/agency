<!-- agency-generated: v1 -->
# novel.list_codex_entries

List CodexEntries for a novel, optionally filtered by kind (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, kind (optional — one of CODEX_ENTRY_KIND).` |  |  |

## Returns

``{entries: [{entry_id, slug, name, kind, body}], count}``.

## Chain-next

``novel.match_codex_entries`` to scan a body.

## Details

(no further detail)

## Example

```bash
agency-novel-list_codex_entries --intent-id $IID …
```
