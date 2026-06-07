<!-- agency-generated: v1 -->
# skills.find

Enumerate the walkable skills across all capabilities, with light filters.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `kind (filter by skill kind, e.g. 'usage'/'discipline'; '' = any); capability (filter by owning capability; '' = any).` |  |  |

## Returns

``{candidates: [{name, kind, capability, phases, phase_count}], total}``.

## Chain-next

``skills.render`` one candidate, or ``develop.skill_walk`` to walk it. The intent→next-skill projection lives on ``intent.suggests`` (Spec 026 B).

## Details

(no further detail)

## Example

```bash
agency-skills-find --intent-id $IID …
```
