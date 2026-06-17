<!-- agency-generated: v1 -->
# manage.artefacts

ARTEFACTS produced under an intent + their source invocations (Spec 290, Memory pillar).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — the Intent id).` |  |  |

## Returns

``{intent_id, count, artefacts: [props]}``.

## Chain-next

manage.read(id) for one artefact's full state.

## Details

(no further detail)

## Example

```bash
agency-manage-artefacts --intent-id $IID …
```
