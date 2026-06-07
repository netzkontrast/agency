<!-- agency-generated: v1 -->
# intent.suggests

Project the serving intent + the last verb's state to the next applicable skill (Spec 026 Part B — Intent owns the intent→skill projection; a RECOMMENDATION, not a dispatch).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `called_capability / called_verb / called_state (the last step's context); floor (min confidence, default 0.5). The serving intent is read ambiently from ``ctx.intent_id``.` |  |  |

## Returns

``{skill, mode, confidence, cue, matched_by}`` for the best match, or ``{skill: None, reason}`` when nothing clears the floor.

## Chain-next

``develop.skill_walk`` the recommended skill, or ``skills.render`` it.

## Details

Matcher kinds: ``pattern`` (regex over the context); ``verb_code`` (invoke a decider verb returning ``{matches, confidence}`` — cycle-checked against the verb in flight); ``llm_select`` is deferred (needs an LLM Driver, Spec 002).

## Example

```bash
agency-intent-suggests --intent-id $IID …
```
