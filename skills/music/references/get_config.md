<!-- agency-generated: v1 -->
# music.get_config

Read the music capability's loaded config (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{config: dict}`` in the bitwize-compatible config shape.

## Chain-next

``music.create_album`` once artist + paths are confirmed.

## Details

Resolves from `.agency/music-config.yaml`, `~/.agency-music/config.yaml`, or `$AGENCY_MUSIC_HOME/config.yaml` per Spec 115 resolution order.

## Example

```bash
agency-music-get_config --intent-id $IID …
```
