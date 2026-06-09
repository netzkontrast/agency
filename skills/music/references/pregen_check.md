<!-- agency-generated: v1 -->
# music.pregen_check

Computed `pre-generation` gate (CORE.md:57-62 — a MACHINE-checkable predicate, not the human ship-it confirm).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (the Lifecycle serving the intent), concept_ready, rights_clear (the computed predicate inputs).` |  |  |

## Returns

``{gate: "pre-generation", passed: True}`` on success; typed ``GATE_FAILED`` otherwise.

## Chain-next

on PASSED, proceed to generation; on fail, resolve the missing inputs then re-check.

## Details

(no further detail)

## Example

```bash
agency-music-pregen_check --intent-id $IID …
```
