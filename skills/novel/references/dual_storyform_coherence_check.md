<!-- agency-generated: v1 -->
# novel.dual_storyform_coherence_check

Composite (act): ``novel_coherence_check`` on EACH member + Klein-c inversion + legality of every recorded transition; records a ``dual-storyform-report`` Artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `storyform_set_id.` |  |  |

## Returns

``{passed, members, inversion, transitions, bridge, artefact_id}``.

## Chain-next

fix the listed non-inverted slots / illegal transitions.

## Details

(no further detail)

## Example

```bash
agency-novel-dual_storyform_coherence_check --intent-id $IID …
```
