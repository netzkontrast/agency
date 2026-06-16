<!-- agency-generated: v1 -->
# document.render

Project graph state to markdown; deterministic.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (str — one of install-artefacts | reflections | provenance | capability-catalogue), for_intent_id (str — required for provenance, optional filter for reflections; named `for_intent_id` rather than `intent_id` because the substrate already injects intent_id for SERVES discipline), format (str — 'markdown' in v1).` |  |  |

## Returns

``{content, tokens, node_count, scope}``.

## Chain-next

caller writes to disk — and a disk edit round-trips back via ``document.ingest`` (graph↔file are peers now; Spec 292).

## Details

(no further detail)

## Example

```bash
agency-document-render --intent-id $IID …
```
