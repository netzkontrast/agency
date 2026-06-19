<!-- agency-generated: v1 -->
# develop.maintain

Drive — and AUTOLEARN — the recurring "Agency Steward" maintenance loop.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `focus (optional steer for this run), record (persist the run node).` |  |  |

## Returns

``{run_id, phases, prior, signals, candidates, next_step}``.

## Chain-next

walk the phases; end with ``reflect.note`` + a handover, then ``branch.finish_branch`` to merge into main.

## Details

The maintenance discipline lives HERE as a verb, not in a fragile external prompt: each call returns the hardened phase plan + an evidence-grounded candidate shortlist COMPUTED from the live graph, and records a ``MaintenanceRun`` linked ``PRECEDES`` from the prior run — so the task learns across scheduled runs (the run chain + the reflection backlog are its memory). Reference it from the steward prompt: call ``develop.maintain`` at session start, follow the returned ``phases``, and the loop compounds. The candidate shortlist is derived, not snapshot (rule 8): the observation ``Reflection`` backlog (lessons to fold) + open Intents ranked by their live ``SERVES`` reach. The seven phases encode the steward discipline (orient → select → build → simplify → pillars → learn → ship).

## Example

```bash
agency-develop-maintain --intent-id $IID …
```
