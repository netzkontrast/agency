<!-- agency-generated: v1 -->
# analyze.migrate_quality_history

One-time importer: ``.brooks-lint-history.json`` → back-dated ``QualityRun`` nodes (Spec 385 §2).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `history_path (the legacy ``.brooks-lint-history.json``).` |  |  |

## Returns

{migrated, imported, skipped, run_ids} — or {migrated: False, reason} when the file is absent / not a JSON array.

## Chain-next

develop.review (its trend now spans the migration boundary).

## Details

Mints one ``QualityRun`` per record (Spec 381 §3) carrying the original ``recorded_at`` date; records are inserted oldest-first so the bi-temporal ``vfrom`` order matches the dates and the next ``analyze.record_run`` trend is CONTINUOUS across the migration boundary. IDEMPOTENT — a per-record content hash (``migrated_key``) skips an already-imported record, so a re-run never duplicates (keep-both, Spec 292).

## Example

```bash
agency-analyze-migrate_quality_history --intent-id $IID …
```
