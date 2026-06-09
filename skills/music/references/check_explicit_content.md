<!-- agency-generated: v1 -->
# music.check_explicit_content

Classify lyrics as clean / suggestive / explicit (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lyrics.` |  |  |

## Returns

``{rating, explicit_words, suggestive_words}``.

## Chain-next

``music.explicit_gate``.

## Details

(no further detail)

## Example

```bash
agency-music-check_explicit_content --intent-id $IID …
```
