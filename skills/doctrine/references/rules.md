<!-- agency-generated: v1 -->
# doctrine.rules

The behavioral rules, optionally filtered by priority (Spec 303).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `priority (str — '' for all, or critical|important|recommended).` |  |  |

## Returns

``{count, priority, rules: [{rule, priority, category, statement, triggers}]}``.

## Chain-next

doctrine.resolve(a, b) when two rules conflict.

## Details

(no further detail)

## Example

```bash
agency-doctrine-rules --intent-id $IID …
```
