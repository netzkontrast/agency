<!-- agency-generated: v1 -->
# document.convergence

Audit a Document's convergence facets (Spec 292 C3).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `document_id (str).` |  |  |

## Returns

``{document_id, has_template, has_schema, has_clarity, has_four_concepts, is_defect, facets}``.

## Chain-next

bind a schema/template or re-ingest to clear a defect.

## Details

The Document is the artefact where the substrate converges. This audit reports which facets a Document carries — ``template``, ``schema`` (CONFORMS_TO), prompt ``clarity_score`` (on any revision), and four-concept session provenance (a `# Session —` render). A Document carrying NONE of these is a **defect** (``is_defect=True``).

## Example

```bash
agency-document-convergence --intent-id $IID …
```
