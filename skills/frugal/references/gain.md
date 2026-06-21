<!-- agency-generated: v1 -->
# frugal.gain

The frugal impact scoreboard — the published benchmark medians (a documented external constant sourced from ``data/benchmark.json``, the CLAUDE.md #8 exception, NOT a frozen snapshot) PLUS the LIVE per-repo marker count (a read-only scan — the only honest per-repo number; never an invented savings figure, since the unbuilt version was never written).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `paths (str — optional scope for the live count; empty = all tracked source).` |  |  |

## Returns

``{benchmark, this_repo: {markers, computable, use, note}}``.

## Chain-next

``frugal.debt`` for the full queryable ledger; ``frugal.instructions``.

## Details

(no further detail)

## Example

```bash
agency-frugal-gain --intent-id $IID …
```
