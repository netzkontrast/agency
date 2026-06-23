<!-- agency-generated: v1 -->
# workflow.finish_spec

FINISH_SPEC — the owner-triggered done-cascade as ONE trigger (Spec 388). "This spec is done" bundled: move the spec to ``/done`` across ALL THREE state representations kept in sync (physical ``Plan/<state>/`` folder + ``state:`` frontmatter + the SpecLifecycle node — the agreement check-drift gates), APPROVE any ADR decisions the spec REFINES (owner authority — an agent never self-approves), and rebuild ``architecture.md``.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `spec_id (the spec number/id), approver (the human owner's identity — authorizes decision approval; '' skips it; 'agent' is rejected by the gate), root (the Plan dir), rebuild_architecture (rebuild ``architecture.md`` after — default True).` |  |  |

## Returns

``{spec_id, moved, from_state, folder, decisions_approved, node_synced, architecture_rebuilt}`` or ``{error}``.

## Chain-next

workflow.board to see the spec in /done; review the PR.

## Details

(no further detail)

## Example

```bash
agency-workflow-finish_spec --intent-id $IID …
```
