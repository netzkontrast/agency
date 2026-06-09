<!-- agency-generated: v1 -->
# novel.manuscript_coherence_check

Chapter-sequence contiguity check (transform, driver-free).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, chapter_count, gaps}`` — gaps lists missing chapter numbers between 1 and the max present number.

## Chain-next

``novel.render_manuscript`` when contiguous.

## Details

(no further detail)

## Example

```bash
agency-novel-manuscript_coherence_check --intent-id $IID …
```
