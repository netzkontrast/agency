<!-- agency-generated: v1 -->
# analyze.graph

Query the provenance graph — a census of node types + a typed listing (read the graph).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_type (label to list, e.g. 'Reflection'/'Intent'; '' → census only); scope (filter Reflection/Event rows by their scope/name); limit (max rows).` |  |  |

## Returns

``{census: {label: count}, nodes: [...]}`` — the LIVE graph, not a snapshot.

## Chain-next

drill an intent via ``memory_graph_provenance``, or re-query a node_type.

## Details

The missing read surface: code-mode exposes only ``call_tool``, so the graph was queryable only one intent at a time via ``memory_graph_provenance``. This analyzes the graph itself — count every node label live, and list one label's rows (optionally filtered) — so "read the graph" is a first-class query.

## Example

```bash
agency-analyze-graph --intent-id $IID …
```
