<!-- agency-generated: v1 -->
# adr.hints

HINTS — the payoff: at implementation start, project the spec's **approved** decisions (+ their depth-1 ``DEPENDS_ON`` neighbours) into a compact, token-BOUNDED architecture-hint block — *decisions and their consequences*, not the spec re-stated (the minimum an implementer needs to not contradict an approved decision).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (a Document id OR a frontmatter spec_id), budget (int — max tokens of returned hints).` |  |  |

## Returns

``{spec_id, themes, hints: [{decision_id, theme, decision, why, constraints, touches, related}], budget, returned_tokens, truncated}`` or ``{error}``.

## Chain-next

load the block into the implementer's context (workflow 358).

## Details

(no further detail)

## Example

```bash
agency-adr-hints --intent-id $IID …
```
