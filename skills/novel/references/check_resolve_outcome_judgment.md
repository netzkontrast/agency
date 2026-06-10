<!-- agency-generated: v1 -->
# novel.check_resolve_outcome_judgment

Decidable check (row 7): resolve/outcome/judgment triple is legal.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `ncp (NCP v1.3.0 payload).` |  |  |

## Returns

``{passed, violations}``.

## Chain-next

``novel.check_approach_concern`` (row 8).

## Details

4 canonical Dramatica endings encode the legal triples: Triumph = (change, success, good) Tragedy = (steadfast, failure, bad) Personal Triumph= (steadfast, failure, good) Personal Tragedy= (change, success, bad) Other 4 combos are inconsistent (e.g. change+failure+good has the protagonist abandon their drive for a happy result — not a canonical Dramatica ending). Cap at the documented table.

## Example

```bash
agency-novel-check_resolve_outcome_judgment --intent-id $IID …
```
