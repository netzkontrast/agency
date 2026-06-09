<!-- agency-generated: v1 -->
# music.promo_gate

Promo-drafted gate — at least 1 promo asset exists (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album.` |  |  |

## Returns

``{gate, passed, asset_count}`` or typed GATE_FAILED.

## Chain-next

``music.publish_asset`` or ``music.upload_promo_video``.

## Details

Passes iff at least 1 published-asset is recorded for the album in the cloud store.

## Example

```bash
agency-music-promo_gate --intent-id $IID …
```
