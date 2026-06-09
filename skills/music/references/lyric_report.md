<!-- agency-generated: v1 -->
# music.lyric_report

Analyze a lyric sheet's syllable load per line via the TextDriver (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, lyrics.` |  |  |

## Returns

``{result, artefact}`` where artefact.kind = ``lyric-report`` (PRODUCES edge).

## Chain-next

feed the report into the mix/master step.

## Details

(no further detail)

## Example

```bash
agency-music-lyric_report --intent-id $IID …
```
