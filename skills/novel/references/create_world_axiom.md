<!-- agency-generated: v1 -->
# novel.create_world_axiom

Encode a WorldAxiom (rule) under a World (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `world_id, text (the rule body — concise), severity (one of ``WORLD_AXIOM_SEVERITY``` |  | hard | soft). |

## Returns

``{axiom_id, world_id, severity, text}``.

## Chain-next

``novel.find_axiom_contradictions`` after several land.

## Details

(no further detail)

## Example

```bash
agency-novel-create_world_axiom --intent-id $IID …
```
