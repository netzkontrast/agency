<!-- agency-generated: v1 -->
# adr.impact

IMPACT — what ``DEPENDS_ON`` / ``REFINES`` / ``PART_OF`` this decision, to ``depth`` hops (SPEC-001-C ``adr impact``).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str), depth (int — transitive hops; ≥ 1).` |  |  |

## Returns

``{decision_id, depth, dependents: [{id, via, status, depth}], total}``.

## Chain-next

review each dependent before changing this decision.

## Details

(no further detail)

## Example

```bash
agency-adr-impact --intent-id $IID …
```
