<!-- agency-generated: v1 -->
# select.route

Route an ``operation`` to an approach archetype by decidable complexity scoring (Spec 296).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `operation (str — what is being done), file_count (int), speed_priority (bool — bias toward the fast pattern engine).` |  |  |

## Returns

``{operation, approach, score, confidence, rationale, fallback}``.

## Chain-next

execute via the chosen approach; fall back along the chain.

## Details

Computes a semantic-ness score in [0,1] from the operation's keywords, ``file_count``, and ``speed_priority``; direct mappings (memory/context) force ``semantic``. Thresholds: score >= 0.6 → semantic, <= 0.4 → pattern, else native. Records a ``Selection`` node SERVING the intent.

## Example

```bash
agency-select-route --intent-id $IID …
```
