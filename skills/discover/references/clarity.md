<!-- agency-generated: v1 -->
# discover.clarity

Score a captured Intent's clarity / readiness (transform, read-only).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (the Intent to score; defaults to ``ctx.intent_id`` — named ``for_intent_id`` not ``intent_id`` to avoid colliding with the invoke serving-intent arg, per the document/dogfood convention).` |  |  |

## Returns

``{score (0.0-1.0), missing:[signal,...], ready (score>=threshold), signals:{name:bool}}``.

## Chain-next

resolve a ``missing`` signal (clarify/acceptance/ground/scope), then re-score.

## Details

The score is the normalized sum of five INDEPENDENT readiness signals, each computed from the live discovery graph (has-triple · acceptance- measurable · ambiguities-resolved · grounded · scope-bounded). Equal weights (the simplest monotone default, CLAUDE.md #8). Writes nothing beyond the Invocation — it reads existing discovery nodes/edges.

## Example

```bash
agency-discover-clarity --intent-id $IID …
```
