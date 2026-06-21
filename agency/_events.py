"""Spec 349a — the pillar event bus.

A capability/intent/memory SUBSCRIBES to a hook event by declaring a handler;
the engine fans each hook out to the matching subscriptions, with a ``once_per``
dedup backed by the Spec 336 ephemeral store's SEPARATE ``event_marker`` table (so
it survives the fresh-process-per-hook model — Spec 349 review M5 — WITHOUT
polluting the captured tool-call rows). This is SUBSTRATE, not a capability (Spec
349 review B1): a module registry the engine consumes; capabilities only declare
subscriptions + handlers.

Two ``once_per`` scopes:
- ``"session.tool"`` — once per (session, tool): the frugal FIRST-USE hint (a hint
  per tool; fail-open to SKIP — a missed hint is harmless);
- ``"session"`` — once per session (tool ignored): the frugal SESSION-DISCIPLINE
  inject (the deep card, delivered ONCE even though SessionStart fires on
  startup/resume/compact; fail-open to EMIT — the mandatory port must land).

Contracts honoured:
- **fail-OPEN** — a dedup/store error never blocks the triggering event; the
  per-subscription ``once_fail_emit`` flag picks the safe direction (emit vs skip);
- **fail-ISOLATED** — a raising subscriber is skipped, never breaks the hook; the
  exception is surfaced on the Spec 021 monitor (diagnosable, not silently lost —
  Spec 349 review S3);
- **no graph record per delivery** — the dedup marker lives in the EPHEMERAL
  store, not the durable graph (Spec 349 review S1 / Spec 336).

Spec 349b §2 — subscriptions are **declarative**: a capability declares a tuple of
:class:`Subscription` (DATA) and ONE engine-bootstrap loop
(:func:`register_capability_subscriptions`) resolves each handler by name + calls
:func:`subscribe`. Subscribers fire in ascending ``priority`` (§7).
``event.emit`` for custom + lifecycle events are later slices (349c+).
"""
from __future__ import annotations

from dataclasses import dataclass

# [(event, handler(engine, event) -> str, once_per, once_fail_emit, name, priority)]
# — append-only, idempotent by (event, name). Module-level: the engine consumes it
# as substrate; capabilities only declare subscriptions.
_SUBSCRIPTIONS: list[tuple] = []

_ONCE_SCOPES = ("", "session", "session.tool")


@dataclass(frozen=True)
class Subscription:
    """Spec 349b §2 — a capability's declared event interest as DATA (not an
    imperative ``subscribe`` call). ``handler`` is the NAME of a module-level
    ``handler(engine, event) -> str`` function on the capability's module,
    resolved against that module at engine bootstrap (so definition order in the
    file never matters). Declaring it as data makes it inspectable, driftable, and
    registered in ONE loop. ``once_fail_emit``/``priority`` mirror :func:`subscribe`."""

    event: str
    handler: str
    once_per: str = ""
    once_fail_emit: bool = False
    priority: int = 50
    name: str = ""


def subscribe(event: str, handler, *, once_per: str = "",
              once_fail_emit: bool = False, name: str = "",
              priority: int = 50) -> None:
    """Declare a hook-event subscription. ``handler(engine, event) -> str`` returns
    the context fragment to inject (empty = nothing).

    ``once_per``: ``""`` = every occurrence; ``"session.tool"`` = once per
    (session, tool); ``"session"`` = once per session. ``once_fail_emit`` picks the
    fail-open direction when the dedup store is unavailable — ``True`` emits anyway
    (a mandatory inject), ``False`` skips (an optional hint). ``priority`` orders
    multiple subscribers on one event (lower runs first, §7).

    ``name`` is REQUIRED and must be stable + unique per event (the idempotency
    key): a re-imported module re-subscribing with the same (event, name) REPLACES
    its prior entry rather than double-registering. An empty name is rejected — a
    ``__name__`` fallback silently clobbers same-named or anonymous handlers (Spec
    349 review M2)."""
    if not name:
        raise ValueError(
            f"subscribe(event={event!r}) requires an explicit, stable `name=` "
            "(the idempotency key); a derived __name__ silently clobbers "
            "same-named/anonymous handlers")
    if once_per not in _ONCE_SCOPES:
        raise ValueError(f"once_per must be one of {_ONCE_SCOPES}; got {once_per!r}")
    _SUBSCRIPTIONS[:] = [s for s in _SUBSCRIPTIONS if (s[0], s[4]) != (event, name)]
    _SUBSCRIPTIONS.append((event, handler, once_per, once_fail_emit, name, priority))


def subscriptions_for(event: str) -> list[tuple]:
    """Every subscription for ``event``, ordered by ascending ``priority`` then
    registration order (a stable sort — the §7 deterministic-ordering contract)."""
    return sorted((s for s in _SUBSCRIPTIONS if s[0] == event),
                  key=lambda s: s[5])


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
                      once_fail_emit=sub.once_fail_emit,
                      name=sub.name or f"{cap.name}.{sub.handler}",
                      priority=sub.priority)
            count += 1
    return count


def _deliver_once(store, once_per: str, session: str, tool: str, name: str,
                  *, fail_emit: bool) -> bool:
    """The dedup gate: ``True`` = deliver this occurrence, ``False`` = already
    delivered (skip). Builds the marker scope from ``once_per`` (``"session"`` →
    ``name``; ``"session.tool"`` → ``f"{name}:{tool}"``) and delegates to the
    store's atomic ``mark_seen``. ``fail_emit`` is returned when the marker cannot
    be checked (no session id / no store / sqlite error) — the caller's chosen
    fail-open direction."""
    if not session:
        return fail_emit
    if once_per == "session.tool" and not tool:
        return fail_emit
    if store is None:
        return fail_emit
    scope = name if once_per == "session" else f"{name}:{tool}"
    try:
        return store.mark_seen(scope=scope, session=session)
    except Exception:                                           # noqa: BLE001
        return fail_emit


def run(engine, event_name: str, event: dict) -> list[str]:
    """Fan ``event_name`` out to its subscriptions (ascending priority, §7),
    applying each one's ``once_per`` dedup, and return the emitted context
    fragments. Fail-isolated: a raising subscriber is skipped (and surfaced on the
    monitor)."""
    out: list[str] = []
    ev = event or {}
    session, tool = ev.get("session_id", ""), ev.get("tool_name", "")
    store = getattr(engine, "toolcalls", None)
    for _evt, handler, once_per, fail_emit, name, _prio in subscriptions_for(event_name):
        try:
            if once_per and not _deliver_once(
                    store, once_per, session, tool, name, fail_emit=fail_emit):
                continue
            text = handler(engine, event) or ""
        except Exception as exc:                                # noqa: BLE001
            _note_handler_error(engine, event_name, name, exc)
            continue
        if text:
            out.append(text)
    return out


def _note_handler_error(engine, event_name: str, name: str, exc: Exception) -> None:
    """Surface a swallowed subscriber exception on the Spec 021 monitor so a broken
    handler is diagnosable (Spec 349 review S3) — without breaking fail-isolation.
    Best-effort: the diagnostic itself must never raise."""
    try:
        from ._monitor import MonitorEvent
        engine.monitor.emit(MonitorEvent(
            source="events", kind="handler_error",
            message=f"{event_name}/{name}: {type(exc).__name__}: {exc}"))
    except Exception:                                           # noqa: BLE001
        pass
