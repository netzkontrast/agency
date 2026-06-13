"""Acceptance — branch capability (Spec 046).

Converted from tests/test_branch*.py (none existed in the flat suite — new coverage).

Dropped as implementation/structural (not behaviour):
- _infer_commit_type and _infer_scope private function internals
- The VCS client itself (real subprocess boundary)

GAPS: branch.assess and branch.finish with a REAL git repository are external
effects. Covered here with a stub VCS backend injected at Engine construction
time, per the VCSBackend protocol (_vcs.py). The real GitClient is never called.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke
from agency.engine import Engine

scenarios("features/branch.feature")


# ── stub VCS ─────────────────────────────────────────────────────────────────

class _StubVCS:
    def __init__(self, ahead=2, behind=0, dirty=False, finish_ok=True):
        self._ahead = ahead
        self._behind = behind
        self._dirty = dirty
        self._finish_ok = finish_ok

    def state(self, branch: str, base: str) -> dict:
        return {"ahead": self._ahead, "behind": self._behind,
                "dirty": self._dirty, "ok": True}

    def finish(self, branch: str, action: str, base: str) -> dict:
        return {"action": action, "ok": self._finish_ok, "detail": "stub"}

    def worktree(self, branch: str, base: str) -> dict:
        return {"path": f"/tmp/wt-{branch}", "branch": branch, "base": base, "ok": True}

    def run(self, command: str, cwd: str) -> dict:
        return {"returncode": 0, "output": "stub output"}

    def remote_exists(self, branch: str, remote: str = "origin") -> dict:
        return {"exists": True, "sha": "abc123", "ok": True, "detail": ""}


def _make_engine(vcs=None):
    return Engine(tempfile.mktemp(suffix=".db"),
                  vcs_backend=vcs or _StubVCS())


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    e = _make_engine()
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("branch acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


def _unwrap(res):
    return res.get("result", res) if isinstance(res, dict) else res


def _cs(engine, confirmed_intent, summary, paths=""):
    res, _ = invoke(engine, confirmed_intent, "branch", "commit_smart",
                    summary=summary, paths=paths)
    return _unwrap(res)


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


@given("a stub VCS that reports ahead 2 behind 0 dirty false", target_fixture="engine")
def _engine_ahead():
    e = _make_engine(vcs=_StubVCS(ahead=2, behind=0, dirty=False))
    return e


@given("a stub VCS that reports ahead 1 behind 3 dirty false", target_fixture="engine")
def _engine_behind():
    return _make_engine(vcs=_StubVCS(ahead=1, behind=3, dirty=False))


@given("a stub VCS that reports ahead 1 behind 0 dirty true", target_fixture="engine")
def _engine_dirty():
    return _make_engine(vcs=_StubVCS(ahead=1, behind=0, dirty=True))


@given("a stub VCS that reports ahead 0 behind 0 dirty false", target_fixture="engine")
def _engine_nothing():
    return _make_engine(vcs=_StubVCS(ahead=0, behind=0, dirty=False))


@given(parsers.parse('a stub VCS that succeeds for action "{action}"'), target_fixture="engine")
def _engine_finish_ok(action):
    return _make_engine(vcs=_StubVCS(ahead=1, finish_ok=True))


# ── commit_smart ──────────────────────────────────────────────────────────────

@when("I call commit_smart with summary \"add user profile page\" and no paths",
      target_fixture="cs")
def _cs_feat(engine, confirmed_intent):
    return _cs(engine, confirmed_intent, "add user profile page")


@then(parsers.parse('the message starts with "{prefix}"'))
def _message_prefix(cs, prefix):
    assert cs["message"].startswith(prefix), \
        f"message {cs['message']!r} doesn't start with {prefix!r}"


@then("the message contains \"add user profile page\"")
def _message_contains(cs):
    assert "add user profile page" in cs["message"]


@when("I call commit_smart with summary \"fix broken login redirect\" and no paths",
      target_fixture="cs")
def _cs_fix(engine, confirmed_intent):
    return _cs(engine, confirmed_intent, "fix broken login redirect")


@when("I call commit_smart with summary \"cover edge case\" and paths \"tests/test_foo.py,tests/test_bar.py\"",
      target_fixture="cs")
def _cs_test(engine, confirmed_intent):
    return _cs(engine, confirmed_intent, "cover edge case",
               paths="tests/test_foo.py,tests/test_bar.py")


@when("I call commit_smart with summary \"update readme\" and paths \"docs/index.md\"",
      target_fixture="cs")
def _cs_docs(engine, confirmed_intent):
    return _cs(engine, confirmed_intent, "update readme", paths="docs/index.md")


@when("I call commit_smart with summary \"extend analyze\" and paths \"agency/capabilities/analyze/_main.py\"",
      target_fixture="cs")
def _cs_scope(engine, confirmed_intent):
    return _cs(engine, confirmed_intent, "extend analyze",
               paths="agency/capabilities/analyze/_main.py")


@then(parsers.parse('the commit scope is "{scope}"'))
def _commit_scope(cs, scope):
    assert cs["scope"] == scope


@when("I call commit_smart with a very long summary", target_fixture="cs")
def _cs_long(engine, confirmed_intent):
    return _cs(engine, confirmed_intent, "a" * 200)


@then("the subject part of the message is at most 60 characters long")
def _subject_limit(cs):
    msg = cs["message"]
    subject = msg.split(": ", 1)[1] if ": " in msg else msg
    assert len(subject) <= 60


# ── assess ────────────────────────────────────────────────────────────────────

@when(parsers.parse('I call branch.assess for branch "{branch}" against base "{base}"'),
      target_fixture="assess_result")
def _assess_call(engine, branch, base):
    # Re-mint intent for the new engine (Given stubs replace the fixture)
    iid = engine.intent.capture("assess", "recommend", "verified")
    engine.intent.confirm(iid)
    res, _ = invoke(engine, iid, "branch", "assess", branch=branch, base=base)
    return _unwrap(res)


@then(parsers.parse('the recommended action is "{action}"'))
def _recommended(assess_result, action):
    assert assess_result["recommended"] == action


# ── finish ────────────────────────────────────────────────────────────────────

@when(parsers.parse('I call branch.finish with action "{action}"'),
      target_fixture="finish_result")
def _finish_call(engine, action):
    iid = engine.intent.capture("finish", "done", "verified")
    engine.intent.confirm(iid)
    res, _ = invoke(engine, iid, "branch", "finish",
                    branch="feature/test", action=action, base="main")
    return _unwrap(res), iid


@then("a BranchOutcome node is recorded")
def _outcome_recorded(engine, finish_result):
    res, iid = finish_result
    node = engine.memory.recall(res["outcome"])
    assert node is not None
    assert node.get("action") == "merge"


@then("the BranchOutcome SERVES the intent")
def _outcome_serves(engine, finish_result):
    res, iid = finish_result
    rows = engine.memory.g.query(
        "MATCH (o:BranchOutcome)-[:SERVES]->(i:Intent) WHERE o.id=$o AND i.id=$i RETURN o",
        {"o": res["outcome"], "i": iid})
    assert rows


@when("I call branch.finish with an unknown action", target_fixture="finish_bad")
def _finish_bad(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "branch", "finish",
                    branch="feature/test", action="obliterate", base="main")
    return _unwrap(res)


@then("the finish result carries an unknown-action error")
def _finish_error(finish_bad):
    assert "error" in finish_bad
