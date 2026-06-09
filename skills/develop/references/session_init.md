<!-- agency-generated: v1 -->
# develop.session_init

Mint a SessionLifecycle SERVING the intent; detect mode; suggest first verb.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `purpose, deliverable, acceptance (optional intent triple — if empty, uses the serving intent's existing fields), mode_hint (override the auto-detect).` |  |  |

## Returns

``{session_lifecycle_id, intent_id, mode, suggested_first_verb}``.

## Chain-next

``develop.session_check`` to read state OR ``develop.mode_select`` to switch.

## Details

The plugin's primary session-driver entry point (Spec 114 Pillar 1). Records a SessionLifecycle node tied to the serving intent + an initial mode (auto-detected from cwd state, or honoring ``mode_hint``). Mode-detection heuristics (cheap, deterministic): - cwd contains ``Plan/*/spec.md`` modified → ``spec-authoring`` - cwd contains ``agency/capabilities/*/*.py`` modified → ``coding`` - default → ``brainstorming``

## Example

```bash
agency-develop-session_init --intent-id $IID …
```
