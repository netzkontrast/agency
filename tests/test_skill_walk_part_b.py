"""Spec 285 Slice 1 Part B — walk-level sampling + enforced assumption-gate.

Drives `develop.skill_walk` over a synthetic probe skill that uses the new
`sample:` and `requires_input:`+`resolve_via:` phase fields, with a fake host
Context bound via the Spec-285 ContextVar seam.
"""
from __future__ import annotations

import tempfile

from agency._host_bridge import bind_host_context, reset_host_context
from agency.capability import CapabilityBase, verb
from agency.capabilities.develop._main import _phase
from agency.engine import Engine
from agency.ontology import OntologyExtension
from agency.toolresult import ToolResult

PROBE_WALK = {"name": "probe-walk", "kind": "discipline", "phases": [
    _phase(1, "draft", ["draft"],
           sample={"produces_key": "draft", "system": "s", "prompt": "p"}),
    _phase(2, "decide", ["choice"],
           requires_input=["choice"],
           resolve_via={"capability": "probewalk", "verb": "choices"}),
]}


class _ProbeWalkCap(CapabilityBase):
    name = "probewalk"
    ontology = OntologyExtension(skills={"probe-walk": PROBE_WALK})

    @verb(role="transform")
    def choices(self, keys: str = "") -> ToolResult:
        return ToolResult.success(data={"options": ["a", "b"], "keys": keys})


# ─────────────────────── fake host Context ───────────────────────


class _SampleCtx:
    async def sample(self, messages, **kw):
        return _Text("GENERATED")

    async def elicit(self, message, response_type=None):
        self.last_options = response_type
        return _Accepted({"choice": "a"})


class _Text:
    def __init__(self, text): self.text = text


class _Accepted:
    def __init__(self, data): self.data = data


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"),
                  extra_capabilities=[_ProbeWalkCap.as_capability()],
                  _require_skill_doc=False)


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 285 b", "walk fields", "verified")
    e.intent.confirm(iid)
    return iid


def _walk(e, iid, **kw):
    raw, _ = e.registry.invoke(e.memory, iid, "develop", "skill_walk",
                               name="probe-walk", **kw)
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


# ─────────────────────── sample phase ───────────────────────


def test_sample_phase_advances_with_host() -> None:
    e = _fresh()
    iid = _iid(e)
    token = bind_host_context(_SampleCtx())
    try:
        # draft is sampled; choice is supplied so the assumption-gate passes.
        out = _walk(e, iid, inputs={"choice": "a"})
    finally:
        reset_host_context(token)
    assert out["status"] == "completed", out
    assert out["outputs"]["draft"] == "GENERATED"     # host-sampled
    e.memory.close()


def test_sample_phase_pauses_without_host() -> None:
    e = _fresh()
    iid = _iid(e)
    out = _walk(e, iid, inputs={"choice": "a"})        # no host bound
    assert out["status"] == "input-required"
    assert out["blocked_on"] == "sample:draft"
    e.memory.close()


# ─────────────────────── assumption-gate ───────────────────────


def test_requires_input_elicits_and_advances() -> None:
    e = _fresh()
    iid = _iid(e)
    token = bind_host_context(_SampleCtx())
    try:
        out = _walk(e, iid, inputs={})                 # nothing supplied
    finally:
        reset_host_context(token)
    assert out["status"] == "completed", out
    assert out["outputs"]["choice"] == "a"             # the elicited choice
    # the resolve_via verb fired as a provenance-recording Invocation
    invs = [n for n in e.memory.find("Invocation")
            if n.get("capability") == "probewalk" and n.get("verb") == "choices"]
    assert invs, "resolve_via should invoke the in-capability options verb"
    e.memory.close()


def test_requires_input_pauses_without_elicit_host() -> None:
    e = _fresh()
    iid = _iid(e)
    token = bind_host_context(_SampleCtx())            # samples draft, then…
    try:
        out = _walk(e, iid, inputs={})
        # …with a host that DOES elicit it completes; to test the no-elicit
        # pause we bind a sample-only host.
    finally:
        reset_host_context(token)
    # sanity: with a full host it completes (covered above). Now the no-elicit case:
    e2 = _fresh()
    iid2 = _iid(e2)

    class _SampleOnly:
        async def sample(self, messages, **kw):
            return _Text("GENERATED")
    token2 = bind_host_context(_SampleOnly())
    try:
        out2 = _walk(e2, iid2, inputs={})
    finally:
        reset_host_context(token2)
    assert out2["status"] == "input-required"
    assert out2["blocked_on"] == "assumption:choice"
    assert out2["options"] == ["a", "b"]               # sourced from resolve_via
    e.memory.close()
    e2.memory.close()


def test_requires_input_satisfied_by_inputs_skips_elicit() -> None:
    e = _fresh()
    iid = _iid(e)
    token = bind_host_context(_SampleCtx())
    try:
        out = _walk(e, iid, inputs={"choice": "b"})
    finally:
        reset_host_context(token)
    assert out["status"] == "completed"
    assert out["outputs"]["choice"] == "b"             # the supplied value, not elicited
    # no resolve_via invocation needed when the value is already present
    invs = [n for n in e.memory.find("Invocation")
            if n.get("capability") == "probewalk" and n.get("verb") == "choices"]
    assert not invs
    e.memory.close()


# ─────────────────── Workstream H — gate pause names the resume path ───────────────────


def test_hard_gate_pause_carries_resume_from_and_hint() -> None:
    """Workstream H — a hard-gate pause must tell the caller the exact
    `resume_from` value (the PHASE NAME) + the outputs to supply, not just a
    bare gate-id blocked_on (the ingest hit this)."""
    import tempfile
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("h", "gate ux", "ok")
    e.intent.confirm(iid)
    raw, _ = e.registry.invoke(e.memory, iid, "develop", "skill_walk",
                               name="tdd", inputs={
                                   "failing_test": "test_x asserts behaviour",
                                   "implementation": "def x(): ...",
                                   "refactored": "tidy",
                                   "tests_pass": "12 passed"})
    out = raw["result"] if isinstance(raw, dict) and "result" in raw else raw
    assert out["status"] == "input-required"
    assert out["phase"] == "verify"
    assert out["resume_from"] == out["phase"]          # the phase name, not a gate id
    assert "resume_from" in out["hint"]
    assert out["resume_with"]                           # the outputs to supply
    e.memory.close()
