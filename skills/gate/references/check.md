<!-- agency-generated: v1 -->
# gate.check

Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON + an input-required pause on failure.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `lifecycle_id (str — the Lifecycle to gate), name (str — gate name), passed (bool — outcome), evidence (str — optional rationale).` |  |  |

## Returns

``{passed, gate}`` (wire shape); on a wrong-intent guard fail, ``{error, lifecycle_id}``.

## Chain-next

a failed gate flips the Lifecycle to ``input-required``; caller resumes by re-invoking the parent verb with ``confirmed=True`` (Hint #8).

## Details

Codex C2 (capability/gate.py:25): an exact ``i.id = $iid`` match rejected lifecycles serving a pre-amend intent — `memory.provenance` deliberately walks the ``SUPERSEDED_BY`` chain (memory.py:161-175), but this guard didn't. A gate against an amended intent would incorrectly report "lifecycle does not serve the current intent" and silently drop the gate outcome. Fix: query the whole ``SUPERSEDED_BY`` chain via ``memory._intent_chain``.

## Example

```bash
agency-gate-check --intent-id $IID …
```
