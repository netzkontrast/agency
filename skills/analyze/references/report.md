<!-- agency-generated: v1 -->
# analyze.report

Render the Iron-Law quality report from the ported templates + persist it as a round-trippable Document (Spec 384 close-out / 382 §4).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `findings (wire-shape finding dicts — risk_code/message/source/ consequence/remedy/tier), mode (review/audit/debt/test/health/sweep), scope (str), score (int — the Health Score, Spec 381), path (optional .md to write + stamp the anchor into; "" = graph-only Document).` |  |  |

## Returns

{report, content, mode, score, document_id, written}.

## Chain-next

document.sync(path) after a human edits the written report.

## Details

Adopts the Spec 384 templates: each finding renders via ``iron-law-finding.md`` and the report shell via ``quality-report.md`` (``ctx.render``); the audit-only Module Dependency Graph is gated by the template's ``<!-- BEGIN IF is_audit -->`` block — honoured programmatically here (the interim conditional processor; **Spec 388** ports the templates to Jinja for a real engine). The rendered report is recorded as a ``Document`` via ``document.emit`` (stable anchor + ``DocRevision``), so an on-disk edit round-trips via ``document.sync`` (Spec 292). Use when: producing + persisting the human-readable code-quality report.

## Example

```bash
agency-analyze-report --intent-id $IID …
```
