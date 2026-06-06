"""Spec 073 — `shell`: token-efficient, recorded, templated host-command boundary.

Behaviour-first (no hardcoded counts): run an allowlisted command/template, filter
the output to cut tokens, record provenance, reject non-allowlisted tools; plus a
pure `filter` verb (hook-ready). Expectations are computed from the live
capability, not pinned, so the suite doesn't gate a fixed surface.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.capabilities.shell import _ALLOWED_TOOLS, _apply_filter
from agency.engine import Engine


class _StubRunner:
    def __init__(self, stdout="", exit_code=0, stderr=""):
        self.stdout, self.exit_code, self.stderr = stdout, exit_code, stderr
        self.calls = []

    def run(self, argv, timeout=600):
        self.calls.append(list(argv))
        return {"exit_code": self.exit_code, "stdout": self.stdout,
                "stderr": self.stderr, "duration_s": 0.1}


def _engine(runner):
    e = Engine(tempfile.mktemp(suffix=".db"), runner=runner)
    iid = e.intent.capture("shell", "filtered recorded exec", "provenance + small delta")
    e.intent.confirm(iid)
    return e, iid


def _call(e, iid, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, "shell", verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def _has_edge(e, src, dst, rel):
    return bool(e.memory.g.query(
        f"MATCH (a)-[:{rel}]->(b) WHERE a.id=$a AND b.id=$b RETURN b", {"a": src, "b": dst}))


# --- pure filter (the token-economy core; hook-ready) -------------------------

@pytest.mark.parametrize("spec,text,expected", [
    ("tail:2", "a\nb\nc\nd", "c\nd"),
    ("head:2", "a\nb\nc\nd", "a\nb"),
    ("grep:ERR", "ok\nERR x\nfine\nERR y", "ERR x\nERR y"),
    ("lines:2-3", "a\nb\nc\nd", "b\nc"),
    ("count", "a\n\nb\nc", "3"),
    ("last", "a\nb\n\n", "b"),
    ("full", "a\nb", "a\nb"),
])
def test_apply_filter_slices(spec, text, expected):
    assert _apply_filter(text, spec) == expected


def test_filter_verb_trims_without_executing():
    e, iid = _engine(_StubRunner())
    try:
        out = _call(e, iid, "filter", text="\n".join(f"line{i}" for i in range(100)), spec="tail:3")
        assert out["lines"] == 3 and out["output"].endswith("line99")
    finally:
        e.memory.close()


# --- run: allowlist + filtered output + provenance ----------------------------

def test_run_allowlisted_filters_and_records():
    runner = _StubRunner(stdout="\n".join(f"row{i}" for i in range(500)))
    e, iid = _engine(runner)
    try:
        out = _call(e, iid, "run", command="ls -la", filter="tail:5")
        assert out["exit_code"] == 0 and out["lines"] == 5      # filtered, not 500 rows
        assert runner.calls[0][0] == "ls"
        node = e.memory.recall(out["run_id"])
        assert node["kind"] == "command-run" and node["tool"] == "ls"
        assert _has_edge(e, out["run_id"], iid, "SERVES")
        assert _has_edge(e, out["run_id"], iid, "OBSERVED_DURING")
    finally:
        e.memory.close()


def test_run_rejects_non_allowlisted_tool():
    runner = _StubRunner()
    e, iid = _engine(runner)
    try:
        out = _call(e, iid, "run", command="rm -rf /")
        assert "error" in out and not runner.calls        # NEVER executed
        assert "rm" not in _ALLOWED_TOOLS                  # the allowlist excludes it
    finally:
        e.memory.close()


def test_run_via_template_uses_its_command_and_filter():
    runner = _StubRunner(stdout="a\nFAILED test_x\nb\nFAILED test_y")
    e, iid = _engine(runner)
    try:
        out = _call(e, iid, "run", template="test-failures")
        assert out["template"] == "test-failures"
        # the template's grep:FAILED filter kept only the failures
        assert all("FAILED" in ln for ln in out["output"].splitlines())
        # the command actually dispatched was the template's command
        assert runner.calls, "template did not dispatch a command"
    finally:
        e.memory.close()


def test_run_unknown_template_errors():
    e, iid = _engine(_StubRunner())
    try:
        out = _call(e, iid, "run", template="does-not-exist")
        assert "error" in out and "templates" in out
    finally:
        e.memory.close()


def test_templates_listed_for_discovery():
    e, iid = _engine(_StubRunner())
    try:
        out = _call(e, iid, "templates")
        names = {t["name"] for t in out}
        assert "tests" in names and all("command" in t and "doc" in t for t in out)
    finally:
        e.memory.close()
