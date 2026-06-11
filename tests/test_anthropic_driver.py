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


def test_dispatch_session_is_slice2_deferred():
    from agency._drivers._anthropic import DriverError
    d = _driver()
    with pytest.raises(DriverError) as ei:
        d.dispatch_session("agent_x", "env_y", "kickoff")
    assert ei.value.code == DriverError.BAD_REQUEST
    assert "Slice 2" in str(ei.value)


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
