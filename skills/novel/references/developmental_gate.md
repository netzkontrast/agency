<!-- agency-generated: v1 -->
# novel.developmental_gate

Composite gate: structure-level editorial readiness (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks}`` or typed GATE_FAILED.

## Chain-next

``novel.line_gate`` once developmental edits are done.

## Details

Combines storyform coherence + chapter contiguity + at-least-one outlined chapter. Mirrors music's lyric-gate composition pattern.

## Example

```bash
agency-novel-developmental_gate --intent-id $IID …
```
