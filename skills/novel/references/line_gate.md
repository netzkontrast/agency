<!-- agency-generated: v1 -->
# novel.line_gate

Composite gate: prose-level editorial readiness (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks, per_chapter}`` or typed GATE_FAILED.

## Chain-next

``novel.copy_gate`` once line edits are done.

## Details

Every chapter must pass filter-word density + show-don't-tell + dialogue attribution thresholds. POV consistency across scenes is required too. The exact-severity discipline: advisory (sensitivity) does NOT block; structural failures do.

## Example

```bash
agency-novel-line_gate --intent-id $IID …
```
