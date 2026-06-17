<!-- agency-generated: v1 -->
# reflect.note

Write a scope-tagged insight node, edged OBSERVED_DURING + SERVES the intent.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (one of observation/project/reflection/technical/user/world), text (str — the insight body).` |  |  |

## Returns

``{result: <reflection_id>}``.

## Chain-next

``reflect.recall(scope=)`` or ``reflect.search(query=)`` to surface what was written.

## Details

(no further detail)

## Example

```bash
agency-reflect-note --intent-id $IID …
```
