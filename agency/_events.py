"""Spec 349a — the pillar event bus (first slice).

A capability/intent/memory SUBSCRIBES to a hook event by declaring a handler;
the engine fans each hook out to the matching subscriptions, with a ``once_per``
dedup backed by the Spec 336 ephemeral tool-call store (so it survives the
fresh-process-per-hook model — Spec 349 review M5). This is SUBSTRATE, not a
capability (Spec 349 review B1): a module registry the engine consumes;
capabilities only declare subscriptions + handlers.

Contracts honoured:
- **fail-OPEN** — a dedup/store error never blocks the triggering tool call;
- **fail-ISOLATED** — a raising subscriber is skipped, never breaks the hook;
- **no graph record per delivery** — the dedup marker lives in the EPHEMERAL
  store, not the durable graph (Spec 349 review S1 / Spec 336), so a high-volume
  event like ``PreToolUse`` can never recreate the graph bloat Spec 336 removed.

This first slice wires the ``PreToolUse`` event (the frugal first-use hint is the
reference subscriber); ``event.emit`` for custom events + lifecycle events are
later slices (349b+).
"""
from __future__ import annotations

# [(event_name, handler(engine, event) -> str, once_per, name)] — append-only,
# idempotent by (event, name). Module-level so the engine consumes it as substrate.
_SUBSCRIPTIONS: list[tuple] = []


def subscribe(event: str, handler, *, once_per: str = "", name: str = "") -> None:
    """Declare a hook-event subscription. ``handler(engine, event) -> str`` returns
    the context fragment to inject (empty = nothing). ``once_per="session.tool"``
    fires at most once per (session, tool). Idempotent by (event, name) so a
    re-imported capability module never double-registers."""
    nm = name or getattr(handler, "__name__", "")
    _SUBSCRIPTIONS[:] = [s for s in _SUBSCRIPTIONS if (s[0], s[3]) != (event, nm)]
    _SUBSCRIPTIONS.append((event, handler, once_per, nm))


def subscriptions_for(event: str) -> list[tuple]:
    """Every subscription registered for ``event``, in registration order."""
    return [s for s in _SUBSCRIPTIONS if s[0] == event]


def _first_use(store, session: str, tool: str, name: str) -> bool:
    """True the FIRST time this subscriber sees (session, tool); writes a marker so
    later calls return False. Per-subscriber (the phase carries ``name``) and
    reuses the Spec 336 store (survives the per-event process model). Fail-open:
    any error → False. A concurrent double is acceptable — a duplicate snippet
    beats a blocked tool call (Spec 349 review S1)."""
    if not store or not session or not tool:
        return False
    phase = f"first_use:{name}"
    try:
        if store.rows(where="phase = ? AND tool = ? AND session = ?",
                      params=(phase, tool, session)):
            return False
        store.record(phase=phase, tool=tool, session=session)
        return True
    except Exception:
        return False


def run(engine, event_name: str, event: dict) -> list[str]:
    """Fan ``event_name`` out to its subscriptions, applying each one's ``once_per``
    dedup, and return the emitted context fragments in registration order.
    Fail-isolated: a raising subscriber is skipped."""
    out: list[str] = []
    ev = event or {}
    session, tool = ev.get("session_id", ""), ev.get("tool_name", "")
    for _evt, handler, once_per, name in subscriptions_for(event_name):
        try:
            if once_per == "session.tool" and not _first_use(
                    getattr(engine, "toolcalls", None), session, tool, name):
                continue
            text = handler(engine, event) or ""
        except Exception:
            continue
        if text:
            out.append(text)
    return out
