<!-- agency-generated: v1 -->
# novel.update_codex_entry

Edit a CodexEntry's body / triggers / name (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `entry_id; any of body / triggers / name (empty = unchanged).` |  |  |

## Returns

``{entry_id, fields_updated: [str]}``.

## Chain-next

``novel.list_codex_entries`` to verify.

## Details

(no further detail)

## Example

```bash
agency-novel-update_codex_entry --intent-id $IID …
```
