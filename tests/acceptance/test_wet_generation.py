"""Acceptance — Spec 338 OpenRouter-first wet generation.

Tests ``LLMClient.generate()`` (free-text generation) and
``select_text_generator()`` (provider selection rule).  All scenarios are
hermetic — no real network calls.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, scenarios, then, when
from unittest.mock import MagicMock

from agency._llm import GenerationResult, LLMClient, select_text_generator

scenarios("features/wet_generation.feature")


# ── minimal driver stand-in ──────────────────────────────────────────────────

class _FakeDrivers:
    """Minimal DriverRegistry-shaped object for select_text_generator tests."""
    def __init__(self):
        self.llm_obj = object()
        self.anthropic_obj = object()

    def get(self, name: str):
        return self.llm_obj if name == "llm" else self.anthropic_obj


# ── scenario: OpenRouter wins when both keys set ──────────────────────────────

@given("a driver registry with llm and anthropic drivers registered", target_fixture="ctx")
def _both_drivers():
    return {"drivers": _FakeDrivers()}


@when("select_text_generator is called with both keys set in the env")
def _call_both_keys(ctx):
    env = {"OPENROUTER_API_KEY": "or-key", "ANTHROPIC_API_KEY": "an-key"}
    ctx["result"] = select_text_generator(ctx["drivers"], env=env)


@then('the returned backend name is "llm"')
def _name_is_llm(ctx):
    assert ctx["result"][0] == "llm"


@then("the returned driver is the registered llm object")
def _driver_is_llm(ctx):
    assert ctx["result"][1] is ctx["drivers"].llm_obj


# ── scenario: Anthropic fallback ─────────────────────────────────────────────

@when("select_text_generator is called with only ANTHROPIC_API_KEY set")
def _call_anthropic_only(ctx):
    ctx["result"] = select_text_generator(ctx["drivers"],
                                          env={"ANTHROPIC_API_KEY": "an-key"})


@then('the returned backend name is "anthropic"')
def _name_is_anthropic(ctx):
    assert ctx["result"][0] == "anthropic"


@then("the returned driver is the registered anthropic object")
def _driver_is_anthropic(ctx):
    assert ctx["result"][1] is ctx["drivers"].anthropic_obj


# ── scenario: DEPENDENCY_MISSING ─────────────────────────────────────────────

@when("select_text_generator is called with no keys set")
def _call_no_keys(ctx):
    try:
        select_text_generator(ctx["drivers"], env={})
        ctx["error"] = None
    except RuntimeError as exc:
        ctx["error"] = exc


@then("a RuntimeError is raised mentioning dependency_missing")
def _check_dep_missing(ctx):
    assert ctx["error"] is not None, "expected RuntimeError but none was raised"
    assert "dependency_missing" in str(ctx["error"])


# ── scenario: generate() enforces :free suffix ───────────────────────────────

@given("the OPENROUTER_API_KEY is set in the environment", target_fixture="ctx")
def _or_key_set(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    return {}


@when("LLMClient.generate is called with a non-free model override")
def _gen_non_free(ctx):
    client = LLMClient()
    try:
        client.generate("hello", model="some-model/name")
        ctx["error"] = None
    except ValueError as exc:
        ctx["error"] = exc


@then("a ValueError is raised mentioning the :free requirement")
def _check_free_error(ctx):
    assert ctx["error"] is not None, "expected ValueError but none was raised"
    assert ":free" in str(ctx["error"])


# ── scenario: generate() raises without API key ──────────────────────────────

@given("the OPENROUTER_API_KEY is absent from the environment", target_fixture="ctx")
def _no_or_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    return {}


@when("LLMClient.generate is called with the default model")
def _gen_no_key(ctx, monkeypatch):
    client = LLMClient()       # __init__ only needs AGENCY_LLM_MODEL, not OR key
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    try:
        client.generate("hello")
        ctx["error"] = None
    except RuntimeError as exc:
        ctx["error"] = exc


@then("a RuntimeError is raised mentioning the missing key")
def _check_missing_key(ctx):
    assert ctx["error"] is not None, "expected RuntimeError but none was raised"
    assert "OPENROUTER_API_KEY" in str(ctx["error"])


# ── scenario: generate() returns GenerationResult via mocked call ────────────

@given("httpx.post is mocked to return a valid generation response")
def _mock_httpx(ctx, monkeypatch):
    fake_resp = MagicMock()
    fake_resp.raise_for_status.return_value = None
    fake_resp.json.return_value = {
        "choices": [{
            "message": {"content": "The quick brown fox."},
            "finish_reason": "stop",
        }]
    }
    import httpx
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: fake_resp)


@when("LLMClient.generate is called with a prompt")
def _gen_with_prompt(ctx):
    client = LLMClient()
    ctx["result"] = client.generate("Tell me something.")


@then("the result is a GenerationResult instance")
def _check_type(ctx):
    assert isinstance(ctx["result"], GenerationResult)


@then("the model in the result ends with :free")
def _check_model_free(ctx):
    assert ctx["result"].model.endswith(":free")


@then('the backend in the result is "openrouter"')
def _check_backend(ctx):
    assert ctx["result"].backend == "openrouter"
