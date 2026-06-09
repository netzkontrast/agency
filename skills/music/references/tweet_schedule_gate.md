<!-- agency-generated: v1 -->
# music.tweet_schedule_gate

Computed tweet-schedule gate (effect) — composes 3 checks.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, body, scheduled_at, platform, max_length (default 280 = X/Twitter).` |  |  |

## Returns

``{gate, passed, evidence}`` or typed GATE_FAILED.

## Chain-next

on PASSED, ``music.db_create_tweet`` to persist.

## Details

Passes iff: body length ≤ max_length AND scheduled_at is a non-empty future-looking timestamp AND body is non-empty.

## Example

```bash
agency-music-tweet_schedule_gate --intent-id $IID …
```
