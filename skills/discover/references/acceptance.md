<!-- agency-generated: v1 -->
# discover.acceptance

Derive testable, Gherkin-shaped acceptance criteria from the Intent (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (the Intent to derive for; defaults to ``ctx.intent_id``).` |  |  |

## Returns

``{criteria:[{id,text,gherkin,measurable,flagged,source}], acceptance, coverage:{deliverable_parts, covered, gaps}}``.

## Chain-next

fold ``acceptance`` into the Intent via ``intent.amend`` / ``discover.refine`` (320); ``discover.clarity`` then re-scores.

## Details

Splits the Intent's ``deliverable`` into checkable sub-parts and derives one criterion per part — a ``text`` statement, a Given/When/Then ``gherkin`` triple, and a ``measurable`` bool. Unmeasurable criteria are FLAGGED, never dropped. Mints each as an ``AcceptanceCriterion`` ``VALIDATES``-edged to the Intent; does NOT overwrite the Intent's ``acceptance`` field (the caller folds it).

## Example

```bash
agency-discover-acceptance --intent-id $IID …
```
