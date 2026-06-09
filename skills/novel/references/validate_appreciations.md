<!-- agency-generated: v1 -->
# novel.validate_appreciations

Hybrid check (row 12): NCP `appreciation` values ∈ canonical 463 set (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations: [{path, value}], canonical_size}``.

## Chain-next

``novel.validate_narrative_functions`` for row 13.

## Details

Walks every ``appreciation`` field across the NCP body recursively; each string must belong to the ``canonical_appreciation`` enum from the vendored NCP v1.3.0 schema (463 values).

## Example

```bash
agency-novel-validate_appreciations --intent-id $IID …
```
