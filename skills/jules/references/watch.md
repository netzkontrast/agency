<!-- agency-generated: v1 -->
# jules.watch

Await the next `WatchEvent` for a session or intent.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid — looks up the watching intent), for_intent (intent_id — explicit override), timeout (int — seconds, capped at 25).` |  |  |

## Returns

``{action, session, state, instruction, evidence, _for_intent}`` on a real event; ``{action: 'noop', instruction: 'Working.', evidence: {}, _for_intent}`` on heartbeat.

## Chain-next

dispatch action-specific verb (e.g. ``jules.approve_plan``, ``jules.recover``, ``jules.verify``).

## Details

Caller supplies EITHER ``session`` (sid; resolves the watching intent via the `JulesSession SERVES Intent` edge) OR ``for_intent`` directly. ``for_intent`` is named distinctly from the engine's auto-injected ``intent_id`` (which always points to the *calling* intent). Returns the next event from the per-intent queue, OR a heartbeat noop after ``min(timeout, 25)`` seconds — so client stdio stays alive even when no transition fires (Spec 012 Refinement Notes must-fix #5). Returns ``{action, session, state, instruction, evidence}`` for a real event, or ``{action: "noop", instruction: "Working.", evidence: {}}`` for the heartbeat. The watcher's poll loop ALSO emits noop heartbeats every 20s; this verb's heartbeat is the client-facing fallback if the queue is otherwise empty. Sync wrapper around the async queue: drains any pending event via ``get_nowait``, else polls 10×/sec for up to ``min(timeout, 25)``s. **Intent semantics** — the *calling intent* (auto-injected as ``intent_id``) wraps THIS verb call in code-mode; the *watching intent* is the one that originated the dispatch (recorded on the ``JulesSession``'s ``SERVES`` edge). They are often the same (one orchestrator dispatches + watches), but on cross-session resume — a fresh intent later asking ``jules.watch(session=sid)`` — they differ. This verb resolves through ``JulesSession SERVES Intent`` to pick the right queue; ``for_intent`` lets the caller override the resolution explicitly. Returns the resolved intent on the response under ``_for_intent`` so the caller knows whose queue was read.

## Example

```bash
agency-jules-watch --intent-id $IID …
```
