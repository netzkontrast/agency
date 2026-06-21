<!-- agency-generated: v1 -->
# adr.draft

DRAFT — record a WH(Y) ``Decision`` (status ``proposed``) ``PART_OF`` the theme, SERVING the intent (SPEC-001-A).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `theme_id (str), decision (str — the chosen course; required), context/facing/neglected/benefits/tradeoffs (str — optional at draft), proposed_by (str).` |  |  |

## Returns

``{id, status, theme_id}`` or ``{error}`` on an ontology violation.

## Chain-next

adr.validate(id) to check the WHY rules; adr.approve (355).

## Details

(no further detail)

## Example

```bash
agency-adr-draft --intent-id $IID …
```
