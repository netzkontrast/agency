<!-- agency-generated: v1 -->
# novel.record_storyform_transition

Record a Vortex — where one storyform overtakes another (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `storyform_set_id, from_role, to_role, at_chapter, kind (operative | ontological | synthesis).` |  |  |

## Returns

``{transition_id, from_role, to_role, at_chapter, kind}``.

## Chain-next

``novel.check_driver_transition_legality(transition_id)``.

## Details

(no further detail)

## Example

```bash
agency-novel-record_storyform_transition --intent-id $IID …
```
