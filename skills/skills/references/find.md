<!-- agency-generated: v1 -->
# skills.find

Enumerate the skills across all capabilities — walkable disciplines AND the concept pillars (Spec 375) — with light filters.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `kind (filter by skill kind, e.g. 'usage'/'discipline'/'pillar'; '' = any); capability (filter by owning capability, '(pillar)' for the concept pillars; '' = any).` |  |  |

## Returns

``{candidates: [{name, kind, capability, phases, phase_count}], total}``.

## Chain-next

``skills.render`` one candidate, or ``develop.skill_walk`` to walk it (a pillar has 0 phases — read its concept skill rather than walking). The intent→next-skill projection lives on ``intent.suggests`` (Spec 026 B).

## Details

(no further detail)

## Example

```bash
agency-skills-find --intent-id $IID …
```
