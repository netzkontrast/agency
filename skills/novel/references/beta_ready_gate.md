<!-- agency-generated: v1 -->
# novel.beta_ready_gate

Composite gate: all chapters drafted+ (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks}`` or typed GATE_FAILED.

## Chain-next

``novel.set_novel_status('beta')`` then ship to readers.

## Details

Passes IFF every Chapter for the Novel has status ∈ {drafted, revised, final}. Outlined chapters block.

## Example

```bash
agency-novel-beta_ready_gate --intent-id $IID …
```
