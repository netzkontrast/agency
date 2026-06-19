"""Spec 285 Slice 1 — the host-bridge seam.

`ctx.sample()` / `ctx.elicit()` live on the FastMCP ``Context``, which is
injected only into wired tools — capability verbs (and the ``skill_walk``
walker) receive the agency ``CapabilityContext`` and have no handle to the
client. That gap is why Spec 279 returns an ``llm_delegate`` envelope instead
of sampling directly.

`HostBridge` bridges the live FastMCP ``Context`` into the capability layer,
request-scoped via a ``ContextVar`` set on every wired-tool entry (see
``engine._wire``). It exposes a narrow, agency-typed surface — ``can_sample`` /
``can_elicit`` (capability + the ``sampling_enabled`` flag), ``sample`` (→ the
driver-agnostic ``Completion`` shape), and ``elicit`` (→ a typed
``ElicitOutcome``). With no bound Context (CLI, bare tests, no client support),
``can_*`` is False and ``sample``/``elicit`` raise ``HostUnavailable`` so callers
fall back (Spec 279 envelope for sampling; ``input-required`` pause for elicit).
"""
from __future__ import annotations

import contextvars
import os
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from agency._drivers._anthropic import Completion

# Request-scoped binding of the live FastMCP Context. Set per wired-tool call in
# engine._wire; async-task-isolated (no cross-call leak). Default None → the
# bridge reports "no host" everywhere a Context isn't bound.
_HOST_CTX: "contextvars.ContextVar[Any]" = contextvars.ContextVar(
    "agency_host_ctx", default=None)


def bind_host_context(ctx: Any) -> "contextvars.Token":
    """Bind the live FastMCP Context for the current task; returns the reset
    token. Callers (``engine._wire``) reset in a ``finally`` so a Context never
    outlives its call."""
    return _HOST_CTX.set(ctx)


def reset_host_context(token: "contextvars.Token") -> None:
    _HOST_CTX.reset(token)


def current_host_context() -> Any:
    return _HOST_CTX.get(None)


def sampling_enabled_default() -> bool:
    """Spec 285 OQ3 — ``sampling_enabled`` resolution: explicit Engine kwarg
    wins (passed straight to ``HostBridge``); else ``AGENCY_SAMPLING_ENABLED``
    env (``0``/``false``/``no``/``off`` → False); else True."""
    raw = os.environ.get("AGENCY_SAMPLING_ENABLED")
    if raw is None:
        return True
    return raw.strip().lower() not in ("0", "false", "no", "off", "")


class HostUnavailable(Exception):
    """Raised by ``sample``/``elicit`` when no capable host Context is bound.
    Callers convert this to their documented fallback (envelope / pause)."""


@dataclass(frozen=True)
class ElicitOutcome:
    """Typed result of an ask-in-the-flow elicitation.

    ``action`` ∈ {accept, decline, cancel}. ``data`` carries the accepted
    value(s) (a dict for structured/options elicits, else the raw scalar).
    """
    action: str
    data: Any = None

    @property
    def accepted(self) -> bool:
        return self.action == "accept"


class HostBridge:
    """The one boundary by which a capability verb reaches the host LLM
    (sampling) and the user (elicitation). Wraps the FastMCP Context; never a
    new wire surface (code-mode stays the only contract)."""

    def __init__(self, ctx: Any = None, *, sampling_enabled: Optional[bool] = None) -> None:
        self._ctx = ctx
        self._sampling_enabled = (sampling_enabled if sampling_enabled is not None
                                  else sampling_enabled_default())

    # --- capability negotiation -------------------------------------------
    @property
    def sampling_enabled(self) -> bool:
        return self._sampling_enabled

    def can_sample(self) -> bool:
        """True when a Context is bound, it exposes ``sample``, AND the
        ``sampling_enabled`` flag is on. The actual client-capability check
        happens at call time (try/except) — a False here is a hard 'no host'."""
        return bool(self._sampling_enabled and self._ctx is not None
                    and hasattr(self._ctx, "sample"))

    def can_elicit(self) -> bool:
        return bool(self._ctx is not None and hasattr(self._ctx, "elicit"))

    # --- sampling ----------------------------------------------------------
    def sample(self, messages: "str | Sequence[Any]", *,
               system: Optional[str] = None,
               max_tokens: int = 8000,
               temperature: Optional[float] = None) -> Completion:
        """Ask the host LLM to generate (MCP ``sampling/createMessage``).

        SYNC — every consumer (``complete_or_delegate``, the ``skill_walk``
        walker) runs on the synchronous verb-invoke path; ``ctx.sample`` is
        async, so we bridge it (FastMCP runs sync tools in an AnyIO worker
        thread; ``_run`` drives the coroutine via ``anyio.from_thread``).
        Returns the driver-agnostic ``Completion`` shape. Raises
        ``HostUnavailable`` when no capable Context is bound (caller falls back
        to the Spec 279 envelope)."""
        if not self.can_sample():
            raise HostUnavailable("no sampling-capable host Context bound")
        kwargs: dict = {"max_tokens": max_tokens}
        if system is not None:
            kwargs["system_prompt"] = system
        if temperature is not None:
            kwargs["temperature"] = temperature

        async def _call():
            return await self._ctx.sample(messages, **kwargs)
        try:
            result = _run(_call)
        except HostUnavailable:
            raise
        except Exception as e:                       # client lacks sampling, or it failed
            raise HostUnavailable(f"host sampling failed: {type(e).__name__}: {e}") from e
        return _normalise_completion(result)

    # --- elicitation -------------------------------------------------------
    def elicit(self, message: str, *,
               options: Optional[Sequence[Any]] = None) -> ElicitOutcome:
        """Ask the user in the flow (SYNC; bridged like ``sample``). ``options``
        (when given) request a structured single choice; else free text. Raises
        ``HostUnavailable`` when no elicit-capable Context is bound (caller
        pauses for resume)."""
        if not self.can_elicit():
            raise HostUnavailable("no elicit-capable host Context bound")
        response_type = list(options) if options else None

        async def _call():
            return await self._ctx.elicit(message, response_type=response_type)
        try:
            result = _run(_call)
        except HostUnavailable:
            raise
        except Exception as e:
            raise HostUnavailable(f"host elicit failed: {type(e).__name__}: {e}") from e
        return _normalise_elicit(result)


def _run(coro_factory):
    """Drive an async client call from synchronous verb code.

    On the live path the sync verb runs in an AnyIO worker thread, so
    ``anyio.from_thread.run`` schedules the coroutine back on the server's event
    loop and blocks for the result. In a unit test / direct-async context (no
    worker-thread portal) that raises ``RuntimeError`` — we fall back to running
    the coroutine on a fresh loop."""
    from anyio.from_thread import run
    try:
        return run(coro_factory)
    except RuntimeError:
        import asyncio
        return asyncio.run(coro_factory())


def _normalise_completion(result: Any) -> Completion:
    """Coerce a FastMCP ``SamplingResult`` (or a fake/str) into ``Completion``."""
    if isinstance(result, Completion):
        return result
    text = getattr(result, "text", None)
    if text is None:
        # SamplingResult may expose .content / .data, or be a bare string.
        text = getattr(result, "content", None)
        if text is None:
            text = result if isinstance(result, str) else str(result)
    return Completion(text=str(text), stop_reason="host_sampled")


def _normalise_elicit(result: Any) -> ElicitOutcome:
    """Coerce a FastMCP elicitation result into the typed outcome. FastMCP
    returns AcceptedElicitation/DeclinedElicitation/CancelledElicitation;
    we read the class name + ``.data`` defensively (fakes use the same shape)."""
    name = type(result).__name__.lower()
    if "decline" in name:
        return ElicitOutcome("decline")
    if "cancel" in name:
        return ElicitOutcome("cancel")
    data = getattr(result, "data", result)
    return ElicitOutcome("accept", data)
