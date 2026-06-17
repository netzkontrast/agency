<!-- agency-generated: v1 -->
# manage.project

PROJECT — a query-ranked, token-budgeted slice of a label's live nodes (Spec 290/293: the `project(query, budget)` read primitive, Goal 1).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `label (str — ontology label), query (str — optional relevance terms), budget (int — max tokens of returned rows).` |  |  |

## Returns

``{label, query, budget, total, returned, returned_tokens, truncated, rows}``.

## Chain-next

manage.read(id) for one row's full state.

## Details

Ranks live ``label`` nodes by overlap with ``query`` (most-relevant first; recency breaks ties), then returns the highest-priority prefix that fits under ``budget`` tokens — a bounded delta, never a raw dump (rule 2). Read-only; composes the shared ``budget_take`` split + the Spec 082 token counter. A budget smaller than the single highest-ranked row yields ``rows: []`` with ``truncated: True`` (the bounded-delta contract — the caller raises the budget or reads the row by id); it never partial-writes a node.

## Example

```bash
agency-manage-project --intent-id $IID …
```
