<!-- agency-generated: v1 -->
# jules.apply_patch

Compute a recovery plan for a session's patch (verb mirror of `recover_apply_plan`).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), branch (optional — defaults ``recover-<session>``), base (str — default 'main'), owner/repo (optional).` |  |  |

## Returns

ordered list of ``{tool, args}`` ops the agent executes via GitHub MCP. NOT executed by this verb (planning vs. execution boundary; Spec 012 REVIEW must-fix #1).

## Chain-next

caller executes the ops via GitHub MCP in order.

## Details

Falls back to ``sourceContext.source`` for owner/repo when omitted.

## Example

```bash
agency-jules-apply_patch --intent-id $IID …
```
