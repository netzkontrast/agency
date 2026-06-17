<!-- agency-generated: v1 -->
# prompt.frameworks_for

Budget-aware candidate list for a known intent category (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `intent (str — one of recover/clarify/create/transform/reason/ critique/agentic), max_tokens (int — total budget).` |  |  |

## Returns

``{intent, frameworks: [{slug, name, complexity_tier, tokens}], total_tokens, truncated_at: int|None}``.

## Chain-next

``prompt.route_framework`` to pick ONE (305); or ``prompt.render(slug, fields)``.

## Details

Returns the user-facing frameworks whose ``intent_category`` matches ``intent``, in library order, accumulating template tokens until ``max_tokens`` binds (the shared ``budget_take`` truncation — 129 parity). Functional frameworks (``audience='functional'``, Spec 306) are held out — they are never user-prompt picks.

## Example

```bash
agency-prompt-frameworks_for --intent-id $IID …
```
