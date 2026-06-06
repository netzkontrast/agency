<!-- agency-generated: v1 -->
# dogfood.note

Record an observation Reflection tagged with plan_slug.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `observation (str — the body text), plan_slug (str — the Plan/NNN-slug directory name; used to scope render() queries).` |  |  |

## Returns

``{reflection_id, plan_slug}``.

## Chain-next

``dogfood.render(plan_slug)`` when humans need the DOGFOOD-NOTES.md projection.

## Details

(no further detail)

## Example

```bash
agency-dogfood-note --intent-id $IID …
```
