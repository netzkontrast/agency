<!-- agency-generated: v1 -->
# jules.list

Enumerate sessions (trimmed to id/state/title/url; one page — walk via token).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `page_size (int), page_token (str — empty = first page).` |  |  |

## Returns

``{sessions: [{id, state, title, url}], next_page_token}``.

## Chain-next

re-call with returned ``next_page_token`` to walk older pages.

## Details

(no further detail)

## Example

```bash
agency-jules-list --intent-id $IID …
```
