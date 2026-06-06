"""Spec 022 — Jules events surface through the engine monitor channel.

First real consumer of Spec 021's single `agency-engine` monitor surface. The
Jules watcher's classified transitions + the dispatch/recover/verify verbs each
fan a `MonitorEvent` into `.agency/monitor.log` (the SIDE-CHANNEL to the
per-intent queue), so a Claude Code session sees Jules state changes live
without a polling loop — and WITHOUT a second monitors.json entry.
"""
from __future__ import annotations

import json
import tempfile

import pytest

from agency.capabilities.jules.watch import INSTRUCTIONS, Watcher
from agency.engine import Engine


class _StubClient:
    """Minimal Jules backend — only `create` matters for these tests."""

    def create(self, **kw):
        return {"id": "sessions/abc", "state": "QUEUED",
                "title": kw.get("title", ""), "url": "https://jules.google.com/session/abc"}


class _StubVCS:
    """git boundary that reports the branch is NOT on the remote (silent fail)."""

    def remote_exists(self, branch, remote="origin"):
        return {"ok": True, "exists": False, "sha": ""}


def _records(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.fixture
def monitor_log(tmp_path, monkeypatch):
    p = tmp_path / "monitor.log"
    monkeypatch.setenv("AGENCY_MONITOR_LOG", str(p))
    return p


@pytest.fixture
def engine(monitor_log):
    return Engine(tempfile.mktemp(suffix=".db"),
                  jules_client=_StubClient(), vcs_backend=_StubVCS())


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("jules monitor", "events surface live", "lines land in monitor.log")
    engine.intent.confirm(i)
    return i


# --- watcher transition (the per-transition side-channel) ---------------------

def test_watcher_transition_emits_and_keeps_queue(engine, iid, monitor_log):
    w = Watcher()
    w.engine = engine
    sinfo = {"intent_id": iid, "last_state": {"state": "IN_PROGRESS"}}
    event = {"action": "verify_pr", "session": "sessions/abc", "state": "COMPLETED",
             "instruction": INSTRUCTIONS["verify_pr"]}
    # both channels fire on the same transition
    w._put_event(iid, event)          # the existing programmatic queue
    w._emit_monitor(sinfo, event)     # the Spec 022 live side-channel
    assert not w._get_queue(iid).empty()          # queue still carries the event
    recs = _records(monitor_log)
    assert len(recs) == 1
    rec = recs[0]
    assert rec["source"] == "jules" and rec["kind"] == "verify_pr"
    assert rec["intent_id"] == iid
    assert "IN_PROGRESS→COMPLETED" in rec["message"]


def test_watcher_noop_does_not_emit(engine, iid, monitor_log):
    w = Watcher()
    w.engine = engine
    w._emit_monitor({"intent_id": iid, "last_state": {"state": "PLANNING"}},
                    {"action": "noop", "session": "s", "state": "PLANNING",
                     "instruction": INSTRUCTIONS["noop"]})
    assert _records(monitor_log) == []  # heartbeat/same-state noise is filtered (OQ#1)


def test_watcher_emit_noop_without_engine():
    w = Watcher()  # no engine attached
    w._emit_monitor({"intent_id": "i", "last_state": None},
                    {"action": "verify_pr", "session": "s", "state": "COMPLETED",
                     "instruction": "x"})  # must not raise


# --- verb-level emits ---------------------------------------------------------

def test_dispatch_emits_dispatched(engine, iid, monitor_log):
    engine.registry.invoke(engine.memory, iid, "jules", "dispatch",
                           source="o/r", starting_branch="main", prompt="do x", title="T")
    disp = [r for r in _records(monitor_log) if r["kind"] == "dispatched"]
    assert disp and disp[0]["source"] == "jules"
    assert disp[0]["intent_id"] == iid
    assert "title=T" in disp[0]["message"]


def test_recover_emits_recovery_started(engine, iid, monitor_log):
    engine._jules_watcher = Watcher()  # recover promotes into the watcher tracker
    engine.registry.invoke(engine.memory, iid, "jules", "recover", session="sessions/abc")
    rec = [r for r in _records(monitor_log) if r["kind"] == "recovery_started"]
    assert rec and "recovery" in rec[0]["message"]
    assert rec[0]["intent_id"] == iid


def test_verify_emits_silent_fail_detected(engine, iid, monitor_log):
    engine.registry.invoke(engine.memory, iid, "jules", "verify",
                           state="COMPLETED", branch="feat-x")
    sf = [r for r in _records(monitor_log) if r["kind"] == "silent_fail_detected"]
    assert sf and "feat-x" in sf[0]["message"]
    assert sf[0]["intent_id"] == iid


def test_verify_no_silent_fail_when_not_completed(engine, iid, monitor_log):
    # An in-progress session whose branch isn't pushed yet is NORMAL — gating
    # the alert on COMPLETED avoids false recovery alerts (PR #20 review).
    engine.registry.invoke(engine.memory, iid, "jules", "verify",
                           state="IN_PROGRESS", branch="feat-x")
    assert [r for r in _records(monitor_log) if r["kind"] == "silent_fail_detected"] == []


def test_recovery_outcome_emits_via_st_shape(engine, iid, monitor_log):
    # The recovery loop carries an `st` dict (intent_id, no last_state); the
    # mirrored emit must handle that shape (PR #20 review — recovery live too).
    w = Watcher()
    w.engine = engine
    w._emit_monitor({"intent_id": iid},
                    {"action": "recover_apply_plan", "session": "sessions/abc",
                     "state": "COMPLETED", "instruction": "apply the patch"})
    recs = [r for r in _records(monitor_log) if r["kind"] == "recover_apply_plan"]
    assert recs and recs[0]["intent_id"] == iid
    assert "sessions/abc" in recs[0]["message"]


def test_emit_monitor_is_best_effort_on_write_failure(engine, iid):
    # A failing monitor write must NOT surface out of a load-bearing verb like
    # jules.dispatch (the remote session already exists — a raised error could
    # trigger a duplicate retry). PR #20 review.
    class _Boom:
        def emit(self, ev):
            raise OSError("disk full")

    engine.monitor = _Boom()
    out, _ = engine.registry.invoke(engine.memory, iid, "jules", "dispatch",
                                    source="o/r", starting_branch="main",
                                    prompt="x", title="T")
    assert out["session"] == "sessions/abc"  # dispatch succeeded despite the failing monitor


# --- the hard constraint: no second monitor surface --------------------------

def test_install_still_has_exactly_one_monitor_entry():
    from agency.install import generate
    e = Engine(":memory:")
    try:
        files = generate(e)
    finally:
        e.memory.close()
    entries = json.loads(files["monitors/monitors.json"])
    assert len(entries) == 1 and entries[0]["name"] == "agency-engine"
