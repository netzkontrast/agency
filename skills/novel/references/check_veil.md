<!-- agency-generated: v1 -->
# novel.check_veil

The multiplicity-veil scan (transform): any scene/chapter body before ``hold_until_chapter`` containing a veil term is a breach.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, veil_term_set (csv), hold_until_chapter.` |  |  |

## Returns

``{passed, breaches: [{chapter, term, where}]}``.

## Chain-next

re-channel the leak into glitch/sensory, re-run.

## Details

(no further detail)

## Example

```bash
agency-novel-check_veil --intent-id $IID …
```
