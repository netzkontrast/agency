<!-- agency-generated: v1 -->
# novel.publish_ready_gate

Composite gate: contiguous chapters + status ≥ querying (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{passed, checks}`` or typed GATE_FAILED.

## Chain-next

``novel.set_novel_status('published')``.

## Details

Composes: manuscript_coherence_check (no chapter-number gaps) AND Novel.status ∈ {querying, published}. The publication-prep terminal gate before set_novel_status('published').

## Example

```bash
agency-novel-publish_ready_gate --intent-id $IID …
```
