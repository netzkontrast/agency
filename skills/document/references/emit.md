<!-- agency-generated: v1 -->
# document.emit

Persist ARBITRARY rendered content as a round-trippable Document (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `content (the rendered markdown), path (optional target .md to write + stamp the anchor into).` |  |  |

## Returns

``{document_id, revision_id, written, action}``.

## Chain-next

``document.sync(path)`` after a human edits the written file.

## Details

The general twin of ``mirror`` (which renders a fixed graph SCOPE): a capability that has ALREADY rendered a template — e.g. ``analyze.report`` rendering ``quality-report.md`` — calls this to record the result as a ``Document`` keyed by a stable anchor + a graph-sourced ``DocRevision``, so an on-disk edit round-trips via ``document.sync``. With ``path=""`` the Document is graph-only (no file write), keyed ``render:<sha>``; with a path the content is written and the anchor stamped. Idempotent on content sha.

## Example

```bash
agency-document-emit --intent-id $IID …
```
