<!-- agency-generated: v1 -->
# dogfood.parse_amendment

Classify recent Reflections into amendment proposals.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (str — substring filter on plan_slug; "" = all), since (reserved; bi-temporal cursor in Slice 3), limit (int — caps the proposal list; default 20).` |  |  |

## Returns

``{proposals: [ProposalPayload]}``.

## Chain-next

``dogfood.apply_amendment(payload, dry_run=True)`` to render the proposed spec-edit as a unified diff.

## Details

Slice 1 ships the keyword classifier — the documented fallback path when the Spec 147 AnthropicDriver is unavailable (never silent no-op). Slice 2 swaps in the driver's structured-output classification (the same ProposalPayload shape, sharper recall).

## Example

```bash
agency-dogfood-parse_amendment --intent-id $IID …
```
