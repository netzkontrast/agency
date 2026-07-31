<!-- agency-generated: v1 -->
# novel.resolve_canon_conflict

Apply the ONE conflict rule (transform): any canonical/proposal beats every quarry; among non-quarry the later ``source_date`` wins; exact ties return ``tied=True``.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `candidates ([{node_id, canon_status, source_date}]).` |  |  |

## Returns

``{winner, losers, reason}`` or ``{tied: True, candidates}``.

## Chain-next

``novel.set_canon_status`` on the loser(s) if demoting.

## Details

(no further detail)

## Example

```bash
agency-novel-resolve_canon_conflict --intent-id $IID …
```
