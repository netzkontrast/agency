<!-- agency-generated: v1 -->
# novel.record_character_learns

Mint a KnownFact + KNOWS + LEARNED_IN edges (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `character_id (any node id — Character ontology lands in Spec 123 Slice 2; for now any id works), fact (freeform), scene_id (existing Scene).` |  |  |

## Returns

``{fact_id, character_id, scene_id}``.

## Chain-next

``novel.what_does_X_know_as_of`` to verify.

## Details

(no further detail)

## Example

```bash
agency-novel-record_character_learns --intent-id $IID …
```
