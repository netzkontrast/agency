<!-- agency-generated: v1 -->
# novel.copy_gate

Composite gate: surface-level editorial readiness (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks, warnings}`` or typed GATE_FAILED.

## Chain-next

``novel.publish_ready_gate``.

## Details

Continuity (proper-noun registry) + content warnings DECLARED on the novel + readability in genre band (advisory). Continuity + content-warning declaration are blocking; readability emits warning only.

## Example

```bash
agency-novel-copy_gate --intent-id $IID …
```
