<!-- agency-generated: v1 -->
# novel.render_all

Re-materialise a novel's full markdown tree from graph ground truth (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{novel_id, count, rendered: [{path, entity_id, artefact_id}], wrote_disk}``.

## Chain-next

``novel.audit_novel_provenance`` to see the new Artefacts; or any editorial gate.

## Details

Spec 283 Slice 1 (Workstream F) — the on-demand full-rebuild path. Walks the novel `RenderSpec` (Novel → work.md, each Chapter → chapters/NN-slug.md), writes each file via the wired `render` driver (graph-only when none is wired — bare engines are unaffected), and mints ONE `Artefact{kind, path, entity_id, frontmatter_hash}` + `PRODUCES` edge per rendered entity. Closes the graph/disk provenance split (the evidence's 2-Artefacts-for-41-files drift): now #Artefacts == #files. Idempotent. Replaces the out-of-band `scripts/materialize_manuscript.py`.

## Example

```bash
agency-novel-render_all --intent-id $IID …
```
