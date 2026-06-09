<!-- agency-generated: v1 -->
# music.analyze_rhyme_scheme

Build a rhyme scheme (A/B/C labels) over the lyric lines (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics (multi-line text).` |  |  |

## Returns

``{scheme, groups, self_rhymes}`` via TextDriver.rhyme_scheme.

## Chain-next

``music.prosody_gate`` for an integrated prosody check.

## Details

(no further detail)

## Example

```bash
agency-music-analyze_rhyme_scheme --intent-id $IID …
```
