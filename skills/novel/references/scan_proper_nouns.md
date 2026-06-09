<!-- agency-generated: v1 -->
# novel.scan_proper_nouns

Extract proper nouns (Title-Case words, sentence-starter words filtered) (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body.` |  |  |

## Returns

``{proper_nouns: [sorted unique], count}``.

## Chain-next

``novel.check_continuity`` (Slice 3+) for the cross-check.

## Details

Catches character + place names for continuity / world-bible cross-reference. Filters out common sentence-starter words ("The", "She", "Then", etc.) which would be Title-Case at position 1 of every sentence — a false-positive source.

## Example

```bash
agency-novel-scan_proper_nouns --intent-id $IID …
```
