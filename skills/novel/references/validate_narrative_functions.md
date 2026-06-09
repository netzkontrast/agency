<!-- agency-generated: v1 -->
# novel.validate_narrative_functions

Hybrid check (row 13): NCP `narrative_function` values ∈ canonical 144 set (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations: [{path, value}], canonical_size}``.

## Chain-next

``novel.check_throughline_partition`` for structural row 5.

## Details

Walks every ``narrative_function`` field; each string must belong to the ``canonical_narrative_function`` enum (144 values).

## Example

```bash
agency-novel-validate_narrative_functions --intent-id $IID …
```
