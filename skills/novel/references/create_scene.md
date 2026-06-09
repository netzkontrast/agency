<!-- agency-generated: v1 -->
# novel.create_scene

Record a Scene node + SCENE_OF the parent Chapter (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id, slug (scene-local short name), pov (one of ``SCENE_POV``).` |  |  |

## Returns

``{scene_id, chapter_id, slug, pov}``.

## Chain-next

``novel.create_scene`` for next beat or back to ``novel.set_chapter_status`` once the chapter's scene set is complete.

## Details

(no further detail)

## Example

```bash
agency-novel-create_scene --intent-id $IID …
```
