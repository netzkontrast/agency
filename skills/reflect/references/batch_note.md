<!-- agency-generated: v1 -->
# reflect.batch_note

Bulk version of ``note``: one Reflection node per text.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (one of observation/project/reflection/technical/user/world), texts (list[str] — one Reflection per non-empty entry).` |  |  |

## Returns

``{ids, count}``.

## Chain-next

``reflect.recall(scope=)`` for surfacing the batch.

## Details

Closes the gap that made ``jules-self-improvement`` only fold the first observation per walk — a real loop ingests N observations from ``dogfood.collect`` in one Phase-2 invocation.

## Example

```bash
agency-reflect-batch_note --intent-id $IID …
```
