<!-- agency-generated: v1 -->
# music.pregen_check

Computed `pre-generation` gate — machine-checkable predicate (Spec 094).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (the Lifecycle serving the intent), concept_ready, rights_clear (the computed predicate inputs).` |  |  |

## Returns

``{gate: "pre-generation", passed: True}`` on success; typed ``GATE_FAILED`` otherwise.

## Chain-next

on PASSED, proceed to generation; on fail, resolve the missing inputs then re-check.

## Details

Not the human ship-it confirm — that stays on an `elicit`/`lifecycle_gate`. Passes only when the concept is complete AND rights are cleared; a fail records BLOCKED_ON + flips the lifecycle to ``input-required`` via ``gate.check`` and returns a typed ``GATE_FAILED``. The terminal human "ready?" stays an ``elicit``/``lifecycle_gate``.

## Example

```bash
agency-music-pregen_check --intent-id $IID …
```
