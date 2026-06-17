<!-- agency-generated: v1 -->
# document.ingest

Round-trip a markdown file INTO the graph (file → graph; Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — the .md file), audit (bool — prompt-audit the body), template (str — generator binding), schema (str — schema binding).` |  |  |

## Returns

``{document_id, revision_id, action, content_sha, anchored, clarity_score, path}``. action ∈ created | revised | unchanged.

## Chain-next

``document.revisions`` to read the keep-both history.

## Details

Inverts the old premise (files were a one-way rendered view): an edited markdown file is now an editable PEER that flows back into the graph as an append-only ``DocRevision``. Keep-both, bi-temporal: the prior (graph- or file-authored) version is retained; latest wins on read. An un-anchored file mints a ``Document`` and the stable ``<!-- agency-node: … -->`` anchor is written back. Every file is also a prompt — the body is scored via ``prompt.audit`` (``audit=True``). ``template`` / ``schema`` bind the other substrate layers onto the Document (convergence artefact).

## Example

```bash
agency-document-ingest --intent-id $IID …
```
