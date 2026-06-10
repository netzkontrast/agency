<!-- agency-generated: v1 -->
# novel.check_continuity

Cross-chapter proper-noun continuity check (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, single_chapter: [{name, chapter}], close_pairs}``.

## Chain-next

``novel.copy_gate``.

## Details

Scans each chapter body for proper nouns; flags two patterns: (1) names appearing in exactly ONE chapter (likely typos or deleted characters), (2) close-distance spelling pairs (e.g. Lara/Laura — Levenshtein ≤ 2 + both ≥ 4 chars).

## Example

```bash
agency-novel-check_continuity --intent-id $IID …
```
