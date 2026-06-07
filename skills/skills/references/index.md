<!-- agency-generated: v1 -->
# skills.index

Promote walkable skills into the graph as Skill + Phase nodes (Spec 026).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{skills, phases}`` — counts of nodes written/updated.

## Chain-next

``analyze.graph`` (node_type='Skill') to read the promoted nodes.

## Details

Writes a `Skill` node per skill + a `Phase` node per phase (with `HAS_PHASE` edges), so skills are queryable like any other node via `analyze.graph`. Idempotent: deterministic node ids (`skill:<name>`, `phase:<name>:<index>`) make re-indexing an upsert, not a duplicate. (Auto-promotion at bootstrap is deferred — bootstrap is write-free today; this keeps promotion explicit.)

## Example

```bash
agency-skills-index --intent-id $IID …
```
