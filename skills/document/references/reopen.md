<!-- agency-generated: v1 -->
# document.reopen

Reopen an archived session Document — reconstruct the four concepts (Spec 292 C4).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — an archived session .md).` |  |  |

## Returns

``{document_id, action, concepts}`` where concepts maps each of the four concept headings to its rendered section text.

## Chain-next

re-`session` to refresh, or diff against the live graph.

## Details

Closes the durability loop: ``session`` archives a Document to ``.agency/sessions/``; ``reopen`` ingests that file back (restoring the Document into the graph) and parses its ``## Intent / Capability / Lifecycle / Memory`` sections so the session is reconstructable, not ephemeral.

## Example

```bash
agency-document-reopen --intent-id $IID …
```
