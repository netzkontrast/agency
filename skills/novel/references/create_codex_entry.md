<!-- agency-generated: v1 -->
# novel.create_codex_entry

Mint a CodexEntry + CODEX_OF edge to the Novel (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, slug, name, kind (one of CODEX_ENTRY_KIND), body (agent-facing description), triggers (comma-separated trigger phrases; defaults to ``name, slug`` if empty).` |  |  |

## Returns

``{entry_id, slug, name, kind}``.

## Chain-next

``novel.match_codex_entries`` to verify auto-injection.

## Details

(no further detail)

## Example

```bash
agency-novel-create_codex_entry --intent-id $IID …
```
