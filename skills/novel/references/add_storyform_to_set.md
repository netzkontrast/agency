<!-- agency-generated: v1 -->
# novel.add_storyform_to_set

Mint ``MEMBER_OF`` + stamp ``Storyform.role`` (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `storyform_id, set_id, role (primary | secondary | …).` |  |  |

## Returns

``{storyform_id, set_id, role, set_membership_count}``.

## Chain-next

``novel.check_klein_c_inversion(set_id)`` once both members are in.

## Details

(no further detail)

## Example

```bash
agency-novel-add_storyform_to_set --intent-id $IID …
```
