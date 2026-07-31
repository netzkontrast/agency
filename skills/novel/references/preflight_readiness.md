<!-- agency-generated: v1 -->
# novel.preflight_readiness

Preflight readiness for a novel (transform) — per registered audit phase, is its graph substrate present (Spec 255 × Spec 170)?

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id.` |  |  |

## Returns

``{phases: [{phase, wired, missing_labels}], wired, total, readiness}``.

## Chain-next

seed the missing substrate (e.g. ``set_reveal_rule``, ``register_project_rule``), then ``preflight_report``.

## Details

(no further detail)

## Example

```bash
agency-novel-preflight_readiness --intent-id $IID …
```
