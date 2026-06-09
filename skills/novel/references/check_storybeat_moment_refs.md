<!-- agency-generated: v1 -->
# novel.check_storybeat_moment_refs

Decidable check (row 11): every moment.storybeat_ref resolves (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_slot_fill`` for row 4 audit.

## Details

Each `moments[*].storybeat_ref` must point to an existing `storybeats[*].id`. A dangling ref is a NCP-referential break.

## Example

```bash
agency-novel-check_storybeat_moment_refs --intent-id $IID …
```
