<!-- agency-generated: v1 -->
# novel.pre_draft_gate

Composite gate: storyform + research + chapters present (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks}`` or typed GATE_FAILED.

## Chain-next

``novel.set_novel_status('drafting')`` once passed.

## Details

(no further detail)

## Example

```bash
agency-novel-pre_draft_gate --intent-id $IID …
```
