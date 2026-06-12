"""Spec 075 — definable, discoverable shell-template registry.

Extends Spec 073's hardcoded `_TEMPLATES` seed into a DEFINABLE, graph-stored,
MCP-discoverable surface (CLAUDE.md #8 — no frozen dict). A named template bundles
a command + an output filter + a doc + tags; `shell.define` records one as an
Artefact, `shell.templates(query)` discovers built-ins ∪ graph templates, and
`shell.run(template=)` resolves graph templates first, then seeds.

Behaviour-first (no pinned counts): expectations computed from the live surface.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.capabilities.shell import _ALLOWED_TOOLS, _TEMPLATES
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
    iid = e.intent.capture("shell-templates", "definable registry", "define/run/query")
    e.intent.confirm(iid)
    return e, iid


def _call(e, iid, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, "shell", verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


# --- define → run round trip --------------------------------------------------

def test_define_then_run_round_trip():
    """A defined template dispatches its command and applies its filter."""
    runner = _StubRunner(stdout="a\nb\nc\nd\ne")
    e, iid = _engine(runner)
    try:
        d = _call(e, iid, "define", name="last2", command="git log",
                  filter="tail:2", doc="last two", tags="git history")
        assert d.get("template_id")
        out = _call(e, iid, "run", template="last2")
        assert out["template"] == "last2"
        assert out["lines"] == 2 and out["output"] == "d\ne"   # the template's tail:2
        assert runner.calls[0][0] == "git"                      # the template's command ran
    finally:
        e.memory.close()


def test_define_is_discoverable_via_query():
    """A graph template surfaces through `templates(query)` matched on
    name / doc / tags, marked source='graph'."""
    e, iid = _engine(_StubRunner())
    try:
        _call(e, iid, "define", name="audit-log", command="git log --oneline",
              filter="head:5", doc="recent history audit", tags="git review")
        # query by a tag token
        hits = _call(e, iid, "templates", query="review")
        names = {t["name"] for t in hits}
        assert "audit-log" in names
        match = next(t for t in hits if t["name"] == "audit-log")
        assert match["source"] == "graph"
        # a query that matches nothing returns no hits
        assert _call(e, iid, "templates", query="zzz-nomatch") == []
    finally:
        e.memory.close()


def test_graph_template_overrides_seed():
    """Defining a template whose name collides with a SEED makes the graph
    version win in both discovery and run resolution."""
    seed_name = sorted(_TEMPLATES)[0]
    runner = _StubRunner(stdout="x\ny")
    e, iid = _engine(runner)
    try:
        _call(e, iid, "define", name=seed_name, command="echo overridden",
              filter="full", doc="graph override", tags="")
        # run resolves the graph command, not the seed's
        _call(e, iid, "run", template=seed_name)
        assert runner.calls[0][:2] == ["echo", "overridden"]
        # discovery shows ONE entry for the name, sourced from the graph
        allt = _call(e, iid, "templates")
        entries = [t for t in allt if t["name"] == seed_name]
        assert len(entries) == 1 and entries[0]["source"] == "graph"
    finally:
        e.memory.close()


def test_define_rejects_non_allowlisted_command():
    """`define` enforces the same first-token allowlist as `run` — a template
    can never smuggle an un-allowlisted tool into the registry."""
    e, iid = _engine(_StubRunner())
    try:
        out = _call(e, iid, "define", name="evil", command="rm -rf /", filter="full")
        assert "error" in out
        assert "rm" not in _ALLOWED_TOOLS
        # nothing was recorded
        assert _call(e, iid, "templates", query="evil") == []
    finally:
        e.memory.close()


def test_redefine_supersedes():
    """Re-defining a name supersedes the prior version: discovery shows one
    current entry (the latest command), and the graph carries SUPERSEDED_BY."""
    e, iid = _engine(_StubRunner())
    try:
        _call(e, iid, "define", name="dup", command="git status", filter="full")
        _call(e, iid, "define", name="dup", command="git diff", filter="tail:5")
        entries = [t for t in _call(e, iid, "templates") if t["name"] == "dup"]
        assert len(entries) == 1
        assert entries[0]["command"] == "git diff"
        rows = e.memory.g.query(
            "MATCH (a:Artefact)-[:SUPERSEDED_BY]->(b:Artefact) RETURN b")
        assert rows, "redefine must leave a SUPERSEDED_BY trail"
    finally:
        e.memory.close()


def test_empty_query_returns_seeds_and_graph():
    """`templates()` with no query returns the union of seeds + graph
    templates (the full surface)."""
    e, iid = _engine(_StubRunner())
    try:
        _call(e, iid, "define", name="mine", command="ls", filter="full")
        allt = _call(e, iid, "templates")
        names = {t["name"] for t in allt}
        assert "mine" in names                       # graph
        assert set(_TEMPLATES).issubset(names)       # every seed present
    finally:
        e.memory.close()


def test_define_serves_intent_for_provenance():
    """The recorded command-template Artefact SERVES the intent — the
    definition is auditable provenance."""
    e, iid = _engine(_StubRunner())
    try:
        d = _call(e, iid, "define", name="prov", command="ls", filter="full")
        tid = d["template_id"]
        assert e.memory.g.query(
            "MATCH (a:Artefact)-[:SERVES]->(i:Intent) WHERE a.id=$a AND i.id=$i RETURN i",
            {"a": tid, "i": iid})
    finally:
        e.memory.close()


# --- Spec 280 — foreign-hook wrap moved out of `shell.run` --------------------
# Codex review on PR #138 round 2: `shell.run(hook_wrap=True)` was a P1
# allowlist bypass (any MCP/CLI caller with a valid intent could
# escape `_ALLOWED_TOOLS`). The wrap moved to a dedicated `agency hook
# wrap` CLI subcommand that doesn't require an intent + preserves
# stdin/stdout/stderr. See `tests/test_hooks_install.py` for the wrap
# behavior; this test asserts the allowlist STAYS in force on the
# public `shell.run` surface (regression invariant).

def test_shell_run_allowlist_still_in_force_on_public_surface():
    """Regression after the Spec 280 round-2 removal of `hook_wrap`:
    the public `shell.run` surface remains allowlist-gated for ALL
    callers. Non-allowlisted tools are rejected (Spec 073 boundary)."""
    runner = _StubRunner()
    e, iid = _engine(runner)
    try:
        out = _call(e, iid, "run", command="/usr/local/bin/audit.sh")
        assert "error" in out
        assert "not allowlisted" in out["error"]
        assert runner.calls == []                                  # never ran
    finally:
        e.memory.close()
