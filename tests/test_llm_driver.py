"""Spec 092 G3 — the LLM-decider Driver + intent.suggests's llm_select Matcher."""
import tempfile

import pytest

from agency.capability import CapabilityBase, verb
from agency.engine import Engine
from agency.ontology import OntologyExtension


class _StubLLM:
    def __init__(self, choice="match", confidence=0.9):
        self.choice, self.confidence, self.calls = choice, confidence, []

    def decide(self, prompt, options, model=None):
        self.calls.append((prompt, options))
        return {"choice": self.choice, "confidence": self.confidence}


class _LLMSkillCap(CapabilityBase):
    name = "llmcap"
    home = "capability"
    ontology = OntologyExtension(skills={"llm-skill": {
        "name": "llm-skill", "kind": "discipline",
        "phases": [{"index": 1, "name": "go", "produces": ["x"]}],
        "applies_when": {"kind": "llm_select", "llm_select": {"prompt": "applies?"}}}})

    @verb(role="transform")
    def noop(self) -> dict:
        """Gist. Inputs: none. Returns: nothing. chain_next: none."""
        return {}


def _engine(llm=None):
    kw = {"extra_capabilities": [_LLMSkillCap.as_capability()], "_require_skill_doc": False}
    if llm is not None:
        kw["drivers"] = {"llm": llm}
    return Engine(tempfile.mktemp(suffix=".db"), **kw)


def _suggest(e):
    iid = e.intent.capture("a", "b", "c")
    e.intent.confirm(iid)
    out, _ = e.registry.invoke(e.memory, iid, "intent", "suggests", called_state="xyz")
    return out["result"] if isinstance(out, dict) and "result" in out else out


def test_llm_driver_registered_by_default():
    e = Engine(":memory:")
    try:
        assert e.drivers.has("llm")
    finally:
        e.memory.close()


def test_llm_select_picks_skill_when_llm_says_match():
    stub = _StubLLM("match", 0.88)
    e = _engine(stub)
    try:
        out = _suggest(e)
        assert out["skill"] == "llm-skill" and out["mode"] == "llm_select"
        assert out["confidence"] == 0.88
        assert stub.calls and "llm-skill" in stub.calls[0][0]      # the LLM was consulted
    finally:
        e.memory.close()


def test_llm_select_skipped_when_llm_says_skip():
    e = _engine(_StubLLM("skip", 0.99))
    try:
        assert _suggest(e)["skill"] != "llm-skill"
    finally:
        e.memory.close()


def test_llm_select_degrades_gracefully_when_unconfigured(monkeypatch):
    # the default lazy LLMClient raises at call time (no OPENROUTER_API_KEY) → the matcher
    # is skipped, not crashed (pattern/verb_code Matchers stay unaffected).
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    e = _engine()                                                  # default LLMClient
    try:
        assert _suggest(e)["skill"] != "llm-skill"
    finally:
        e.memory.close()


# ── OpenRouter integration (backend selection + tolerant parse; no network) ──────
def test_backend_is_openrouter_when_keyed_else_none(monkeypatch):
    from agency._llm import LLMClient
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert LLMClient().backend() == "none"
    monkeypatch.setenv("OPENROUTER_API_KEY", "y")
    assert LLMClient().backend() == "openrouter"


def test_decide_raises_without_openrouter_key(monkeypatch):
    from agency._llm import LLMClient
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        LLMClient().decide("p", ["a", "b"])


def test_model_default_and_override(monkeypatch):
    from agency._llm import LLMClient
    monkeypatch.delenv("AGENCY_LLM_MODEL", raising=False)
    assert LLMClient().model == "openai/gpt-4o-mini"               # cheap/fast default
    monkeypatch.setenv("AGENCY_LLM_MODEL", "google/gemini-flash-1.5")
    assert LLMClient().model == "google/gemini-flash-1.5"
    assert LLMClient(model="anthropic/claude-3.5-haiku").model == "anthropic/claude-3.5-haiku"


def test_parse_handles_strict_json_fences_and_tolerant_fallback():
    from agency._llm import LLMClient
    p = LLMClient._parse
    assert p('{"choice": "match", "confidence": 0.7}', ["match", "skip"]) == \
        {"choice": "match", "confidence": 0.7}
    # fenced JSON (some models wrap in ```json) → stripped + parsed
    assert p('```json\n{"choice":"skip","confidence":0.4}\n```', ["match", "skip"]) == \
        {"choice": "skip", "confidence": 0.4}
    # prose mentioning an option → tolerant fallback
    assert p("I'd pick skip here.", ["match", "skip"])["choice"] == "skip"
    # a choice outside the option set is rejected → first option, conf 0
    assert p('{"choice": "maybe", "confidence": 0.9}', ["match", "skip"]) == \
        {"choice": "match", "confidence": 0.0}


def test_doctor_reports_llm_backend(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "y")
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        assert e.llm_client.backend() == "openrouter"
    finally:
        e.memory.close()
