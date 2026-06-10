<!-- agency-generated: v1 -->
# novel.integrate_scene_body

Spec 130 phase 5 — write the generated body back to the Scene (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, body (the prose body to commit).` |  |  |

## Returns

``{scene_id, artefact_id, bytes}``.

## Chain-next

terminal — the manuscript advances to the next scene.

## Details

The scene-writer skill's hard-gate integrate phase: promotes a draft body (from skill phase 3's generate output) onto the Scene node and records a ``scene-integration`` Artefact for provenance.

## Example

```bash
agency-novel-integrate_scene_body --intent-id $IID …
```
