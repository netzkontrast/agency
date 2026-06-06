<!-- agency-generated: v1 -->
# workspace.isolate

Create an isolated git worktree on a fresh branch off `base`; record the Workspace.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `branch (str — new branch name), base (str — default 'main').` |  |  |

## Returns

``{workspace, path, branch, base}`` on success; ``{error, branch, detail}`` on failure (wire shape).

## Chain-next

``workspace.baseline(workspace=, command=)`` to record the starting GREEN state.

## Details

(no further detail)

## Example

```bash
agency-workspace-isolate --intent-id $IID …
```
