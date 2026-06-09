<!-- agency-generated: v1 -->
# music.release_check

Computed `release-qa` gate: every track mastered (read via the DBDriver).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (the Lifecycle serving the intent), album.` |  |  |

## Returns

``{album, gate: "release-qa", passed: True}`` on success; typed ``GATE_FAILED`` otherwise.

## Chain-next

on PASSED, ``music.publish_asset`` the release; on fail, master the blocking tracks then re-check.

## Details

(no further detail)

## Example

```bash
agency-music-release_check --intent-id $IID …
```
