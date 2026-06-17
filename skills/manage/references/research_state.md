<!-- agency-generated: v1 -->
# manage.research_state

RESEARCH-STATE — open research leads with their claims, citations and verification status, grouped (Spec 290, Memory pillar).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `domain (str — optional case-insensitive filter on a lead's question; scopes the children too), top (int — leads returned).` |  |  |

## Returns

``{domain, totals, leads: [{research_id, question, status, claims, citations, verifications}], pending}``.

## Chain-next

manage.read(research_id) for one lead's full props.

## Details

Composes the research sub-graph (`Research` · `ResearchClaim` · `Citation` · `Verification`) into one rollup. ``pending`` lists leads not yet ``ready``/``published`` — the verifications still owed.

## Example

```bash
agency-manage-research_state --intent-id $IID …
```
