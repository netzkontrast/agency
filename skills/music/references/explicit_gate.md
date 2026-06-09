<!-- agency-generated: v1 -->
# music.explicit_gate

Computed explicit-content gate (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, lyrics, allow_explicit (default False).` |  |  |

## Returns

``{gate, passed, rating}`` or typed GATE_FAILED.

## Chain-next

rewrite explicit words OR re-call with allow_explicit=True if the release is intentionally explicit.

## Details

Passes iff rating ∈ {clean, suggestive} OR ``allow_explicit=True``. Records the rating on the gate's evidence so audit knows what was OK'd. Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

## Example

```bash
agency-music-explicit_gate --intent-id $IID …
```
