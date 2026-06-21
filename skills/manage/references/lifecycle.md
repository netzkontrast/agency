<!-- agency-generated: v1 -->
# manage.lifecycle

LIFECYCLE READ — the Spec 341 `read` frame: one Lifecycle's full state rolled up in ONE call (state · phase · kind · serving intent · agent · gates), so the agent need not know which surface holds each piece.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (str).` |  |  |

## Returns

``{lifecycle_id, state, phase, kind, parameterization, intent_id, agent_id, gates}`` or ``{error}`` if absent / not a Lifecycle.

## Chain-next

manage.lifecycle_trail(lifecycle_id) for its transition history; gate.check(lifecycle_id, …) to gate it (the `check` frame).

## Details

(no further detail)

## Example

```bash
agency-manage-lifecycle --intent-id $IID …
```
