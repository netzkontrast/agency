<!-- agency-generated: v1 -->
# persona.recommend

Recommend the specialist persona(s) best matched to a ``task`` by decidable domain overlap (read-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `task (str — what you need a specialist for), top (int — how many).` |  |  |

## Returns

``{task, top, matches: [{persona, score, focus}]}``.

## Chain-next

persona.summon(top, task) to compose the dispatch brief.

## Details

(no further detail)

## Example

```bash
agency-persona-recommend --intent-id $IID …
```
