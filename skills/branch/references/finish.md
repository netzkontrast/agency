<!-- agency-generated: v1 -->
# branch.finish

Finish the branch by the chosen action (merge/pr/keep/discard); record the outcome.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `branch (str), action (one of merge/pr/keep/discard), base (str).` |  |  |

## Returns

``{outcome, branch, action, ok, detail}`` (wire shape); ``{error, actions}`` on unknown action.

## Chain-next

terminal — outcome node carries the audit trail.

## Details

(no further detail)

## Example

```bash
agency-branch-finish --intent-id $IID …
```
