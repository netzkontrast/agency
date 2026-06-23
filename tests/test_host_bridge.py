"""Spec 285 Slice 1 — HostBridge seam (sampling + elicitation boundary).

Unit-tests the bridge with fake Contexts, plus the request-scoped ContextVar
capture in engine._wire (a real verb reaches `self.ctx.host`).
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest

from agency._drivers._anthropic import Completion
from agency._host_bridge import (
    HostBridge,
    HostUnavailable,
    bind_host_context,
    current_host_context,
    reset_host_context,
)
from agency.capability import CapabilityBase, verb
from agency.engine import Engine


# ─────────────────────── no host bound ───────────────────────


def test_no_context_reports_incapable_and_raises() -> None:
    b = HostBridge(None)
    assert b.can_sample() is False
    assert b.can_elicit() is False
    with pytest.raises(HostUnavailable):
        b.sample("hi")
    with pytest.raises(HostUnavailable):
        b.elicit("pick one")


def test_sampling_disabled_flag_forces_incapable() -> None:
    class _Ctx:
        async def sample(self, *a, **k):  # capable client…
            return "x"
    b = HostBridge(_Ctx(), sampling_enabled=False)   # …but flag off
    assert b.can_sample() is False                   # OQ3 cost control
    with pytest.raises(HostUnavailable):
        b.sample("hi")


# ─────────────────────── fake capable host ───────────────────────


class _FakeCtx:
    def __init__(self) -> None:
        self.seen = {}

    async def sample(self, messages, **kwargs):
        self.seen["sample"] = (messages, kwargs)
        return _FakeSamplingResult("GENERATED")

    async def elicit(self, message, response_type=None):
        self.seen["elicit"] = (message, response_type)
        return _FakeAccepted({"pov": "first"})


class _FakeSamplingResult:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeAccepted:
    def __init__(self, data) -> None:
        self.data = data


def test_sample_returns_normalised_completion() -> None:
    ctx = _FakeCtx()
    b = HostBridge(ctx, sampling_enabled=True)
    assert b.can_sample() is True
    comp = b.sample("draft this", system="be terse", max_tokens=64)
    assert isinstance(comp, Completion)
    assert comp.text == "GENERATED"
    assert comp.stop_reason == "host_sampled"
    # system → system_prompt is forwarded to ctx.sample
    assert ctx.seen["sample"][1]["system_prompt"] == "be terse"
    assert ctx.seen["sample"][1]["max_tokens"] == 64


def test_elicit_structured_options_returns_accept_outcome() -> None:
    ctx = _FakeCtx()
    b = HostBridge(ctx)
    assert b.can_elicit() is True
    out = b.elicit("which pov?", options=["first", "third-limited"])
    assert out.accepted is True
    assert out.data == {"pov": "first"}
    assert ctx.seen["elicit"][1] == ["first", "third-limited"]   # response_type


def test_sample_failure_becomes_host_unavailable() -> None:
    class _Boom:
        async def sample(self, *a, **k):
            raise RuntimeError("client has no sampling capability")
    b = HostBridge(_Boom(), sampling_enabled=True)
    assert b.can_sample() is True            # optimistic; the call decides
    with pytest.raises(HostUnavailable):
        b.sample("hi")


# ─────────────────────── ContextVar binding ───────────────────────


def test_bind_reset_is_scoped() -> None:
    assert current_host_context() is None
    sentinel = object()
    token = bind_host_context(sentinel)
    try:
        assert current_host_context() is sentinel
    finally:
        reset_host_context(token)
    assert current_host_context() is None


# ─────────────────────── seam: a verb reaches ctx.host ───────────────────────


class _ProbeCap(CapabilityBase):
    """Minimal probe capability — reports what its ctx.host sees."""
    name = "hostprobe"

    @verb(role="transform")
    def host_state(self) -> dict:
        from agency.toolresult import ToolResult
        h = self.ctx.host
        return ToolResult.success(data={
            "can_sample": h.can_sample(),
            "can_elicit": h.can_elicit(),
            "bound": current_host_context() is not None,
        })


def _fresh(**kw) -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"),
                  extra_capabilities=[_ProbeCap.as_capability()],
                  _require_skill_doc=False, **kw)


def test_wire_binds_fastmcp_context_into_verb() -> None:
    # Calling a wired verb through the MCP server binds the injected FastMCP
    # Context request-scoped, so the verb's ctx.host sees a live host.
    e = _fresh()
    mcp = e.build_mcp(codemode=True)
    iid = e.intent.capture("spec 285", "host seam", "verified")
    e.intent.confirm(iid)

    async def main():
        return await mcp.call_tool("capability_hostprobe_host_state", {"intent_id": iid})

    res = asyncio.run(main())
    sc = res.structured_content
    assert sc["bound"] is True            # the ContextVar was set during the call
    assert sc["can_elicit"] is True       # the injected Context exposes elicit
    e.memory.close()


def test_host_unbound_outside_a_call() -> None:
    # After the call returns, the binding is reset (no leak across calls).
    assert current_host_context() is None


# ─────────────────────── complete_or_delegate precedence (Part A) ───────────


from agency._host_llm import HostLLMRequest, complete_or_delegate  # noqa: E402


class _Driver:
    def __init__(self, backend: str) -> None:
        self._backend = backend

    def backend(self) -> str:
        return self._backend

    def complete(self, **kw):
        return Completion(text="DRIVER", stop_reason="end_turn")


_MSGS = [{"role": "user", "content": "draft this"}]

# Spec 352 — the seam now routes plain text to an OpenRouter free model FIRST
# whenever OPENROUTER_API_KEY is set (which it is in the dev/CI env). These
# precedence tests target the driver / host-sampling / delegate branches, so
# they explicitly pass an env WITHOUT the key to opt out of free-first; the
# free-first branch gets its own test below.
_NO_FREE: dict = {}


def test_precedence_driver_wins_over_sample() -> None:
    out = complete_or_delegate(_Driver("anthropic"), messages=_MSGS, env=_NO_FREE,
                               host=HostBridge(_FakeCtx(), sampling_enabled=True))
    assert out.text == "DRIVER"                       # driver beats sample


def test_precedence_sample_wins_over_envelope() -> None:
    # driver backend "none" → host sampling is used before the envelope.
    out = complete_or_delegate(_Driver("none"), messages=_MSGS, env=_NO_FREE,
                               host=HostBridge(_FakeCtx(), sampling_enabled=True))
    assert isinstance(out, Completion)
    assert out.text == "GENERATED"
    assert out.stop_reason == "host_sampled"          # the third inference path


def test_precedence_no_host_falls_back_to_envelope() -> None:
    # no capable host → the Spec 279 envelope path is intact.
    out = complete_or_delegate(_Driver("none"), messages=_MSGS, env=_NO_FREE,
                               host=HostBridge(None))
    assert isinstance(out, HostLLMRequest)
    assert out.kind == "llm_delegate"


def test_precedence_sample_failure_falls_back_to_envelope() -> None:
    class _Boom:
        async def sample(self, *a, **k):
            raise RuntimeError("no sampling")
    out = complete_or_delegate(_Driver("none"), messages=_MSGS, env=_NO_FREE,
                               host=HostBridge(_Boom(), sampling_enabled=True))
    assert isinstance(out, HostLLMRequest)            # HostUnavailable → envelope


def test_precedence_free_first_wins_over_driver() -> None:
    # Spec 352: with OPENROUTER_API_KEY set, plain text routes free-first —
    # ahead of even a capable anthropic driver. A stub LLMClient keeps it
    # network-free; the marker is the openrouter_free stop_reason.
    class _StubGen:
        def generate(self, prompt, **kw):
            from agency._llm import GenerationResult
            return GenerationResult(text="FREE", model="x/m:free",
                                    backend="openrouter", finish_reason="stop")
    out = complete_or_delegate(_Driver("anthropic"), messages=_MSGS,
                               env={"OPENROUTER_API_KEY": "or"}, llm=_StubGen())
    assert out.stop_reason == "openrouter_free"
    assert out.text == "FREE"                          # free beats the driver


# ─────────────────────── agency_doctor host block ───────────────────────


def test_agency_doctor_reports_host_block() -> None:
    e = Engine(tempfile.mktemp(suffix=".db"), sampling_enabled=False)
    mcp = e.build_mcp(codemode=False)

    async def main():
        return await mcp.call_tool("agency_doctor", {})

    res = asyncio.run(main())
    host = res.structured_content["host"]
    assert set(host) == {"sampling", "elicitation", "sampling_enabled", "note"}
    assert host["sampling_enabled"] is False          # flag honoured
    assert host["sampling"] is False                  # flag off ⇒ never samples
    # Spec 390 — the host block is HONEST that capability is advertised, not
    # guaranteed: a declined request falls back to an input-required pause.
    assert "input-required" in host["note"] and "advertised" in host["note"]
    e.memory.close()
