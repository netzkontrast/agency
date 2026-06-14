<!-- agency-generated: v1 -->
# novel.create_scene

Record a Scene node + SCENE_OF the parent Chapter (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id, slug (scene-local short name), pov (a ``SCENE_POV`` member or rich text projected onto one).` |  |  |

## Returns

``{scene_id, chapter_id, slug, pov, pov_detail?}``.

## Chain-next

``novel.create_scene`` for next beat or back to ``novel.set_chapter_status`` once the chapter's scene set is complete.

## Details

Spec 284 — ``pov`` is a *projected enum*: it accepts rich free text (e.g. ``"auktorialer Erzähler"``) and projects it onto a canonical ``SCENE_POV`` member, preserving the original in ``pov_detail`` (the non-lossy contract). Input carrying no POV signal still fails PERMANENT, listing the members.

## Example

```bash
agency-novel-create_scene --intent-id $IID …
```
