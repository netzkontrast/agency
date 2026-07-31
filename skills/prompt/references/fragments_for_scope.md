<!-- agency-generated: v1 -->
# prompt.fragments_for_scope

Compose KP fragments for a drafting scope (transform; Spec 143).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scope (dict), max_tokens (total budget, ≤2000 default).` |  |  |

## Returns

``{fragments: [{slug, kind, text, tokens, family}], total_tokens, truncated_at, skipped_no_fragment}``.

## Chain-next

``prompt.compose_drafting_brief(scene_id)`` for the scene-level composition.

## Details

KP scope keys (all optional; earlier = higher priority when the budget binds): mode_block, genre_accent, audience_tier, routing_mode, transition_kind, predicate_kind, veil (maintain|leak-via-glitch| payoff), reveal_channels (list), alter_id (Alter node → category + function fragments), r_rule_ids (list — registered R-rule handles), family (whole-family pull), kp (bool opt-in).

## Example

```bash
agency-prompt-fragments_for_scope --intent-id $IID …
```
