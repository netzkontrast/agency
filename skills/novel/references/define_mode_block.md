<!-- agency-generated: v1 -->
# novel.define_mode_block

Mint a ``ModeBlock`` — a chapter span sharing a narrative stance (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, label (e.g. "Akt I — Heldinnenreise"), mode (linear-introspective|cyclic-recursive|linear-ascending| vortex-still|choral|framing), from_chapter, to_chapter, bridge_frequency_target (the Spec 136 soft-share target), genre_accent (the §11 per-act genre).` |  |  |

## Returns

``{mode_block_id, label, mode}``.

## Chain-next

``novel.assign_chapter_to_block`` per chapter; ``novel.mode_block_report``.

## Details

(no further detail)

## Example

```bash
agency-novel-define_mode_block --intent-id $IID …
```
