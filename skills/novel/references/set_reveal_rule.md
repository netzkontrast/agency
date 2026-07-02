<!-- agency-generated: v1 -->
# novel.set_reveal_rule

Mint/update a ``RevealRule`` — upsert keyed by (novel, fact, tier) (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, fact (freeform or a node-ref), tier (reader|pov|antagonist), may_know_from_chapter, must_not_before (0 = use may_know_from_chapter as the floor), channel (glitch|log|sensory|dialogue|metaphor|narration), rationale, fact_node_id (when the fact IS a node).` |  |  |

## Returns

``{rule_id, tier, may_know_from_chapter, was_update}``.

## Chain-next

``novel.check_reveal_timing(scene_id, fact)`` while drafting; ``novel.reveal_timeline_report``.

## Details

(no further detail)

## Example

```bash
agency-novel-set_reveal_rule --intent-id $IID …
```
