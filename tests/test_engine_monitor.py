"""Spec 021 — engine monitor channel.

One file-backed event stream; many capability emitters fan in (same shape as
``search/get_schema/execute`` exposing ONE wire surface for N tools). These
tests pin the substrate contract: ``MonitorEvent`` (frozen + JSON-line
serializable), ``MonitorEmitter`` (append-only JSONL + 1 MB rotation + atomic
append byte budget), ``Engine.monitor`` ownership, the
``CapabilityContext.emit_monitor`` sugar, and the single ``monitors.json``
install entry.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time

import pytest

from agency._monitor import (
    MonitorEmitter,
    MonitorEvent,
    resolve_monitor_log_path,
)


def test_monitor_event_json_roundtrip():
    ev = MonitorEvent(
        source="jules", kind="state_transition",
        message="session abc -> COMPLETED", intent_id="intent:1", ts=123.0,
    )
    line = ev.to_json()
    assert "\n" not in line  # single-line guarantee (tail -F delivers one line per event)
    assert MonitorEvent.from_json(line) == ev


def test_emitter_appends_jsonl(tmp_path):
    log = tmp_path / "monitor.log"
    em = MonitorEmitter(str(log))
    em.emit(MonitorEvent("engine", "info", "first"))
    em.emit(MonitorEvent("delegate", "fanout_complete", "second"))
    lines = log.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["message"] == "first"
    assert json.loads(lines[1])["kind"] == "fanout_complete"


def test_emit_autofills_ts_when_zero(tmp_path):
    log = tmp_path / "monitor.log"
    before = time.time()
    MonitorEmitter(str(log)).emit(MonitorEvent("engine", "info", "x"))  # ts defaults to 0.0
    assert json.loads(log.read_text().splitlines()[0])["ts"] >= before


def test_rotation_at_threshold_overwrites_dot1(tmp_path):
    log = tmp_path / "monitor.log"
    em = MonitorEmitter(str(log), rotate_bytes=200)
    (tmp_path / "monitor.log.1").write_text("OLD")  # seed to prove overwrite
    for i in range(50):
        em.emit(MonitorEvent("engine", "info", f"event-{i}-padding-padding"))
    assert (tmp_path / "monitor.log.1").exists()
    assert (tmp_path / "monitor.log.1").read_text() != "OLD"  # overwritten, not appended
    assert log.stat().st_size < 200 * 4  # live file stays bounded near threshold


def test_event_line_stays_within_atomic_budget(tmp_path):
    log = tmp_path / "monitor.log"
    MonitorEmitter(str(log)).emit(MonitorEvent("engine", "info", "M" * 10_000))
    line = log.read_text().splitlines()[0]
    assert len(line.encode("utf-8")) <= 4096  # POSIX atomic-append guarantee
    assert json.loads(line)["source"] == "engine"  # still valid JSON after truncation


def test_atomic_budget_holds_after_json_escaping(tmp_path):
    # Escapable chars (quotes/backslashes) ~double under json.dumps; truncation
    # must measure the SERIALIZED line, not the raw message bytes.
    log = tmp_path / "monitor.log"
    for msg in ('"' * 10_000, "\\" * 10_000, "\n" * 10_000):
        MonitorEmitter(str(log)).emit(MonitorEvent("engine", "warning", msg))
    for line in log.read_text().splitlines():
        assert len(line.encode("utf-8")) <= 4096  # holds post-escaping
        assert json.loads(line)["kind"] == "warning"  # still parseable


def test_resolve_path_prefers_explicit_then_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_MONITOR_LOG", str(tmp_path / "from-env.log"))
    assert resolve_monitor_log_path(explicit=str(tmp_path / "x.log")) == str(tmp_path / "x.log")
    assert resolve_monitor_log_path() == str(tmp_path / "from-env.log")


def test_resolve_path_sibling_of_db(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENCY_MONITOR_LOG", raising=False)
    db = tmp_path / ".agency" / "session.db"
    assert resolve_monitor_log_path(db_path=str(db)) == str(tmp_path / ".agency" / "monitor.log")


def test_engine_owns_monitor(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_MONITOR_LOG", str(tmp_path / "monitor.log"))
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        assert isinstance(e.monitor, MonitorEmitter)
    finally:
        e.memory.close()


def test_capability_context_emit_monitor_autofills(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_MONITOR_LOG", str(tmp_path / "monitor.log"))
    from agency.capability import CapabilityContext
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        ctx = CapabilityContext(
            memory=e.memory, ontology=e.ontology, registry=e.registry,
            intent_id="intent:42", engine=e,
        )
        ctx.emit_monitor("jules", "recovery", "recovered session")
        rec = json.loads((tmp_path / "monitor.log").read_text().splitlines()[0])
        assert rec["intent_id"] == "intent:42"  # auto-filled from ctx
        assert rec["source"] == "jules" and rec["kind"] == "recovery"
        assert rec["ts"] > 0  # auto-filled
    finally:
        e.memory.close()


def test_emit_monitor_noop_without_engine():
    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=None, ontology=None, registry=None, intent_id="i", engine=None,
    )
    ctx.emit_monitor("x", "info", "noop")  # must not raise when no monitor attached


def test_install_generates_single_monitor_entry():
    from agency.engine import Engine
    from agency.install import generate
    e = Engine(":memory:")
    try:
        files = generate(e)
    finally:
        e.memory.close()
    assert "monitors/monitors.json" in files, sorted(files)
    entries = json.loads(files["monitors/monitors.json"])
    assert isinstance(entries, list) and len(entries) == 1
    assert entries[0]["name"] == "agency-engine"
    assert "monitor.log" in entries[0]["command"]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="tail -F is POSIX-only")
def test_tail_f_delivers_one_line_per_event(tmp_path):
    log = tmp_path / "monitor.log"
    log.write_text("")
    em = MonitorEmitter(str(log))
    proc = subprocess.Popen(
        ["tail", "-n", "0", "-F", str(log)],
        stdout=subprocess.PIPE, text=True,
    )
    try:
        time.sleep(0.3)  # let tail attach before the write
        em.emit(MonitorEvent("engine", "info", "live-event"))
        line = proc.stdout.readline()  # blocks until the appended line arrives
        assert line.strip()
        assert json.loads(line)["message"] == "live-event"
    finally:
        proc.terminate()
        proc.wait(timeout=5)
