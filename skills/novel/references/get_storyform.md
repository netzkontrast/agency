<!-- agency-generated: v1 -->
# novel.get_storyform

Return a novel's Storyform node + parsed NCP body (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id (parent Novel).` |  |  |

## Returns

``{storyform_id, novel_id, body}`` (``body`` is the parsed NCP dict, or ``{}`` when unset); ``found=False`` when the novel has no Storyform yet.

## Chain-next

feed ``body`` into ``novel.novel_coherence_check`` or any decidable ``check_*`` verb.

## Details

(no further detail)

## Example

```bash
agency-novel-get_storyform --intent-id $IID …
```
