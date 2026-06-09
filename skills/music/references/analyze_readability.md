<!-- agency-generated: v1 -->
# music.analyze_readability

Flesch-Kincaid-shaped readability over the lyric text (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `text_ (multi-line — `text` is a builtin so kw is suffixed).` |  |  |

## Returns

``{grade_level, avg_words_per_sentence, avg_syllables_per_word}``.

## Chain-next

pair with ``music.analyze_rhyme_scheme`` for a full prosody view.

## Details

(no further detail)

## Example

```bash
agency-music-analyze_readability --intent-id $IID …
```
