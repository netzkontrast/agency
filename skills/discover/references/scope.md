<!-- agency-generated: v1 -->
# discover.scope

Elicit in-/out-of-scope boundaries (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (defaults to ``ctx.intent_id``); decisions (the folded {candidate_text|citation_id → "in"|"out"} map).` |  |  |

## Returns

``{in_scope:[...], out_of_scope:[...], open:[...], question}``.

## Chain-next

seed deferred sub-intents from ``out_of_scope`` via ``discover.decompose_intent`` (319).

## Details

Candidates are DERIVED from the Intent's ``GROUNDS`` citations (Spec 312) — never invented. ``scope`` composes ``discover.ask`` (310) to build ONE well-formed multiSelect question over the candidates (it never calls ``AskUserQuestion`` itself — 310 owns that contract). The caller folds the ``decisions`` ({candidate → "in"|"out"}); each decided candidate becomes a ``ScopeBoundary`` (``side ∈ {in,out}``) ``BOUNDS``-edged to the Intent, undecided ones stay ``open`` (no node).

## Example

```bash
agency-discover-scope --intent-id $IID …
```
