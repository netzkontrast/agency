<!-- agency-generated: v1 -->
# novel.canon_gate

The drafting hard-stop (transform): refuse to treat a proposal/quarry/gap node as fact without an explicit author override — the KP "check the Master-Index first" rule, chainable from any drafting skill.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_id, allow (csv of acceptable statuses; default 'canonical'), override (author's explicit go-ahead).` |  |  |

## Returns

``{passed, status, advice}``.

## Chain-next

``novel.lock_index`` when blocked (consult, then decide).

## Details

(no further detail)

## Example

```bash
agency-novel-canon_gate --intent-id $IID …
```
