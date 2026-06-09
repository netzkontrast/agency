<!-- agency-generated: v1 -->
# novel.check_show_dont_tell

Telling-verb scan — interior-monologue tells (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body.` |  |  |

## Returns

``{passed, tell_count, tells}``.

## Chain-next

rewrite tells into action / sensory detail.

## Details

Distinct from ``check_filter_words`` (which scans adverbs). Flags ``felt``/``realized``/``noticed``/etc. — verbs that NARRATE emotion instead of dramatizing it.

## Example

```bash
agency-novel-check_show_dont_tell --intent-id $IID …
```
