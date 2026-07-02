<!-- agency-generated: v1 -->
# novel.add_alter

Add an alter to the system (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `system_id, name, category (anp|ep|special|mirror), layer (layer-1|layer-2|cross-layer), function (freeform — Fight / Freeze / Caregiver / …), taboo_rules (csv anti-cliché rules; read as HARD violations by Spec 134 check_pov_voice).` |  |  |

## Returns

``{alter_id, system_id, name, category, layer, function}``.

## Chain-next

``novel.record_alter_conflict`` for the matrix; ``novel.assign_voice_to_alter`` for the voice.

## Details

(no further detail)

## Example

```bash
agency-novel-add_alter --intent-id $IID …
```
