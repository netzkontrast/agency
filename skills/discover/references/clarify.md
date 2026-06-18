<!-- agency-generated: v1 -->
# discover.clarify

Resolve a draft Intent's ambiguities, folding each answer back (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (defaults to ``ctx.intent_id``); answers (the folded ``{ambiguity_kind → verbatim answer}`` map); max_rounds (budget).` |  |  |

## Returns

``{intent_id (latest revision), rounds:[{ambiguity_kind, score, question_id, answer, amended_to}], residual_ambiguity, exited_by: "below_threshold"|"max_rounds"}``.

## Chain-next

``discover.clarity`` re-scores; the confirm gate reads it.

## Details

Scores the Intent against the ambiguity-signals registry; for each unresolved ambiguity above threshold (highest first) composes ``discover.ask`` for a targeted question, folds the verbatim answer via ``intent.amend`` (bi-temporal supersede — the prior revision is kept), and records a ``CLARIFIES`` edge to the Intent's stable identity. Loops until residual ambiguity is below threshold or ``max_rounds`` is hit.

## Example

```bash
agency-discover-clarify --intent-id $IID …
```
