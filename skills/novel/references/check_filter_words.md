<!-- agency-generated: v1 -->
# novel.check_filter_words

Filter-word density check (transform, show-don't-tell).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body, threshold (default 0.05).` |  |  |

## Returns

``{passed, filter_count, total_words, density, offenders}``.

## Chain-next

``novel.set_chapter_status`` once density is in range.

## Details

Scans for canonical filter words (really / just / very / etc.). Density = filter-count / total-words; passes when ≤ threshold.

## Example

```bash
agency-novel-check_filter_words --intent-id $IID …
```
