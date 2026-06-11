"""Spec 147 — the canonical AnthropicDriver boundary (Slice 1: inference surface).

The driver mirrors the Spec 092 G3 LLMClient pattern (lazy, key-gated, degrades
cleanly, reports a backend for agency_doctor) but exposes the typed
`complete` / `count_tokens` surface the `claude-api` skill documents:
adaptive thinking, output_config structured outputs, and typed `DriverError`
handling for refusal / rate-limit / overload / auth / network.

Tests inject a fake SDK client (no `anthropic` package, no network) — the
driver imports the SDK lazily inside `_sdk()`, so the module imports without it.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


# ── fake anthropic SDK client ────────────────────────────────────────────────
class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text="hi", stop_reason="end_turn", model="claude-opus-4-8",
                 stop_details=None, input_tokens=10, output_tokens=5):
        self.content = [_Block(text)] if text else []
        self.stop_reason = stop_reason
        self.stop_details = stop_details
        self.model = model
        self._request_id = "req_abc"

        class _U:
            pass
        self.usage = _U()
        self.usage.input_tokens = input_tokens
        self.usage.output_tokens = output_tokens
        self.usage.cache_read_input_tokens = 0
        self.usage.cache_creation_input_tokens = 0


class _Details:
    def __init__(self, category):
        self.category = category


class _FakeMessages:
    def __init__(self, resp=None, raise_exc=None, count=42):
        self._resp = resp or _Resp()
        self._raise = raise_exc
        self._count = count
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        if self._raise:
            raise self._raise
        return self._resp

    def count_tokens(self, **kw):
        self.calls.append(kw)

        class _C:
            pass
        c = _C()
        c.input_tokens = self._count
        return c


class _FakeClient:
    def __init__(self, messages=None):
        self.messages = messages or _FakeMessages()


def _driver(client=None, **kw):
    from agency._drivers._anthropic import AnthropicDriver
    return AnthropicDriver(client=client or _FakeClient(), **kw)


# ── backend selection (never the key) ────────────────────────────────────────
def test_backend_none_without_key_or_client(monkeypatch):
    from agency._drivers._anthropic import AnthropicDriver
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert AnthropicDriver().backend() == "none"


def test_backend_anthropic_with_key(monkeypatch):
    from agency._drivers._anthropic import AnthropicDriver
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert AnthropicDriver().backend() == "anthropic"


def test_backend_anthropic_with_injected_client(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert _driver().backend() == "anthropic"


def test_model_default_and_override(monkeypatch):
    from agency._drivers._anthropic import AnthropicDriver
    monkeypatch.delenv("AGENCY_ANTHROPIC_MODEL", raising=False)
    assert AnthropicDriver().model == "claude-opus-4-8"
    monkeypatch.setenv("AGENCY_ANTHROPIC_MODEL", "claude-sonnet-4-6")
    assert AnthropicDriver().model == "claude-sonnet-4-6"
    assert AnthropicDriver(model="claude-haiku-4-5").model == "claude-haiku-4-5"


# ── claude-api skill defaults are applied to the request ─────────────────────
def test_complete_applies_adaptive_thinking_and_effort():
    msgs = _FakeMessages()
    d = _driver(_FakeClient(msgs))
    d.complete([{"role": "user", "content": "hi"}], system="sys", effort="high")
    sent = msgs.calls[0]
    assert sent["thinking"] == {"type": "adaptive"}
    assert sent["output_config"]["effort"] == "high"
    assert sent["model"] == "claude-opus-4-8"
    assert sent["system"] == "sys"


def test_complete_returns_typed_completion():
    d = _driver(_FakeClient(_FakeMessages(_Resp(text="the answer"))))
    c = d.complete([{"role": "user", "content": "q"}])
    assert c.text == "the answer"
    assert c.stop_reason == "end_turn"
    assert c.model == "claude-opus-4-8"
    assert c.usage["input_tokens"] == 10
    assert c.request_id == "req_abc"


def test_output_schema_sets_format_and_parses_json():
    resp = _Resp(text='{"choice": "a", "n": 2}')
    msgs = _FakeMessages(resp)
    d = _driver(_FakeClient(msgs))
    schema = {"type": "object", "properties": {"choice": {"type": "string"}}}
    c = d.complete([{"role": "user", "content": "q"}], output_schema=schema)
    assert msgs.calls[0]["output_config"]["format"]["type"] == "json_schema"
    assert c.parsed == {"choice": "a", "n": 2}


# ── refusal + typed error handling (Nygard failure modes) ────────────────────
def test_refusal_raises_typed_driver_error_with_category():
    from agency._drivers._anthropic import DriverError
    resp = _Resp(text="", stop_reason="refusal", stop_details=_Details("cyber"))
    d = _driver(_FakeClient(_FakeMessages(resp)))
    with pytest.raises(DriverError) as ei:
        d.complete([{"role": "user", "content": "q"}])
    assert ei.value.code == DriverError.REFUSAL
    assert ei.value.detail.get("category") == "cyber"


class _RateLimit(Exception):
    status_code = 429


class _Overloaded(Exception):
    status_code = 529


class _Auth(Exception):
    status_code = 401


def test_rate_limit_maps_to_typed_code():
    from agency._drivers._anthropic import DriverError
    d = _driver(_FakeClient(_FakeMessages(raise_exc=_RateLimit("slow down"))))
    with pytest.raises(DriverError) as ei:
        d.complete([{"role": "user", "content": "q"}])
    assert ei.value.code == DriverError.RATE_LIMITED


def test_overload_maps_to_typed_code():
    from agency._drivers._anthropic import DriverError
    d = _driver(_FakeClient(_FakeMessages(raise_exc=_Overloaded("busy"))))
    with pytest.raises(DriverError) as ei:
        d.complete([{"role": "user", "content": "q"}])
    assert ei.value.code == DriverError.OVERLOADED


def test_auth_failure_maps_to_typed_code():
    from agency._drivers._anthropic import DriverError
    d = _driver(_FakeClient(_FakeMessages(raise_exc=_Auth("bad key"))))
    with pytest.raises(DriverError) as ei:
        d.complete([{"role": "user", "content": "q"}])
    assert ei.value.code == DriverError.AUTH_FAILED


def test_complete_without_key_or_client_raises_auth(monkeypatch):
    from agency._drivers._anthropic import AnthropicDriver, DriverError
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(DriverError) as ei:
        AnthropicDriver().complete([{"role": "user", "content": "q"}])
    assert ei.value.code == DriverError.AUTH_FAILED


# ── count_tokens ─────────────────────────────────────────────────────────────
def test_count_tokens_returns_input_tokens():
    d = _driver(_FakeClient(_FakeMessages(count=137)))
    assert d.count_tokens([{"role": "user", "content": "q"}]) == 137


# ── readiness report (agency_doctor) ─────────────────────────────────────────
def test_readiness_shape(monkeypatch):
    from agency._drivers._anthropic import AnthropicDriver
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-x")
    r = AnthropicDriver().readiness()
    assert r["api_key_present"] is True
    assert r["model_id_resolved"] == "claude-opus-4-8"
    assert r["managed_agents_capable"] is False        # Slice 2


# ── Slice 2: Managed-Agents bridge — dispatch_session ────────────────────────
class _FakeSession:
    """The shape of `client.beta.agents.sessions.create(...)` response."""

    def __init__(self, session_id="sess_abc", status="running",
                 status_reason=None, started_at="2026-06-11T00:00:00Z"):
        self.id = session_id
        self.status = status
        self.status_reason = status_reason
        self.started_at = started_at


class _FakeSessions:
    def __init__(self, response=None, raise_exc=None):
        self._response = response or _FakeSession()
        self._raise = raise_exc
        self.calls: list[dict] = []

    def create(self, **kw):
        self.calls.append(kw)
        if self._raise:
            raise self._raise
        return self._response


class _FakeAgentsClient:
    def __init__(self, sessions):
        self.sessions = sessions


class _FakeBeta:
    def __init__(self, sessions):
        self.agents = _FakeAgentsClient(sessions)


class _FakeManagedClient:
    def __init__(self, sessions):
        self.beta = _FakeBeta(sessions)


def test_dispatch_session_returns_typed_session_handle():
    """Slice 2: `dispatch_session` returns a typed SessionHandle with the
    session_id + status from the SDK response."""
    from agency._drivers._anthropic import AnthropicDriver, SessionHandle
    sessions = _FakeSessions(_FakeSession(session_id="sess_abc",
                                            status="running"))
    d = AnthropicDriver(client=_FakeManagedClient(sessions))
    h = d.dispatch_session(agent_id="agent_x", env_id="env_y",
                           kickoff="Summarize chapter 1")
    assert isinstance(h, SessionHandle)
    assert h.session_id == "sess_abc"
    assert h.status == "running"
    assert h.status_reason is None or h.status_reason == ""


def test_dispatch_session_passes_create_once_args():
    """Per claude-api skill: Agent FIRST, then session — NO EXCEPTIONS.
    The SDK call MUST reference a pre-created agent_id + env_id;
    Slice 2 does NOT create the agent itself."""
    from agency._drivers._anthropic import AnthropicDriver
    sessions = _FakeSessions()
    d = AnthropicDriver(client=_FakeManagedClient(sessions))
    d.dispatch_session(agent_id="agent_x", env_id="env_y",
                       kickoff="kickoff text")
    assert len(sessions.calls) == 1
    call = sessions.calls[0]
    # The SDK kwargs MUST carry the pre-created agent_id + env_id; the
    # driver does NOT mint a new agent (Spec 137 Lock owns that).
    assert call.get("agent_id") == "agent_x"
    # env_id maps to environment_id in the SDK.
    assert call.get("environment_id") == "env_y" or \
           call.get("env_id") == "env_y"
    # kickoff travels under one of these documented names.
    kickoff_args = (call.get("kickoff_message")
                    or call.get("kickoff")
                    or call.get("initial_message"))
    assert "kickoff text" in str(kickoff_args)


def test_dispatch_session_rejects_empty_agent_id():
    """Pre-create doctrine: dispatch needs a real agent_id, never empty."""
    from agency._drivers._anthropic import AnthropicDriver, DriverError
    d = AnthropicDriver(client=_FakeManagedClient(_FakeSessions()))
    with pytest.raises(DriverError) as ei:
        d.dispatch_session(agent_id="", env_id="env_y", kickoff="x")
    assert ei.value.code == DriverError.BAD_REQUEST


def test_dispatch_session_rejects_empty_env_id():
    from agency._drivers._anthropic import AnthropicDriver, DriverError
    d = AnthropicDriver(client=_FakeManagedClient(_FakeSessions()))
    with pytest.raises(DriverError) as ei:
        d.dispatch_session(agent_id="agent_x", env_id="", kickoff="x")
    assert ei.value.code == DriverError.BAD_REQUEST


def test_dispatch_session_rejects_empty_kickoff():
    from agency._drivers._anthropic import AnthropicDriver, DriverError
    d = AnthropicDriver(client=_FakeManagedClient(_FakeSessions()))
    with pytest.raises(DriverError) as ei:
        d.dispatch_session(agent_id="agent_x", env_id="env_y", kickoff="")
    assert ei.value.code == DriverError.BAD_REQUEST


def test_dispatch_session_carries_status_reason_when_failed():
    """When the SDK returns a non-running status with a reason
    (e.g. status='terminated', status_reason='unauthorized'), the
    handle surfaces both so the engine can branch."""
    from agency._drivers._anthropic import AnthropicDriver
    sessions = _FakeSessions(_FakeSession(session_id="sess_x",
                                            status="terminated",
                                            status_reason="unauthorized"))
    d = AnthropicDriver(client=_FakeManagedClient(sessions))
    h = d.dispatch_session(agent_id="agent_x", env_id="env_y",
                           kickoff="x")
    assert h.status == "terminated"
    assert h.status_reason == "unauthorized"


def test_session_handle_is_frozen_dataclass():
    from agency._drivers._anthropic import SessionHandle
    h = SessionHandle(session_id="s", status="running")
    with pytest.raises(Exception):
        h.session_id = "mutated"                                   # frozen


def test_readiness_reflects_managed_agents_capable_when_client_has_beta():
    """`agency_doctor.anthropic_driver.managed_agents_capable` flips
    True when the injected client exposes the .beta.agents.sessions
    surface (Slice 2 detection signal)."""
    from agency._drivers._anthropic import AnthropicDriver
    d = AnthropicDriver(client=_FakeManagedClient(_FakeSessions()))
    r = d.readiness()
    assert r["managed_agents_capable"] is True


def test_readiness_managed_agents_false_when_client_lacks_beta():
    """A bare client (just messages.create) reports
    managed_agents_capable=False."""

    class _BareClient:
        pass

    from agency._drivers._anthropic import AnthropicDriver
    d = AnthropicDriver(client=_BareClient())
    r = d.readiness()
    assert r["managed_agents_capable"] is False


def test_dispatch_session_maps_sdk_auth_error_to_driver_error():
    """SDK exceptions are mapped to typed DriverError (Spec 002 boundary)."""
    from agency._drivers._anthropic import AnthropicDriver, DriverError

    class _AuthErr(Exception):
        pass

    sessions = _FakeSessions(raise_exc=_AuthErr("AuthenticationError: bad key"))
    d = AnthropicDriver(client=_FakeManagedClient(sessions))
    with pytest.raises(DriverError) as ei:
        d.dispatch_session(agent_id="agent_x", env_id="env_y", kickoff="x")
    # Generic exception (not a recognized SDK name) maps to BAD_REQUEST or NETWORK;
    # the contract is: it raises DriverError, never the raw SDK exception.
    assert isinstance(ei.value, DriverError)


# ── engine wiring ────────────────────────────────────────────────────────────
def test_anthropic_driver_registered_by_default():
    e = Engine(":memory:")
    try:
        assert e.drivers.has("anthropic")
    finally:
        e.memory.close()


def test_doctor_reports_anthropic_driver(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-x")
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        out, _ = e.registry.invoke_substrate("agency_doctor") \
            if hasattr(e.registry, "invoke_substrate") else (None, None)
        # the readiness method is the contract; doctor surfaces it
        assert e.anthropic_driver.readiness()["api_key_present"] is True
        assert e.anthropic_driver.backend() == "anthropic"
    finally:
        e.memory.close()
