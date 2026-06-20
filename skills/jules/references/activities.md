<!-- agency-generated: v1 -->
# jules.activities

A session's activity stream.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), page_size (int), only_kinds (comma-separated kinds), page_token (str — empty for newest page), full (bool — False = {id,originator,kind,summary} preview; True = the complete raw activity, nothing dropped — CLAUDE.md #9).` |  |  |

## Returns

``{activities: [...], next_page_token}``.

## Chain-next

walk pages via ``next_page_token``; ``jules.plan`` / ``jules.patch`` for typed slices.

## Details

Without ``page_token`` older `agentMessaged` / failure details become unreachable (Codex review ccb8f03 / jules.py:139).

## Example

```bash
agency-jules-activities --intent-id $IID …
```
