<!-- agency-generated: v1 -->
# develop.record_authoring_outcome

Record a Reflection at the end of an authoring-capabilities walk.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name (capability name authored), kind (scaffold kind).` |  |  |

## Returns

{result: <reflection_id>}.

## Chain-next

(terminal — discipline closes here).

## Details

The authoring-capabilities discipline's phase 6 (hard gate) is the commit boundary; the caller confirms then invokes this verb to write a `Reflection{scope:"observation"}` SERVING the calling intent. The observation surfaces back into future authoring walks (the self-improvement loop closes when Spec 014 promotes them to spec amendments).

## Example

```bash
agency-develop-record_authoring_outcome --intent-id $IID …
```
