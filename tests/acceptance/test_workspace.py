"""Acceptance — workspace capability (Spec 002).

Converted from tests/test_workspace*.py (none existed in the flat suite — new coverage).

Dropped as implementation/structural (not behaviour):
- VCS client internals (subprocess boundary)

GAPS: real git worktree creation requires a live git repository. Covered here
with a stub VCS backend injected at Engine construction time. The real GitClient
is never called.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke
from agency.engine import Engine

scenarios("features/workspace.feature")


# ── stub VCS ─────────────────────────────────────────────────────────────────

class _StubVCS:
    def __init__(self, worktree_ok=True, run_returncode=0):
        self._worktree_ok = worktree_ok
        self._run_returncode = run_returncode

    def worktree(self, branch: str, base: str) -> dict:
        return {"path": f"/tmp/wt-{branch.replace('/', '-')}",
                "branch": branch, "base": base, "ok": self._worktree_ok, "detail": ""}

    def run(self, command: str, cwd: str) -> dict:
        return {"returncode": self._run_returncode, "output": "stub output"}

    def state(self, branch: str, base: str) -> dict:
        return {"ahead": 0, "behind": 0, "dirty": False, "ok": True}

    def finish(self, branch: str, action: str, base: str) -> dict:
        return {"action": action, "ok": True, "detail": "stub"}

    def remote_exists(self, branch: str, remote: str = "origin") -> dict:
        return {"exists": True, "sha": "abc123", "ok": True, "detail": ""}


def _make_engine(vcs=None):
    return Engine(tempfile.mktemp(suffix=".db"), vcs_backend=vcs or _StubVCS())


def _unwrap(res):
    return res.get("result", res) if isinstance(res, dict) else res


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    e = _make_engine()
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("workspace acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@given(parsers.parse('an isolated workspace for branch "{branch}"'),
       target_fixture="workspace_data")
def _workspace_for(engine, confirmed_intent, branch):
    res, _ = invoke(engine, confirmed_intent, "workspace", "isolate",
                    branch=branch, base="main")
    r = _unwrap(res)
    return r["workspace"], engine, confirmed_intent


# ── isolate ───────────────────────────────────────────────────────────────────

@when(parsers.parse('I isolate branch "{branch}"'), target_fixture="isolate_result")
def _isolate(engine, confirmed_intent, branch):
    res, _ = invoke(engine, confirmed_intent, "workspace", "isolate",
                    branch=branch, base="main")
    return _unwrap(res), engine, confirmed_intent


@then("a Workspace node is recorded with the branch name")
def _workspace_recorded(isolate_result):
    res, engine, iid = isolate_result
    ws_id = res["workspace"]
    node = engine.memory.recall(ws_id)
    assert node is not None
    assert node.get("branch") == "feature/safe-work"


@then("the Workspace SERVES the intent")
def _workspace_serves(isolate_result):
    res, engine, iid = isolate_result
    rows = engine.memory.g.query(
        "MATCH (w:Workspace)-[:SERVES]->(i:Intent) WHERE w.id=$w AND i.id=$i RETURN w",
        {"w": res["workspace"], "i": iid})
    assert rows


# ── baseline ──────────────────────────────────────────────────────────────────

@when(parsers.parse('I run the baseline command "{cmd}" in the workspace'),
      target_fixture="baseline_result")
def _baseline_green(workspace_data, cmd):
    ws_id, engine, iid = workspace_data
    res, _ = invoke(engine, iid, "workspace", "baseline",
                    workspace=ws_id, command=cmd)
    return _unwrap(res), ws_id, engine


@then("the baseline result reports passed true")
def _baseline_passed(baseline_result):
    res, ws_id, engine = baseline_result
    assert res["passed"] is True


@then("the workspace has a BASELINED edge to the Baseline")
def _baselined_edge(baseline_result):
    res, ws_id, engine = baseline_result
    rows = engine.memory.g.query(
        "MATCH (w:Workspace)-[:BASELINED]->(b:Baseline) WHERE w.id=$w RETURN b",
        {"w": ws_id})
    assert rows


@when("I run a failing baseline command in the workspace", target_fixture="baseline_fail")
def _baseline_fail(workspace_data):
    ws_id, engine, iid = workspace_data
    # Use an engine with a failing VCS stub for the run
    fail_engine = _make_engine(vcs=_StubVCS(run_returncode=1))
    # Re-create the workspace in the failing engine so baseline can find it
    iid2 = fail_engine.intent.capture("fail", "d", "a")
    fail_engine.intent.confirm(iid2)
    iso, _ = invoke(fail_engine, iid2, "workspace", "isolate",
                    branch="feature/failing", base="main")
    ws2_id = _unwrap(iso)["workspace"]
    res, _ = invoke(fail_engine, iid2, "workspace", "baseline",
                    workspace=ws2_id, command="pytest -q")
    return _unwrap(res)


@then("the baseline result reports passed false")
def _baseline_not_passed(baseline_fail):
    assert baseline_fail["passed"] is False


@when("I baseline against an unknown workspace id", target_fixture="baseline_unknown")
def _baseline_unknown(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "workspace", "baseline",
                    workspace="workspace:does-not-exist", command="echo ok")
    return _unwrap(res)


@then("the baseline result carries an error")
def _baseline_error(baseline_unknown):
    assert "error" in baseline_unknown
