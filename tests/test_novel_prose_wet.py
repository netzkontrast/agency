"""Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279.

Spec 130 scene-writer phase 3 was a stub (no driver binding). Spec 220
Slice 1 wires it to a real TextDriver backed by the AnthropicDriver
(Spec 147) AND the host-LLM delegation envelope (Spec 279) so a
no-key host (Claude Code) can run inference itself instead of failing.

Slice 1 ships:
- driver-bound path → Completion → Spec 154 capture → body_handle
- delegation envelope path (prefer_delegate=True + backend "none")
- host_completion resume path
- voice-locked invariant (alter_id requires Spec 144 brief)
- typed WetSceneResult shape

Slice 2+ wires the check-driven regenerate loop (the shipped prose
checks gate the output; failures trigger bounded re-generation).
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 220 wet prose", "ship slice 1", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    """Return (data_dict, invocation_id). data is None on failure."""
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def _err_code(e: Engine, inv_id: str) -> str:
    """Read the typed error code from the failed Invocation node."""
    return e.memory.recall(inv_id).get("error", "")


# ── stub drivers ───────────────────────────────────────────────────────────
class _FakeCapableDriver:
    """Stub AnthropicDriver: backend "anthropic" + scripted complete()."""

    def __init__(self, body: str = "<draft scene body>"):
        self._body = body
        self.calls: list[dict] = []

    def backend(self) -> str:
        return "anthropic"

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        from agency._drivers._anthropic import Completion
        return Completion(
            text=self._body, stop_reason="end_turn", model="claude-test")


class _NoBackendDriver:
    def backend(self) -> str:
        return "none"

    def complete(self, **_kwargs):                                # pragma: no cover
        raise AssertionError("must not call .complete on no-backend driver")


# ── verb registration ─────────────────────────────────────────────────────
def test_generate_scene_body_is_registered():
    e = _fresh()
    cap = e.registry._caps["novel"]
    assert "generate_scene_body" in cap.verbs


def test_scene_writer_phase_3_binds_generate_scene_body():
    """Slice 1 lands the deferred phase 3 binding."""
    from agency.capabilities.novel._main import SCENE_WRITER_SKILL
    gen = next(p for p in SCENE_WRITER_SKILL["phases"]
               if p["name"] == "generate")
    assert "novel.generate_scene_body" in gen["verbs"]


# ── driver path (Branch 2 of complete_or_delegate) ────────────────────────
def test_generate_scene_body_uses_capable_driver_and_returns_handle():
    """Capable driver → Completion → Spec 154 capture → body_handle.
    Body is NEVER inline (Spec 146 prefix discipline; Spec 154 budget)."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver(body="The rain hammered the slate.")
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="Open on a storm at dusk.")
    assert data is not None, "verb must succeed"
    assert data["driver"] == "spec147"
    assert data["wc"] == 5
    assert data["body_handle"], "body_handle must be the Artefact id"
    assert data["voice_locked"] is False
    # Codex review (P2) on PR #137: Slice 1 hasn't wired the gate loop;
    # `checks=[]` means no gate was applied. Report `unchecked=True` +
    # `passes_all=False` rather than the misleading `passes_all=True`.
    assert data["passes_all"] is False
    assert data["unchecked"] is True
    # The Artefact carries the full body — verb response does NOT.
    assert "body" not in data, "body must travel via handle, not inline"


def test_generate_scene_body_forwards_brief_to_driver():
    """The brief becomes the user message; the driver sees it intact."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver()
    e.drivers.register("anthropic", driver)
    _invoke(e, iid, "generate_scene_body",
            scene_id="", brief="Brief X under storm.")
    assert len(driver.calls) == 1
    messages = driver.calls[0]["messages"]
    assert messages[0]["content"] == "Brief X under storm."
    # The default system prompt is sent.
    system = driver.calls[0]["system"]
    assert "novelist" in system.lower()


def test_generate_scene_body_voice_locked_marks_artefact():
    """When alter_id is set, the scene is voice-locked; the system
    prompt mentions the alter and `voice_locked=True`."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver(body="Locked-voice draft.")
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="Voice-locked brief body.",
                       alter_id="kira-pov")
    assert data is not None
    assert data["voice_locked"] is True
    system = driver.calls[0]["system"]
    assert "kira-pov" in system


def test_voice_locked_requires_brief():
    """Voice-lock fidelity invariant: alter_id without a brief is a
    caller bug — VOICE_BRIEF_MISSING typed code."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver()
    e.drivers.register("anthropic", driver)
    data, inv = _invoke(e, iid, "generate_scene_body",
                         scene_id="", brief="", alter_id="kira-pov")
    assert data is None
    assert "VOICE_BRIEF_MISSING" in _err_code(e, inv)


# ── delegate path (Branch 3 — Spec 279) ───────────────────────────────────
def test_generate_scene_body_emits_delegate_envelope_when_prefer_delegate():
    """No-backend driver + prefer_delegate=True → kind=llm_delegate
    envelope so Claude Code (the host) runs inference. The body is
    empty until the host resumes."""
    e = _fresh()
    iid = _iid(e)
    e.drivers.register("anthropic", _NoBackendDriver())
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="Brief.",
                       prefer_delegate=True)
    assert data is not None
    assert data["driver"] == "delegate"
    assert data["kind"] == "llm_delegate"
    req = data["request"]
    assert req["kind"] == "llm_delegate"
    assert "continuation_token" in req
    assert "messages" in req
    assert data["body_handle"] == ""
    assert data["wc"] == 0


def test_generate_scene_body_typed_fail_when_no_driver_no_delegate():
    """No driver + no resume + prefer_delegate=False → typed
    DEPENDENCY_MISSING failure; the verb never crashes the loop."""
    e = _fresh()
    iid = _iid(e)
    # The default AnthropicDriver auto-registered by Engine has
    # backend "none" (no key). With prefer_delegate=False we refuse.
    data, inv = _invoke(e, iid, "generate_scene_body",
                         scene_id="", brief="x")
    assert data is None
    assert "DEPENDENCY_MISSING" in _err_code(e, inv)


# ── resume path (Branch 1 — host_completion wins) ─────────────────────────
def test_generate_scene_body_resume_from_host_completion():
    """host_completion supplied → the verb parses the host's text into
    a body Artefact; reports driver=host."""
    e = _fresh()
    iid = _iid(e)
    e.drivers.register("anthropic", _NoBackendDriver())
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="x",
                       host_completion={"text":
                                          "Host-generated scene body."})
    assert data is not None
    assert data["driver"] == "host"
    assert data["wc"] == 3
    assert data["body_handle"], "Artefact id required on resume"


def test_generate_scene_body_resume_wins_over_capable_driver():
    """host_completion supplied → host path wins even when a capable
    driver is wired. The driver must NOT be invoked."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver(body="never-fetched")
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="x",
                       host_completion={"text": "Host text wins."})
    assert data is not None
    assert data["driver"] == "host"
    assert driver.calls == [], "driver must NOT be invoked on resume"


def test_generate_scene_body_resume_malformed_returns_typed_code():
    """Malformed host_completion (no text) → HOST_DELEGATE_MALFORMED."""
    e = _fresh()
    iid = _iid(e)
    e.drivers.register("anthropic", _NoBackendDriver())
    data, inv = _invoke(e, iid, "generate_scene_body",
                         scene_id="", brief="x",
                         host_completion={"parsed": {}})            # no text
    assert data is None
    assert "HOST_DELEGATE_MALFORMED" in _err_code(e, inv)


# ── provenance + body-via-handle invariant ────────────────────────────────
def test_generate_scene_body_records_scene_body_artefact_with_provenance():
    """A scene-body Artefact PRODUCES_FROM the Scene + SERVES the
    intent — the provenance moat invariant. The Scene must EXIST
    (Codex review on PR #137 — NOT_FOUND guard)."""
    e = _fresh()
    iid = _iid(e)
    # Real Scene required for provenance linkage.
    scene_id = e.memory.record("Scene", {
        "chapter": "chap-1", "slug": "scene-xyz",
        "pov": "third-limited"})
    driver = _FakeCapableDriver(body="One sentence draft.")
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id=scene_id, brief="x")
    aid = data["body_handle"]
    artefact = e.memory.recall(aid)
    assert artefact is not None
    assert artefact["kind"] == "scene-body"
    assert artefact["scene_id"] == scene_id
    assert "draft" in artefact["full_body"]
    assert artefact["driver"] == "spec147"


def test_generate_scene_body_returns_not_found_for_unknown_scene():
    """Codex review on PR #137 (P2): validate scene_id BEFORE spending
    LLM work. A mistyped scene_id would otherwise burn real inference
    and produce prose whose body_handle can't be integrated."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver()
    e.drivers.register("anthropic", driver)
    data, inv = _invoke(e, iid, "generate_scene_body",
                         scene_id="scene:not-a-real-id", brief="x")
    assert data is None
    assert "NOT_FOUND" in _err_code(e, inv)
    # Driver must NOT have been invoked — that's the whole point.
    assert driver.calls == []


def test_fetch_scene_body_returns_full_body_for_handle():
    """Spec 220 Slice 1.5: `novel.fetch_scene_body(body_handle)` is the
    public retrieval path (Codex review on PR #137 P1: the prior
    response only carried `body_handle` and the body was stranded
    behind a graph-internal field)."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver(body="The full scene body text.")
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="x")
    handle = data["body_handle"]
    fetched, _ = _invoke(e, iid, "fetch_scene_body", body_handle=handle)
    assert fetched is not None
    assert fetched["body"] == "The full scene body text."
    assert fetched["total_chars"] == len("The full scene body text.")
    assert fetched["voice_locked"] is False
    assert fetched["truncated"] is False
    assert fetched["driver"] == "spec147"


def test_fetch_scene_body_honors_max_chars_cap():
    """Caller-side budget cap so a large body can be streamed in slices."""
    e = _fresh()
    iid = _iid(e)
    driver = _FakeCapableDriver(body="x" * 2000)
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body", brief="x")
    fetched, _ = _invoke(e, iid, "fetch_scene_body",
                          body_handle=data["body_handle"], max_chars=500)
    assert fetched["truncated"] is True
    assert len(fetched["body"]) == 500
    assert fetched["total_chars"] == 2000


def test_fetch_scene_body_rejects_unknown_handle():
    """Bad handle → NOT_FOUND."""
    e = _fresh()
    iid = _iid(e)
    data, inv = _invoke(e, iid, "fetch_scene_body",
                         body_handle="artefact:not-real")
    assert data is None
    assert "NOT_FOUND" in _err_code(e, inv)


def test_fetch_scene_body_rejects_non_scene_body_artefact():
    """A handle that points at an Artefact of a DIFFERENT kind is
    rejected — preserves the contract that body_handle resolves to a
    Spec 220 scene-body specifically."""
    e = _fresh()
    iid = _iid(e)
    aid = e.memory.record("Artefact", {"kind": "something-else"})
    data, inv = _invoke(e, iid, "fetch_scene_body", body_handle=aid)
    assert data is None
    assert "BAD_REQUEST" in _err_code(e, inv)


def test_generate_scene_body_response_carries_no_inline_body():
    """Spec 146 + Spec 154 invariant: the verb response NEVER carries
    the full body inline — wrapping LLM drivers fetch via handle.
    A 3KB-body call must still return a tiny response."""
    e = _fresh()
    iid = _iid(e)
    big = "x " * 1500                                              # ~3KB
    driver = _FakeCapableDriver(body=big)
    e.drivers.register("anthropic", driver)
    data, _ = _invoke(e, iid, "generate_scene_body",
                       scene_id="", brief="x")
    # The response data must NOT contain the body text.
    assert big.strip() not in str(data), \
        "the full body must not appear inline in the response"
    # But the handle resolves to an Artefact carrying it.
    art = e.memory.recall(data["body_handle"])
    assert big.strip() in art["full_body"]
