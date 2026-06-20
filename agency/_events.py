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

from dataclasses import dataclass

# [(event_name, handler(engine, event) -> str, once_per, name, priority)] —
# append-only, idempotent by (event, name). Module-level so the engine consumes
# it as substrate.
_SUBSCRIPTIONS: list[tuple] = []


@dataclass(frozen=True)
class Subscription:
    """Spec 349b §2 — a capability's declared event interest as DATA (not an
    imperative ``subscribe`` call). ``handler`` is the NAME of a module-level
    ``handler(engine, event) -> str`` function on the capability's module,
    resolved against that module at engine bootstrap (so definition order in the
    file never matters). Declaring it as data makes it inspectable
    (``event.subscribers``), driftable, and registered in ONE loop."""

    event: str
    handler: str
    once_per: str = ""
    priority: int = 50
    name: str = ""


def subscribe(event: str, handler, *, once_per: str = "", name: str = "",
              priority: int = 50) -> None:
    """Declare a hook-event subscription. ``handler(engine, event) -> str`` returns
    the context fragment to inject (empty = nothing). ``once_per="session.tool"``
    fires at most once per (session, tool). ``priority`` orders multiple
    subscribers (lower runs first, §7). Idempotent by (event, name) so a
    re-imported capability module / a re-run bootstrap loop never double-registers."""
    nm = name or getattr(handler, "__name__", "")
    _SUBSCRIPTIONS[:] = [s for s in _SUBSCRIPTIONS if (s[0], s[3]) != (event, nm)]
    _SUBSCRIPTIONS.append((event, handler, once_per, nm, priority))


def subscriptions_for(event: str) -> list[tuple]:
    """Every subscription for ``event``, ordered by ascending ``priority`` then
    registration order (a stable sort — the §7 deterministic-ordering contract)."""
    return sorted((s for s in _SUBSCRIPTIONS if s[0] == event),
                  key=lambda s: s[4])


def register_capability_subscriptions(caps) -> int:
    """Spec 349b §2 — THE missing loop. Walk every registered capability, read its
    declarative ``subscriptions`` tuple, resolve each handler by name against the
    capability's module, and ``subscribe`` it. This is the *reader* the infra
    audit found missing: capabilities self-register verbs by reflection but could
    not self-register event interest. Returns the count registered."""
    import importlib
    # AGENCY-DRIFT: event-subscribers — every declarative subscription flows
    # through this loop; `grep -rn 'subscriptions =' agency/capabilities` lists
    # the declarations, `subscriptions_for(event)` lists the live registrations.
    count = 0
    for cap in caps:
        module = getattr(cap, "module", "")
        for sub in getattr(cap, "subscriptions", ()) or ():
            try:                                 # a broken sub never breaks bootstrap
                handler = getattr(importlib.import_module(module), sub.handler)
            except (ImportError, AttributeError):
                continue
            subscribe(sub.event, handler, once_per=sub.once_per,
                      name=sub.name or f"{cap.name}.{sub.handler}",
                      priority=sub.priority)
            count += 1
    return count


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
    for _evt, handler, once_per, name, _prio in subscriptions_for(event_name):
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
