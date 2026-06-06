<!-- agency-generated: v1 -->
# reflect.recall_semantic

Semantic top-k recall over Reflection nodes; backend-injectable.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `query (str — free text; empty → empty results), k (int — max results), scope (str — optional post-rank filter).` |  |  |

## Returns

``{results: [{id, score, scope, text, vfrom}], embedder}``. ``text`` truncated to 200 chars (Spec 023 budget); call ``recall``/``search`` for full text. ``embedder`` names the live backend so callers confirm which ran.

## Chain-next

``reflect.recall(scope=)`` for full text on a top match.

## Details

(no further detail)

## Example

```bash
agency-reflect-recall_semantic --intent-id $IID …
```
