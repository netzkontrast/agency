<!-- agency-generated: v1 -->
# dogfood.boundary_use_audit

Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — filter to BoundaryUses serving this intent; "" = global). session_lifecycle_id (legacy alias; ignored when for_intent_id is set).` |  |  |

## Returns

``{intent_id, bypass_count, by_tool: {Write, Edit, Bash, …}, samples: [{tool, target, verb_shadow, argument_summary, session}], count}``.

## Chain-next

``dogfood.parse_amendment`` reads the bypass rate when the dogfood loop classifies amendments.

## Details

Reads BoundaryUse nodes (Spec 195 Slice 1: recorded by the engine's default hook handler when a raw Write/Edit/Bash fires under an active intent) and aggregates them into a typed audit report. Spec 195 invariants: - `bypass_count` is the sum of `by_tool` counts (no double-count). - When `for_intent_id` is given, only uses SERVING that intent are included (cross-intent contamination caught by the SERVES edge filter). - `samples` shows up to 5 representative records per tool (a paged audit reader can chain `dogfood.recall_overflow_slice` for the full set).

## Example

```bash
agency-dogfood-boundary_use_audit --intent-id $IID …
```
