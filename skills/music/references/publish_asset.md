<!-- agency-generated: v1 -->
# music.publish_asset

Publish an album asset to object storage via the CloudDriver (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, key, body.` |  |  |

## Returns

``{key, bytes}`` on success.

## Chain-next

``music.verify_streaming`` once distributor links propagate.

## Details

Returns ``DEPENDENCY_MISSING`` (typed) when the cloud backend is unconfigured — never a stringly-typed raise.

## Example

```bash
agency-music-publish_asset --intent-id $IID …
```
