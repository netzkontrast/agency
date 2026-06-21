<!-- agency-generated: v1 -->
# intent.triage

Triage a Finding — the intent's stance on it (Spec 381 §4).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `finding_id (str), action (dismiss|defer|accept|skip), reason (str), expires (str — epoch; defer defaults +90d).` |  |  |

## Returns

{action, finding_id, node_id, risk, pattern} (or {action: skip}).

## Chain-next

analyze.score / analyze.record_run — honoured on the next run.

## Details

- ``dismiss`` → records a ``Suppression{risk, pattern, reason}`` SERVING the intent + SUPPRESSES the Finding; the next scan drops a matching finding from the score (analyze reads it cross-capability). - ``defer`` → a Suppression with an expiry (default +90d); the finding resurfaces once expired. - ``accept`` → an ``Acknowledgement`` ACKNOWLEDGES the Finding ("known, won't fix" — queryable). - ``skip`` → no-op. ``risk`` + ``pattern`` are READ from the Finding node by ``finding_id`` (one source, no caller duplication). Keep-both: the Finding is never deleted; a Suppression only changes its tier on the scoring read (Spec 292).

## Example

```bash
agency-intent-triage --intent-id $IID …
```
