<!-- agency-generated: v1 -->
# music.update_streaming_url

Persist a verified streaming URL via StateDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, platform, url.` |  |  |

## Returns

``{album, platform, url, persisted}``.

## Chain-next

``music.get_streaming_urls`` to verify.

## Details

Caller invokes ``music.verify_streaming`` first if reachability matters; this verb only persists. Two-step idiom keeps the CloudDriver surface clean (Spec 097 §"CloudDriver method delta" — no new methods).

## Example

```bash
agency-music-update_streaming_url --intent-id $IID …
```
