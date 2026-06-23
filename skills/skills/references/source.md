<!-- agency-generated: v1 -->
# skills.source

Read WHERE a capability's v2 skill data comes from (Spec 371 Slice 3).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `capability (the registry capability name, e.g. 'develop').` |  |  |

## Returns

``{name, owner, source, source_stamp}`` — ``source`` ∈ derived|authored, ``owner`` ∈ auto|capability (A6).

## Chain-next

``skills.render`` to read the skill, or author a ``<cap>/skill.yaml`` to override the derived default.

## Details

A capability's skill DERIVES from its module docstring (rule 2) unless it SHIPS a ``<cap>/skill.yaml`` (the A6 authored override). This reads back that provenance without re-deriving the whole Skill.

## Example

```bash
agency-skills-source --intent-id $IID …
```
