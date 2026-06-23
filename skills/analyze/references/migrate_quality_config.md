<!-- agency-generated: v1 -->
# analyze.migrate_quality_config

One-time importer: ``.brooks-lint.yaml`` → ``.agency/config.yaml quality:`` block + ``Suppression`` nodes (Spec 385 §1).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `config_path (the legacy ``.brooks-lint.yaml``).` |  |  |

## Returns

{migrated, quality, suppressions, written, source, source_preserved} — or {migrated: False, reason} when the legacy file is absent.

## Chain-next

analyze.migrate_quality_history, then verify + /plugin uninstall.

## Details

Maps the brooks config (disable/severity/ignore/focus/strictness/ custom_risks) onto the unified ``quality:`` block (Spec 381 §2), MERGING into ``.agency/config.yaml`` (never clobbering other sections); ``suppress`` entries become ``Suppression{risk, glob}`` nodes (Spec 381 §4, read by the score's ``apply_suppressions``). NON-DESTRUCTIVE — the ``.brooks-lint.yaml`` is left in place (keep-both, Spec 292); the 381 compat-read window is the safety net while this makes the migration durable.

## Example

```bash
agency-analyze-migrate_quality_config --intent-id $IID …
```
