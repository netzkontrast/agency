<!-- agency-generated: v1 -->
# novel.record_lock

Mint a ``Lock`` — a canonized decision (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, topic, content (the locked statement, verbatim), source (originating doc/log), locked_on (ISO date; default today UTC), supersedes (optional earlier Lock id).` |  |  |

## Returns

``{lock_id, topic, locked_on, supersedes, supersedes_chain}``.

## Chain-next

``novel.lock_index(novel_id)`` — the Master-Index.

## Details

(no further detail)

## Example

```bash
agency-novel-record_lock --intent-id $IID …
```
