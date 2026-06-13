"""Spec 282 — error severity taxonomy.

Replays the exact failure scenarios mined from
``kohaerenzprotokoll/.agency/session.db`` (1952 invocations, 626 failed):
``create_scene`` rejected 513× on a closed ``pov`` enum (PERMANENT — never
succeeds) versus the known ``Failed to set property 'vfrom' on edge N``
contention (TRANSIENT — retry helps). The engine must tell them apart so a
caller stops retrying impossible calls.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine
from agency.toolresult import (
    Codes,
    Severity,
    ToolResult,
    classify_severity,
)
from agency._retry import retry_transient


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 282", "severity taxonomy", "verified")
    e.intent.confirm(iid)
    return iid


# ── 1-5: the classifier ────────────────────────────────────────────────

def test_invalid_argument_is_permanent() -> None:
    # replay create_scene: every failure was INVALID_ARGUMENT on the pov enum.
    assert classify_severity(Codes.INVALID_ARGUMENT) == Severity.PERMANENT


def test_enum_violation_message_is_permanent() -> None:
    msg = "pov='Erzähler (Vermittler-Stimme)' not in ['first', 'second']"
    assert classify_severity("INVALID_ARGUMENT", message=msg) == Severity.PERMANENT


def test_not_found_and_gate_are_permanent() -> None:
    assert classify_severity(Codes.NOT_FOUND) == Severity.PERMANENT
    assert classify_severity(Codes.GATE_FAILED) == Severity.PERMANENT


def test_graph_contention_exception_is_transient() -> None:
    exc = RuntimeError("Failed to set property 'vfrom' on edge 5")
    assert classify_severity("", exc=exc, message=str(exc)) == Severity.TRANSIENT


def test_unexpected_exception_is_fatal() -> None:
    assert classify_severity("", exc=KeyError("x")) == Severity.FATAL


def test_unknown_code_defaults_permanent() -> None:
    # documented default: the failure mode we fix is OVER-retrying, so an
    # unclassified failure is not retried.
    assert classify_severity("totally_unknown_code") == Severity.PERMANENT


# ── 6-7: TypedError / ToolResult carry severity ────────────────────────

def test_failure_classifies_severity_and_retryable() -> None:
    r = ToolResult.failure("INVALID_ARGUMENT", "bad pov")
    assert r.error.severity == Severity.PERMANENT
    assert r.error.retryable is False


def test_explicit_severity_overrides_classifier() -> None:
    r = ToolResult.failure("INVALID_ARGUMENT", "x", severity=Severity.TRANSIENT)
    assert r.error.severity == Severity.TRANSIENT
    assert r.error.retryable is True


# ── 8-9: Registry.invoke records severity on the Invocation ────────────

def _novel_with_chapter(e: Engine, iid: str) -> str:
    novel, _ = e.registry.invoke(e.memory, iid, "novel", "create_novel",
                                 title="K", author="A")
    ch, _ = e.registry.invoke(e.memory, iid, "novel", "create_chapter",
                              novel_id=novel["novel_id"], number=1, title="C")
    return ch["chapter_id"]


def test_invoke_records_permanent_for_bad_pov() -> None:
    e = _fresh()
    iid = _iid(e)
    cid = _novel_with_chapter(e, iid)
    data, inv = e.registry.invoke(
        e.memory, iid, "novel", "create_scene",
        chapter_id=cid, slug="s1",
        pov="Erzähler (Vermittler-Stimme, hypotaktisch-philosophisch)")
    assert data is None  # internal convention unchanged
    node = e.memory.recall(inv)
    assert node.get("outcome") == "failed"
    assert node.get("error_severity") == Severity.PERMANENT
    e.memory.close()


def test_invoke_records_transient_for_contention_exception() -> None:
    e = _fresh()
    iid = _iid(e)
    # register a probe verb that raises the known contention error.
    cap = e.registry._caps["novel"]

    def _boom(ctx):  # noqa: ANN001
        raise RuntimeError("Failed to set property 'vfrom' on edge 7")

    cap.verbs["_probe_contention"] = {
        "role": "effect", "fn": _boom, "inject": ["ctx"],
    }
    try:
        e.registry.invoke(e.memory, iid, "novel", "_probe_contention")
    except RuntimeError:
        pass
    # the most recent failed Invocation must be classified transient.
    rows = e.memory.g.query(
        "MATCH (i:Invocation) WHERE i.verb = $v RETURN i.error_severity AS s",
        {"v": "_probe_contention"})
    assert rows and rows[0]["s"] == Severity.TRANSIENT
    e.memory.close()


# ── 10: the wire surfaces a typed error (compat break) ─────────────────

def test_wire_surfaces_permanent_error_envelope() -> None:
    e = _fresh()
    iid = _iid(e)
    cid = _novel_with_chapter(e, iid)
    result, inv = e.registry.invoke(
        e.memory, iid, "novel", "create_scene",
        chapter_id=cid, slug="s1", pov="not-a-valid-pov")
    shaped = e._shape_wire_result(result, inv)
    assert shaped["ok"] is False
    err = shaped["error"]
    assert err["code"] == "INVALID_ARGUMENT"
    assert err["severity"] == Severity.PERMANENT
    assert err["retryable"] is False
    assert err["trace_id"] == inv
    assert "not-a-valid-pov" in err["message"]
    e.memory.close()


def test_wire_success_path_unchanged() -> None:
    e = _fresh()
    iid = _iid(e)
    result, inv = e.registry.invoke(e.memory, iid, "novel", "create_novel",
                                    title="K", author="A")
    shaped = e._shape_wire_result(result, inv)
    assert "error" not in shaped
    assert shaped.get("novel_id", "").startswith("novel:")
    e.memory.close()


# ── 11: retry_transient only retries transient ─────────────────────────

def test_retry_transient_calls_permanent_once() -> None:
    calls = {"n": 0}

    def call():
        calls["n"] += 1
        return {"ok": False, "error": {"severity": Severity.PERMANENT,
                                       "retryable": False}}

    out = retry_transient(call, attempts=4, sleep=lambda _s: None)
    assert calls["n"] == 1
    assert out["error"]["severity"] == Severity.PERMANENT


def test_retry_transient_retries_transient_to_limit() -> None:
    calls = {"n": 0}

    def call():
        calls["n"] += 1
        return {"ok": False, "error": {"severity": Severity.TRANSIENT,
                                       "retryable": True}}

    retry_transient(call, attempts=4, sleep=lambda _s: None)
    assert calls["n"] == 4


def test_retry_transient_returns_on_success() -> None:
    calls = {"n": 0}

    def call():
        calls["n"] += 1
        if calls["n"] < 3:
            return {"ok": False, "error": {"severity": Severity.TRANSIENT}}
        return {"ok": True, "scene_id": "scene:1"}

    out = retry_transient(call, attempts=8, sleep=lambda _s: None)
    assert calls["n"] == 3
    assert out["ok"] is True
