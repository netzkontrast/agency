<!-- agency-generated: v1 -->
# research.record_ingested_source

Record an ``ingested-source`` Artefact (SERVES intent + PRODUCES edge).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `source_url (str — gdoc URL), dest (str — path on disk), bytes/lines (int), sha256 (str — 64 hex), title (str).` |  |  |

## Returns

``{artefact_id, idempotent}`` OR ``{error: 'UNKNOWN_INTENT', intent_id}``.

## Chain-next

``analyze.graph`` to see the corpus; downstream readers open ``dest`` directly.

## Details

Idempotent on ``(intent_id, sha256)``: a re-fetch of the same doc body returns the existing artefact_id, so a re-run of an ingestion pipeline doesn't double-record.

## Example

```bash
agency-research-record_ingested_source --intent-id $IID …
```
