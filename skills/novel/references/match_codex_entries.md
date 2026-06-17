<!-- agency-generated: v1 -->
# novel.match_codex_entries

Scan ``text`` for any registered codex trigger and return matches (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, text (the body to scan — chapter outline, scene draft, etc.).` |  |  |

## Returns

``{matches: [{entry_id, slug, name, kind, body, trigger_hit}]}``.

## Chain-next

feed matches to ``prompt.assemble_scene_brief``'s world_rules section.

## Details

Case-insensitive whole-substring match (the simpler half of the Novelcrafter behaviour; word-boundary matching is a Slice 2 refinement). Archived entries are skipped.

## Example

```bash
agency-novel-match_codex_entries --intent-id $IID …
```
