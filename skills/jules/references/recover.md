<!-- agency-generated: v1 -->
# jules.recover

Promote a session to the watcher's recovery-in-flight tracker.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), owner/repo/branch (optional plumb-throughs), base (str — default 'main').` |  |  |

## Returns

``{status: 'probing', session, attempts_planned: 3}`` IMMEDIATELY; outcome arrives later as a ``verify_pr`` / ``recover_apply_plan`` WatchEvent on the per-intent queue.

## Chain-next

``jules.watch(session=)`` to await the recovery outcome.

## Details

The probe-wait-recheck cycle (~5 min × 3 attempts per AGENCY_PROTOCOL §5) lives in the watcher's poll loop. Missing owner/repo/branch are derived from ``sourceContext.source`` at probe-exhaustion time.

## Example

```bash
agency-jules-recover --intent-id $IID …
```
