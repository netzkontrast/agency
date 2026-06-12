<!-- agency-generated: v1 -->
# skills.rank

Rank walkable skills against a free-text query (Spec 161 Slice 1).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query (free text; empty = list all).` |  |  |

## Returns

``{candidates: [{name, kind, capability, phases, phase_count, score}], total, scorer}``.

## Chain-next

``skills.render`` the top candidate, then ``develop.skill_walk`` it.

## Details

Slice 1 is a deterministic keyword scorer: tokenize the query, normalise to lowercase, count substring hits across each skill's `name`, `capability`, `kind`, and phase names. Ties broken by `(capability, name)` for stability. Slice 2 swaps in an LLM ranker via the Spec 147 AnthropicDriver behind the same shape. An empty query falls through to the `find`-style listing (no ranking applied; same alphabetic sort).

## Example

```bash
agency-skills-rank --intent-id $IID …
```
