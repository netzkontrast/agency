<!-- agency-generated: v1 -->
# dogfood.boundary_use_audit

Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session_lifecycle_id (optional; if given, filters to uses related to that session).` |  |  |

## Returns

``{uses: [{tool, argument_summary, suggested_verb}], count}``.

## Chain-next

walk the verbs surfaced in `suggested_verb` for the next session.

## Details

Reads all BoundaryUse nodes in the graph (recorded by Spec 076's unified hook layer when a raw Write/Edit/Bash fires) and lists each with a suggestion: did a capability verb exist for that boundary? The Spec 076 hook integration ships in Slice 2; this verb is the read-side that future-sessions will consult.

## Example

```bash
agency-dogfood-boundary_use_audit --intent-id $IID …
```
