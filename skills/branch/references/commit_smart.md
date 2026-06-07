<!-- agency-generated: v1 -->
# branch.commit_smart

Compose a conventional-commit message from a change summary + the changed paths (Spec 046 F-C — decidable, no LLM).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `summary (one-line description of the change); paths (comma-separated changed files — drives the inferred type + scope).` |  |  |

## Returns

``{message, type, scope}``.

## Chain-next

use the message for the commit; then ``branch.assess`` / ``finish``.

## Details

(no further detail)

## Example

```bash
agency-branch-commit_smart --intent-id $IID …
```
