<!-- agency-generated: v1 -->
# novel.check_sensitivity

Sensitivity-topic advisory scan (transform, WARN-severity).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body.` |  |  |

## Returns

``{passed: True, warnings: [{category, term}]}``.

## Chain-next

``novel.developmental_gate`` (advisory only).

## Details

Extends content-warnings with a documented sensitivity lexicon covering mental-health, identity, and trauma-adjacent terms. Always passes — sensitivity is informational, not blocking (the spec's "exact-severity discipline" — advisory checks never gate). Emits ``warnings`` array for the editorial report.

## Example

```bash
agency-novel-check_sensitivity --intent-id $IID …
```
