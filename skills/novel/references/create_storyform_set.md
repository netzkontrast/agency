<!-- agency-generated: v1 -->
# novel.create_storyform_set

Mint a ``StoryformSet`` grouping N simultaneous storyforms (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, label, count (default 2).` |  |  |

## Returns

``{set_id, label, count}``.

## Chain-next

``novel.add_storyform_to_set`` per member storyform.

## Details

(no further detail)

## Example

```bash
agency-novel-create_storyform_set --intent-id $IID …
```
