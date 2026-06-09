<!-- agency-generated: v1 -->
# music.promo_review

Rule-based scoring of promo copy quality (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body, platform.` |  |  |

## Returns

``{score, findings, max_length, platform}``.

## Chain-next

``music.promo_review_gate`` for an admissible threshold.

## Details

Scores body 0-100 on: length-in-window per platform, has-CTA (call to action), no-explicit-words.

## Example

```bash
agency-music-promo_review --intent-id $IID …
```
