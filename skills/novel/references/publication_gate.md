<!-- agency-generated: v1 -->
# novel.publication_gate

Terminal composite: publish_ready + ≥1 export + front-matter declared (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks, exports: [{format, path}]}`` or typed GATE_FAILED.

## Chain-next

terminal — call ``novel.set_novel_status('published')``.

## Details

Composes: - ``publish_ready_gate`` (chapters contiguous + status ≥ querying) - at least one ``published-manuscript`` Artefact already exists (caller has run ``export_epub`` / ``export_pdf`` / ``export_docx``) - novel front-matter declares ``content_warnings`` (empty string OK, but the field MUST be set so reviewers see a deliberate state).

## Example

```bash
agency-novel-publication_gate --intent-id $IID …
```
