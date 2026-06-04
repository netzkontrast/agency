"""Spec 013 Phase 4 — jules.dispatch arg extension + flag interaction matrix.

Two new pass-through args on `jules.dispatch` (and `JulesBackend.create` /
`_jules_api.jules_create`):

- `automation_mode` — canonical Jules-side field (``"" | "AUTO_CREATE_PR"``).
- `protocol_preset` — when non-empty, prepends the Mode-A/B preamble via
  `_jules_preambles.assemble(...)`.

Tests verify each cell of the flag interaction matrix at the Stub backend
boundary AND the protocol-preset preamble wiring through to the request body.
"""
import tempfile

import pytest

from agency.capabilities.jules import api as _jules_api
from agency.engine import Engine


class _RecordingClient:
    """Stub backend that records every create-call kwargs verbatim."""
    def __init__(self):
        self.last_kwargs: dict = {}

    def create(self, **kw):
        self.last_kwargs = kw
        return {"id": "sessions/abc", "state": "QUEUED",
                "title": kw.get("title", ""), "url": "https://jules.google.com/session/abc"}

    # The rest of the Protocol — stubs that don't matter for these tests.
    def get(self, session): return {"state": "QUEUED"}
    def list(self, page_size, page_token=""): return {"sessions": []}
    def activities(self, session, page_size, only_kinds, page_token=""): return {"activities": []}
    def plan(self, session, max_pages): return {"steps": []}
    def approve_plan(self, session): return {"ok": True}
    def message(self, session, prompt): return {"ok": True}
    def resolve_source(self, owner, repo): return {"source": f"sources/{owner}-{repo}"}
    def get_full(self, session): return {"id": session, "outputs": []}
    def status_all(self, page_size, max_pages): return {"sessions": [], "total": 0}
    def approve_awaiting(self, limit): return {"approved": []}
    def quota(self, daily_limit): return {"active_today": 0, "headroom": 0}
    def patch(self, session): return {"total_files": 0, "outputs": []}


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"), jules_client=_RecordingClient())


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "Phase 4 dispatch args",
        "automation_mode + protocol_preset flow through",
        "deprecation alias warns + maps once",
    )
    engine.intent.confirm(intent)
    return intent


def _client(engine):
    return engine.jules_client


def _dispatch(engine, iid, **kw):
    return engine.registry.invoke(
        engine.memory, iid, "jules", "dispatch",
        agent_id="agent:jules",
        source="netzkontrast/agency", starting_branch="main", prompt="task body",
        **kw,
    )[0]


# ---------------------------------------------------------------------------
# Flag interaction matrix (DESIGN.md / AGENCY_PROTOCOL.md §7).
# ---------------------------------------------------------------------------


def test_matrix_default_is_plan_gated_no_automation(engine, iid):
    """Cell 1: require_plan_approval=True (default), automation_mode="".
    Doctrine default — plan-gated, agent confirms PR."""
    _dispatch(engine, iid)
    kw = _client(engine).last_kwargs
    assert kw["require_plan_approval"] is True
    assert kw["automation_mode"] == ""


def test_matrix_plan_gated_with_auto_pr(engine, iid):
    """Cell 2: require_plan_approval=True, automation_mode="AUTO_CREATE_PR".
    Agency-driving-Jules pattern — plan-gated, PR auto-opens."""
    _dispatch(engine, iid, automation_mode="AUTO_CREATE_PR")
    kw = _client(engine).last_kwargs
    assert kw["require_plan_approval"] is True
    assert kw["automation_mode"] == "AUTO_CREATE_PR"


def test_matrix_zero_touch(engine, iid):
    """Cell 4: require_plan_approval=False, automation_mode="AUTO_CREATE_PR".
    Zero-touch — flagged as the only unsafe-without-affects-lock combo."""
    _dispatch(engine, iid, require_plan_approval=False,
              automation_mode="AUTO_CREATE_PR")
    kw = _client(engine).last_kwargs
    assert kw["require_plan_approval"] is False
    assert kw["automation_mode"] == "AUTO_CREATE_PR"


# ---------------------------------------------------------------------------
# protocol_preset wiring — Mode A/B preamble prepends to prompt.
# ---------------------------------------------------------------------------


def test_protocol_preset_prepends_mode_a_preamble(monkeypatch):
    """Mode A (source == DISPATCH_SELF_SOURCE): preamble prepended; no
    clone block."""
    captured: dict = {}
    monkeypatch.setattr(_jules_api, "_request",
                        lambda method, path, body=None, params=None: captured.setdefault("body", body) or {"id": "s"})
    monkeypatch.setattr(_jules_api, "_coerce_source", lambda s: f"sources/{s.replace('/', '-')}")
    _jules_api.jules_create(
        prompt="USER PROMPT", source="netzkontrast/agency",
        starting_branch="main", protocol_preset="agency-default",
    )
    sent_prompt = captured["body"]["prompt"]
    assert "USER PROMPT" in sent_prompt
    # Mode A — no clone block.
    assert "git clone" not in sent_prompt
    # Preamble is present.
    assert "AGENCY_PROTOCOL.md" in sent_prompt


def test_protocol_preset_prepends_mode_b_clone_for_external_source(monkeypatch):
    """Mode B (any other source): preamble + explicit READ-ONLY clone
    instruction prepended."""
    captured: dict = {}
    monkeypatch.setattr(_jules_api, "_request",
                        lambda method, path, body=None, params=None: captured.setdefault("body", body) or {"id": "s"})
    monkeypatch.setattr(_jules_api, "_coerce_source", lambda s: f"sources/{s.replace('/', '-')}")
    _jules_api.jules_create(
        prompt="DO THE THING", source="someone/their-project",
        starting_branch="feature", protocol_preset="agency-default",
    )
    sent_prompt = captured["body"]["prompt"]
    assert "DO THE THING" in sent_prompt
    # Mode B — clone block prepended.
    assert "git clone --depth=1" in sent_prompt
    assert "read_file" in sent_prompt


def test_no_protocol_preset_means_no_prepend(monkeypatch):
    """When protocol_preset is empty (default), the prompt is sent verbatim."""
    captured: dict = {}
    monkeypatch.setattr(_jules_api, "_request",
                        lambda method, path, body=None, params=None: captured.setdefault("body", body) or {"id": "s"})
    monkeypatch.setattr(_jules_api, "_coerce_source", lambda s: f"sources/{s.replace('/', '-')}")
    _jules_api.jules_create(
        prompt="RAW PROMPT", source="netzkontrast/agency",
        starting_branch="main",
    )
    assert captured["body"]["prompt"] == "RAW PROMPT"


def test_protocol_preset_passed_through_dispatch_verb(engine, iid):
    """End-to-end: the verb forwards protocol_preset to the backend; the
    backend's create call sees it."""
    _dispatch(engine, iid, protocol_preset="agency-default")
    kw = _client(engine).last_kwargs
    assert kw["protocol_preset"] == "agency-default"
