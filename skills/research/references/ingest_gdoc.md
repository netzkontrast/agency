<!-- agency-generated: v1 -->
# research.ingest_gdoc

Compose a subagent dispatch contract that ingests a Google Doc to disk.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `source (URL or file_id), dest (str — default ``.agency/sources/gdoc-<id>.md``).` |  |  |

## Returns

``{action, prompt, tools, model, dest, file_id, after}`` OR ``{error: 'INVALID_SOURCE', source}``.

## Chain-next

orchestrator dispatches Agent tool with ``prompt``+``tools``; on return, calls ``after.verb`` with ``after.kwargs`` plus the subagent's structured return.

## Details

The verb performs NO I/O. It resolves ``source`` (URL or file_id) and returns a contract the orchestrator hands to the Agent tool: the subagent fetches via ``mcp__Google_Drive__*``, writes to ``dest``, and returns ONLY ``{path, bytes, lines, sha256, title}`` — the doc body never crosses back to main context. After the subagent returns, call ``research.record_ingested_source`` with the metadata to record the ``ingested-source`` Artefact (SERVES + PRODUCES edges).

## Example

```bash
agency-research-ingest_gdoc --intent-id $IID …
```
