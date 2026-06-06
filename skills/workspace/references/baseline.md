<!-- agency-generated: v1 -->
# workspace.baseline

Run the baseline test command in the workspace and record the green/red result.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `workspace (Workspace node id), command (str — shell test cmd).` |  |  |

## Returns

``{workspace, passed, output}`` (wire shape); ``{error, workspace}`` on unknown workspace.

## Chain-next

caller proceeds with the work; later runs compare against this Baseline via ``BASELINED`` provenance.

## Details

(no further detail)

## Example

```bash
agency-workspace-baseline --intent-id $IID …
```
