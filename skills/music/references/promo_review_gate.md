<!-- agency-generated: v1 -->
# music.promo_review_gate

Computed promo-review gate (effect) — composes ``promo_review`` scoring.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, body, platform, min_score (default 70).` |  |  |

## Returns

``{gate, passed, score, findings}`` or typed GATE_FAILED.

## Chain-next

on failure, revise the copy + re-call ``promo_review_gate``.

## Details

Passes iff ``promo_review.score >= min_score``. Records the score on gate evidence so audit knows the threshold + actual.

## Example

```bash
agency-music-promo_review_gate --intent-id $IID …
```
