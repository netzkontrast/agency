"""Spec 012 Phase 7 — `jules.watch` / `jules.recover` / `jules.apply_patch` verbs.

These wrap the watcher's queue + recovery-in-flight tracker as engine-level
verbs auto-wired through MCP / Skills / bash CLI. The watcher is engine-
attached at `engine._jules_watcher` and populated by `_jules_watch.start(engine)`
(Phase 8 wiring); verbs reach it via `self.ctx.engine`.
"""
import asyncio
import tempfile

import pytest

from agency.capabilities.jules import watch as _jules_watch
from agency.engine import Engine


@pytest.fixture
def engine():
    """Fresh engine per test. The watcher is engine-attached (not a module
    singleton) so each fixture gets its own clean instance — no manual
    state cleanup needed."""
    return Engine(tempfile.mktemp(suffix=".db"))


def _attach_watcher(engine):
    """Attach a Watcher to the engine WITHOUT starting the poll loop.

    Tests exercise the watcher's queue + recovery_in_flight surface via the
    engine; the poll loop's asyncio.Task isn't part of what we want to test
    here (its behavior is covered in tests/test_jules_watch.py + the
    recovery-signature integration test). This mirrors what
    `_jules_watch.start(engine)` would do for the attach step.
    """
    engine._jules_watcher = _jules_watch.Watcher()
    return engine._jules_watcher


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "watch + recover + apply_patch",
        "verbs surface watcher state through the engine",
        "queue events bubble; recovery in-flight tracked; plan returns ordered ops",
    )
    engine.intent.confirm(intent)
    return intent


def _call(engine, iid, verb, **kw):
    res, _inv = engine.registry.invoke(
        engine.memory, iid, "jules", verb, agent_id="agent:claude", **kw
    )
    return res


# ---------------------------------------------------------------------------
# watch — drains the per-intent queue + heartbeat fallback.
# ---------------------------------------------------------------------------


def test_watch_returns_error_without_session_or_for_intent(engine, iid):
    res = _call(engine, iid, "watch")
    assert res["action"] == "error"
    assert "session or for_intent" in res["instruction"]


def test_watch_emits_noop_when_watcher_not_started(engine, iid):
    """No `start(engine)` call → engine._jules_watcher absent → noop with explanation."""
    assert not hasattr(engine, "_jules_watcher")
    res = _call(engine, iid, "watch", for_intent=iid)
    assert res["action"] == "noop"
    assert "not started" in res["evidence"]["reason"]


def test_watch_drains_queued_event(engine, iid):
    """When the watcher has a queued event for the intent, watch returns it
    immediately (no polling)."""
    watcher = _attach_watcher(engine)
    event = {"action": "verify_pr", "session": "sess-1", "state": "COMPLETED",
             "instruction": "...", "evidence": {}}
    watcher._put_event(iid, event)
    res = _call(engine, iid, "watch", for_intent=iid)
    # Verb adds a `_for_intent` trace field so callers know whose queue
    # was read; original event fields are preserved verbatim.
    assert res["_for_intent"] == iid
    assert {k: v for k, v in res.items() if k != "_for_intent"} == event


def test_watch_heartbeat_after_short_timeout(engine, iid):
    """Empty queue + zero timeout → immediate noop heartbeat."""
    watcher = _attach_watcher(engine)
    res = _call(engine, iid, "watch", for_intent=iid, timeout=0)
    assert res["action"] == "noop"
    assert res["instruction"] == "Working."


def test_watch_resolves_intent_from_session_serves_edge(engine, iid):
    """When `session` is supplied but no `for_intent`, the verb walks the
    `JulesSession SERVES Intent` edge to find the watching intent."""
    watcher = _attach_watcher(engine)
    # Seed a JulesSession node + SERVES edge to iid.
    sess_id = "jules-session:edge-resolve"
    engine.memory.record("JulesSession", {"sid": "edge-resolve"}, node_id=sess_id)
    engine.memory.link(sess_id, iid, "SERVES")
    event = {"action": "noop", "instruction": "from edge", "evidence": {}}
    watcher._put_event(iid, event)
    res = _call(engine, iid, "watch", session="edge-resolve")
    # Drop the verb-added trace field for the equality check.
    assert res.get("_for_intent") == iid
    res_no_trace = {k: v for k, v in res.items() if k != "_for_intent"}
    assert res_no_trace == event


# ---------------------------------------------------------------------------
# recover — promotes session to recovery_in_flight, returns immediately.
# ---------------------------------------------------------------------------


def test_recover_errors_when_watcher_not_started(engine, iid):
    assert not hasattr(engine, "_jules_watcher")
    res = _call(engine, iid, "recover", session="s-nostart")
    assert res["status"] == "error"
    assert "not started" in res["reason"]


def test_recover_promotes_to_recovery_in_flight(engine, iid):
    watcher = _attach_watcher(engine)
    res = _call(engine, iid, "recover", session="s-1",
                owner="netzkontrast", repo="agency", branch="feature-x", base="main")
    assert res == {"status": "probing", "session": "s-1", "attempts_planned": 3}
    assert "s-1" in watcher.recovery_in_flight
    st = watcher.recovery_in_flight["s-1"]
    assert st["attempt"] == 0
    assert st["intent_id"] == iid
    assert st["owner"] == "netzkontrast"
    assert st["repo"] == "agency"
    assert st["base"] == "main"
    assert st["recover_branch"] == "recover-s-1"


def test_recover_defaults_base_to_main_when_omitted(engine, iid):
    watcher = _attach_watcher(engine)
    _call(engine, iid, "recover", session="s-2")
    assert watcher.recovery_in_flight["s-2"]["base"] == "main"
    # owner/repo empty when not supplied — the recovery path falls back to
    # parsing sourceContext at probe-exhaustion time.
    assert watcher.recovery_in_flight["s-2"]["owner"] == ""


# ---------------------------------------------------------------------------
# apply_patch — returns the planner output verbatim (does NOT execute ops).
# ---------------------------------------------------------------------------


def test_apply_patch_returns_planner_output(engine, iid, monkeypatch):
    """The verb is a pure planner — returns ordered {tool, args} ops for the
    agent to execute via GitHub MCP. Spec 012 REVIEW must-fix #1: the verb
    does NOT execute cross-MCP ops itself."""
    from agency.capabilities.jules import api as _jules_api
    from agency.capabilities.jules import patch as _jules_patch

    fake_session = {
        "id": "s-apply",
        "outputs": [{"changeSet": {"gitPatch": {"unidiffPatch": (
            "diff --git a/new.txt b/new.txt\n"
            "new file mode 100644\n"
            "index 0000000..e69de29\n"
            "--- /dev/null\n"
            "+++ b/new.txt\n"
            "@@ -0,0 +1,1 @@\n"
            "+hello\n"
        )}}}],
        "sourceContext": {"source": "sources/netzkontrast-agency"},
    }
    monkeypatch.setattr(_jules_api, "jules_get_full", lambda sid: fake_session)

    res = _call(engine, iid, "apply_patch", session="s-apply")

    assert res["branch"] == "recover-s-apply"
    assert res["base_branch"] == "main"
    ops = res["ops"]
    assert ops[0]["tool"] == "mcp__github__create_branch"
    assert ops[0]["args"]["owner"] == "netzkontrast"
    assert ops[0]["args"]["repo"] == "agency"
    assert any(op["tool"] == "mcp__github__push_files" for op in ops)
    assert any(op["tool"] == "mcp__github__create_pull_request" for op in ops)


def test_apply_patch_respects_explicit_owner_repo(engine, iid, monkeypatch):
    """When the caller plumbs owner/repo, the parser fallback is skipped."""
    from agency.capabilities.jules import api as _jules_api

    monkeypatch.setattr(_jules_api, "jules_get_full", lambda sid: {
        "id": "s-explicit", "outputs": [],
        "sourceContext": {"source": "sources/wrong-source"},
    })
    res = _call(engine, iid, "apply_patch", session="s-explicit",
                owner="someone-else", repo="myrepo", branch="custom-recover",
                base="develop")
    assert res["branch"] == "custom-recover"
    assert res["base_branch"] == "develop"
    assert res["ops"][0]["args"]["owner"] == "someone-else"
    assert res["ops"][0]["args"]["repo"] == "myrepo"
