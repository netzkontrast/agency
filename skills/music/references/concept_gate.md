<!-- agency-generated: v1 -->
# music.concept_gate

Pre-generation gate: concept exists for the album (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id, album.` |  |  |

## Returns

``{gate, passed, evidence}`` or typed GATE_FAILED.

## Chain-next

``music.conceptualize`` if no concept yet.

## Details

Passes iff the album's slug resolves AND a concept artefact has been produced. The latter is a heuristic check on the graph (look for any Artefact with kind=album-concept SERVES the intent that opened the lifecycle).

## Example

```bash
agency-music-concept_gate --intent-id $IID …
```
