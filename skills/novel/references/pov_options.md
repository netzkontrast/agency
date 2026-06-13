<!-- agency-generated: v1 -->
# novel.pov_options

Structured POV choices for an assumption-gate (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `keys (the missing requires_input keys, comma-joined; advisory).` |  |  |

## Returns

``{options: [<SCENE_POV members>], keys}``.

## Chain-next

the walker presents ``options`` via an elicit gate.

## Details

Spec 285 Part B — the `resolve_via` target for the `scene-writer` skill's `requires_input` POV gate: a FastMCP-annotated verb in the novel capability that sources the canonical `SCENE_POV` members so the walker can elicit a CHOICE from the user instead of assuming a POV.

## Example

```bash
agency-novel-pov_options --intent-id $IID …
```
