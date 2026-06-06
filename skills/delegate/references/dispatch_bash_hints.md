<!-- agency-generated: v1 -->
# delegate.dispatch_bash_hints

Compose the bash-hint context block for a dispatch prompt.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `paths (comma-separated dirs/globs), symbols (comma-separated grep terms). Both empty → empty hints.` |  |  |

## Returns

``{hints: [str], block: str}`` where ``block`` is the ready-to-paste markdown.

## Chain-next

paste ``block`` into the dispatched agent's prompt.

## Details

When the orchestrator decides to dispatch (per ``dispatch_decision``), hand the agent the exact bash commands that surface the right files — cheap on orchestrator tokens, fast for the agent.

## Example

```bash
agency-delegate-dispatch_bash_hints --intent-id $IID …
```
