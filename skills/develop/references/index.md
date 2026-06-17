<!-- agency-generated: v1 -->
# develop.index

Index a repo as a token-cheap briefing — the development-workflow entry to the indexer (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str), apply (bool — write PROJECT_INDEX.md), max_tokens (int — budget; default 3000).` |  |  |

## Returns

``{index_id, content, tokens, files_scanned, writeup}``.

## Chain-next

read the briefing instead of re-scanning the tree.

## Details

Understanding a repo before working on it is a `develop` concern, so the 94%-reduction briefing is surfaced here. Delegates to ``document.index_repo`` (the rendering machinery + ``RepoIndex`` graph node stay in ``document``; this is the verb-level port, not a fork), so a single call records the index node AND, with ``apply``, writes ``PROJECT_INDEX.md``. Used by the SessionStart hook to keep the index fresh each session.

## Example

```bash
agency-develop-index --intent-id $IID …
```
