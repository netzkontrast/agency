<!-- agency-generated: v1 -->
# music.verify_streaming

Verify an album's streaming links are live via the CloudDriver (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `album, urls (comma-separated).` |  |  |

## Returns

``{album, live, dead, artefact}`` partitioning the URLs by HEAD-status.

## Chain-next

re-submit any dead links to the distributor.

## Details

Spec 097 Slice 2 (review-driven): produces a `streaming-verify` artefact — without this the ontology schema was dormant.

## Example

```bash
agency-music-verify_streaming --intent-id $IID …
```
