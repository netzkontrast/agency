<!-- agency-generated: v1 -->
# prompt.fragments_for

Compose multiple fragments for a storyform scope (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (dict), max_tokens (int — total budget).` |  |  |

## Returns

``{fragments: [{slug, kind, text, tokens}], total_tokens, truncated_at: int|None, skipped_no_fragment: [slug]}``.

## Chain-next

feed ``fragments`` into the assembled brief (Spec 127 ``prompt.assemble_scene_brief``).

## Details

``scope`` describes a slice of a storyform — any of these keys contributes a fragment lookup (order matters; earlier = higher priority when budget binds): throughline → th.{mc|os|ic|rs} class_id → class.{universe|physics|mind|psychology} concern_id → type.{slug} problem_id → element/variation lookup solution_id → element/variation lookup crucial_element_id → element/variation lookup archetypes → list[arc.*]; included in order

## Example

```bash
agency-prompt-fragments_for --intent-id $IID …
```
