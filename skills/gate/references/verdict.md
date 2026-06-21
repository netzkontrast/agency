<!-- agency-generated: v1 -->
# gate.verdict

Read the LATEST Gate by name and report its pass/block verdict — the reusable CI reader (Spec 382 §2, OQ2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (str — the gate name, e.g. "quality` |  | review"). |

## Returns

``{name, found, passed, blocked, evidence}``; an unknown name is ``found=False, blocked=False`` (nothing to block on).

## Chain-next

in CI, exit non-zero when ``blocked``; else proceed.

## Details

(no further detail)

## Example

```bash
agency-gate-verdict --intent-id $IID …
```
