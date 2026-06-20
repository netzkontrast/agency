<!-- agency-generated: v1 -->
# discover.clarity_gate

Composite clarity gate — records outcome via gate.check (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (Lifecycle to gate on), override_token (optional bypass — deliberately confirm a below- threshold Intent; recorded in gate evidence), min_clarity (threshold, default CLARITY_THRESHOLD — overridable per CLAUDE.md rule 8 so tests can flip the gate).` |  |  |

## Returns

``{gate, passed, score, missing, override_used}`` or GATE_FAILED.

## Chain-next

on failure, resolve ``missing`` signals (clarify/acceptance/ ground/scope), re-score with ``clarity``, then re-gate.

## Details

Passes iff the serving Intent's clarity score >= min_clarity OR an explicit override_token is provided (the deliberate escape hatch, also recorded so the provenance moat shows the bypass). Returns GATE_FAILED when the score is too low and no override_token was given.

## Example

```bash
agency-discover-clarity_gate --intent-id $IID …
```
