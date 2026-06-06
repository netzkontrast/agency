<!-- agency-generated: v1 -->
# dogfood.export

Dump the provenance store to a portable JSON file.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `path (str — destination; empty → ``.agency/export-<ns>.json`` with a nanosecond-precision timestamp to avoid path collisions between exports in the same second).` |  |  |

## Returns

``{path, nodes, edges, bytes}``.

## Chain-next

caller can rsync, commit, or replay the JSON.

## Details

Snapshot semantics: this export captures the FULL bi-temporal history (all nodes regardless of vto), not just the current-as-of-now snapshot. Replay against a fresh DB therefore reconstructs the entire append-only timeline — which is the right behaviour for merge-conflict recovery. Use case: merge-conflict recovery (Spec 020 line 69-73). When two branches both write to ``.agency/session.db`` and merge, the binary conflict can't be resolved. Recovery: export each branch's graph to JSON, then replay both JSONs against a fresh DB on the merged branch. The export is portable + diff-able (JSON is indent=2 + sort_keys=True). v1 scope: this verb ONLY emits the export. A matching ``dogfood.import`` verb that replays the JSON (preserving original node ids + vfrom/vto windows) is a v2 follow-up.

## Example

```bash
agency-dogfood-export --intent-id $IID …
```
