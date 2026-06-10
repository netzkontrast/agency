<!-- agency-generated: v1 -->
# novel.chapter_report_full

Full editorial dashboard for one chapter (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `chapter_id.` |  |  |

## Returns

``{chapter_id, checks: {...}, artefact_id}``.

## Chain-next

``novel.line_gate`` to roll up to a manuscript verdict.

## Details

Runs every prose check over the chapter's body and aggregates the verdicts; records a ``chapter-report`` Artefact + SERVES intent.

## Example

```bash
agency-novel-chapter_report_full --intent-id $IID …
```
