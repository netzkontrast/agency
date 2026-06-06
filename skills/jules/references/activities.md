<!-- agency-generated: v1 -->
# jules.activities

A session's activity stream, trimmed to summaries (the costliest Jules read).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), page_size (int), only_kinds (comma-separated kinds), page_token (str — empty for newest page).` |  |  |

## Returns

``{activities: [{kind, summary, ts}], next_page_token}``.

## Chain-next

walk pages via ``next_page_token``; ``jules.plan`` / ``jules.patch`` for typed slices.

## Details

Without ``page_token`` older `agentMessaged` / failure details become unreachable (Codex review ccb8f03 / jules.py:139).

## Example

```bash
agency-jules-activities --intent-id $IID …
```
