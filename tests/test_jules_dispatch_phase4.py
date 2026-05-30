"""Spec 013 Phase 4 — jules.dispatch arg extension + flag interaction matrix.

Two new pass-through args on `jules.dispatch` (and `JulesBackend.create` /
`_jules_api.jules_create`):

- `automation_mode` — canonical Jules-side field (``"" | "AUTO_CREATE_PR"``).
- `protocol_preset` — when non-empty, prepends the Mode-A/B preamble via
  `_jules_preambles.assemble(...)`.

`auto_create_pr=True` becomes a back-compat alias for
`automation_mode="AUTO_CREATE_PR"` with a one-shot DeprecationWarning.

Tests verify each cell of the flag interaction matrix at the Stub backend
boundary (we record what `create` is invoked with) AND exercise the full
chain `dispatch -> backend.create -> _jules_api.jules_create` for the
deprecation-alias semantics.
"""
import tempfile
import warnings

import pytest

from agency.capabilities import _jules_api
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
    assert kw["auto_create_pr"] is False


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
# Back-compat alias: auto_create_pr -> automation_mode.
# ---------------------------------------------------------------------------


def test_auto_create_pr_passes_through_to_api(engine, iid):
    """At the dispatch verb boundary `auto_create_pr=True` is forwarded
    verbatim; the API client is what does the mapping + the deprecation
    warning (deprecation belongs at the lowest layer that knows the
    canonical name)."""
    _dispatch(engine, iid, auto_create_pr=True)
    kw = _client(engine).last_kwargs
    assert kw["auto_create_pr"] is True
    # The verb does NOT pre-translate — that's the API's job.
    assert kw["automation_mode"] == ""


def test_api_maps_auto_create_pr_to_automation_mode_with_warning(monkeypatch):
    """At `_jules_api.jules_create`, `auto_create_pr=True` produces a body
    with `automationMode: AUTO_CREATE_PR` AND fires a DeprecationWarning
    (once per process, per the spec). Reset the module-level guard so the
    test exercises the warning path."""
    captured: dict = {}
    monkeypatch.setattr(_jules_api, "_request",
                        lambda method, path, body=None, params=None: captured.setdefault("body", body) or {"id": "s"})
    monkeypatch.setattr(_jules_api, "_coerce_source", lambda s: f"sources/{s.replace('/', '-')}")
    monkeypatch.setattr(_jules_api, "_AUTO_CREATE_PR_DEPRECATION_FIRED", False)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _jules_api.jules_create(prompt="p", source="o/r", starting_branch="main",
                                auto_create_pr=True)

    assert captured["body"]["automationMode"] == "AUTO_CREATE_PR"
    # DeprecationWarning fired exactly once for this call.
    deprecations = [x for x in w if issubclass(x.category, DeprecationWarning)]
    assert len(deprecations) == 1
    assert "automation_mode" in str(deprecations[0].message)


def test_api_explicit_automation_mode_wins_over_alias(monkeypatch):
    """When both `automation_mode` and `auto_create_pr` are supplied, the
    explicit canonical name wins and no deprecation fires."""
    captured: dict = {}
    monkeypatch.setattr(_jules_api, "_request",
                        lambda method, path, body=None, params=None: captured.setdefault("body", body) or {"id": "s"})
    monkeypatch.setattr(_jules_api, "_coerce_source", lambda s: f"sources/{s.replace('/', '-')}")
    monkeypatch.setattr(_jules_api, "_AUTO_CREATE_PR_DEPRECATION_FIRED", False)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _jules_api.jules_create(prompt="p", source="o/r", starting_branch="main",
                                auto_create_pr=True,
                                automation_mode="AUTO_CREATE_PR")

    assert captured["body"]["automationMode"] == "AUTO_CREATE_PR"
    # Explicit canonical name → no deprecation fires (auto_create_pr is ignored).
    assert not [x for x in w if issubclass(x.category, DeprecationWarning)]


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
