<!-- agency-generated: v1 -->
# novel.create_character_system

Mint the host ``CharacterSystem`` (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, name (e.g. "Kael"), model (TSDP | OSDD | authored — documents the clinical frame).` |  |  |

## Returns

``{system_id, novel_id, name, model}``.

## Chain-next

``novel.add_alter`` per system member.

## Details

(no further detail)

## Example

```bash
agency-novel-create_character_system --intent-id $IID …
```
