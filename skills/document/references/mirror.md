<!-- agency-generated: v1 -->
# document.mirror

Project graph→file AND event-source it (Spec 292 — closes the loop).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (str — a render scope), apply_path (str — target .md), for_intent_id (str — render filter, as in ``render``).` |  |  |

## Returns

``{scope, document_id, revision_id, action, written, tokens}``.

## Chain-next

``document.ingest`` the file after a human edits it.

## Details

``render`` is a pure projection; ``mirror`` is its effect twin: it renders ``scope``, writes the markdown to ``apply_path`` with a stable anchor, and appends a **graph-sourced** ``DocRevision`` to the Document keyed by that file. This makes the graph→file direction event-sourced and symmetric with ``ingest`` (file→graph) — a rendered file and a later on-disk edit now coexist as keep-both revisions. Idempotent: re-mirroring identical content appends no new revision.

## Example

```bash
agency-document-mirror --intent-id $IID …
```
