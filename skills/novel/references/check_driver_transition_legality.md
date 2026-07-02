<!-- agency-generated: v1 -->
# novel.check_driver_transition_legality

The KP driver rule (transform): a driver-flip WITHIN one storyform is illegal (Dramatica forbids it); only a storyform *transition* (e.g.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `transition_id.` |  |  |

## Returns

``{passed, from_driver, to_driver, same_storyform, verdict}``.

## Chain-next

``novel.dual_storyform_coherence_check``.

## Details

(no further detail)

## Example

```bash
agency-novel-check_driver_transition_legality --intent-id $IID …
```
