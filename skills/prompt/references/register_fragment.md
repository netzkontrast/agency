<!-- agency-generated: v1 -->
# prompt.register_fragment

Write a fragment to the project overlay (effect; runtime-extensible).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `slug (str — canonical or alias id), text (str — guidance body, ≤300 tokens recommended), overlay_path (str — defaults to ``.agency/dramatica-fragments-overlay.yaml``).` |  |  |

## Returns

``{slug, canonical_id, kind, tokens, overlay_path}`` OR ``{slug, error: 'UNKNOWN_SLUG'}``.

## Chain-next

``prompt.fragment(slug)`` to verify the round-trip.

## Details

(no further detail)

## Example

```bash
agency-prompt-register_fragment --intent-id $IID …
```
