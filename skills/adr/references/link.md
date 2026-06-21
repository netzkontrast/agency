<!-- agency-generated: v1 -->
# adr.link

LINK — add a typed SPEC-001-C dependency edge between two Decisions.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `source_id, dependency_type (one of DEPENDS_ON · RELATES_TO · REFINES · PART_OF), target_id, note (the DEP-004 rationale).` |  |  |

## Returns

``{linked: True, source_id, target_id, dependency_type}`` or ``{error, rule, linked: False}``.

## Chain-next

adr.impact(target_id) to see what now depends on it.

## Details

(no further detail)

## Example

```bash
agency-adr-link --intent-id $IID …
```
