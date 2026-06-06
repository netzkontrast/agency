<!-- agency-generated: v1 -->
# delegate.fan_out

Open one child Lifecycle per item (capped at `quota`), dispatch the driver for each, and record a Delegation that DELEGATES_TO every child.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `driver (capability name), driver_verb (str), items (list[dict] — each dict unpacked as driver kwargs), quota (int — admission cap).` |  |  |

## Returns

``{delegation, dispatched, skipped, children: [{lifecycle, result}]}`` (wire shape); ``{error, quota|offending}`` on validation fail.

## Chain-next

``delegate.join(delegation=)`` after children complete.

## Details

Children start ``working`` (dispatched ≠ done).

## Example

```bash
agency-delegate-fan_out --intent-id $IID …
```
