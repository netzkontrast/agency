<!-- agency-generated: v1 -->
# novel.check_alter_recognition

The "recognized, never labeled" discipline (transform): alters are identified by syntax + somatik + lexicon, never by headers or labels; clinical veil terms are forbidden before the reveal chapter.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id, veil_chapter (Akt-I veil boundary; default 13), veil_terms (csv of clinical terms under the veil).` |  |  |

## Returns

``{passed, violations: [{kind, pattern, reason}], checked_chapter, veil_active}``.

## Chain-next

rewrite flagged spans; re-run.

## Details

(no further detail)

## Example

```bash
agency-novel-check_alter_recognition --intent-id $IID …
```
