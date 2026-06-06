<!-- agency-generated: v1 -->
# jules.review_comment

Compose an @jules PR review-comment with the mandatory handshake tail.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body (str — your review comment).` |  |  |

## Returns

``{text, tail_appended}``. ``text`` is what the caller passes to GitHub MCP ``add_issue_comment``; ``tail_appended=False`` means the body already carried a compliant tail.

## Chain-next

post ``text`` via the GitHub MCP comment tool.

## Details

The tail instructs Jules to ``reply_to_pr_comments(...)`` after pushing (AGENCY_PROTOCOL.md §9). Idempotent.

## Example

```bash
agency-jules-review_comment --intent-id $IID …
```
