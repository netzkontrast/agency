<!-- agency-generated: v1 -->
# gate.adjudicate

Adjudicate two CONFLICTING concerns at a decision point by consulting ``doctrine.resolve`` — the priority-hierarchy winner (safety > correctness > maintainability > speed), recorded as a Gate (Spec 303).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `a (str — one concern), b (str — the conflicting concern), lifecycle_id (str — optional Lifecycle to edge the verdict onto).` |  |  |

## Returns

``{result: {winner, winner_category, loser, tie, rationale, gate}}``.

## Chain-next

proceed with the winning concern; doctrine.cite it.

## Details

This is doctrine's real consumer: rather than guessing which concern wins a tradeoff, the gate delegates to the doctrine capability (recording a ``doctrine.resolve`` Invocation that SERVES the intent) and persists the verdict as auditable Gate provenance.

## Example

```bash
agency-gate-adjudicate --intent-id $IID …
```
