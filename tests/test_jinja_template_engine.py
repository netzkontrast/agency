"""Spec 388 — Jinja template engine: programmatic gates for all templates.

Behaviour for the owner directive (2026-06-23): *"install jinja Template Engine
and port all templates — let the gates be decided programmatically."* The
``ctx.render`` seam (``CapabilityContext.render``) renders through a Jinja
``Environment`` (``StrictUndefined``, autoescape off) so ``{% if %}`` / ``{% for %}``
/ ``{# #}`` are first-class — replacing the interim Spec 384 regex strippers in
``analyze/_report.py``. These map 1:1 to the spec's §Acceptance scenarios.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from agency.capability import CapabilityContext

pytestmark = pytest.mark.analyze

_REPO = Path(__file__).resolve().parents[1]
_TEMPLATE_GLOB = sorted(
    set((_REPO / "agency" / "capabilities").rglob("templates/**/*.md")))


def _ctx(body: str, name: str = "t") -> CapabilityContext:
    """A minimal context whose ``render`` only needs ``ontology.templates``."""
    return CapabilityContext(
        memory=None, ontology=SimpleNamespace(templates={name: body}),
        registry=None, intent_id="intent:test")


# ── Scenario: a template gate is decided programmatically ─────────────────────

def test_gate_decided_programmatically() -> None:
    body = "before\n{% if is_audit %}## Module Dependency Graph{% endif %}\nafter"
    assert "Module Dependency Graph" not in _ctx(body).render("t", is_audit=False)
    assert "Module Dependency Graph" in _ctx(body).render("t", is_audit=True)


# ── Scenario: a template loop renders a list ──────────────────────────────────

def test_loop_renders_list() -> None:
    body = "{% for f in findings %}- {{ f.title }}\n{% endfor %}"
    out = _ctx(body).render("t", findings=[{"title": "a"}, {"title": "b"}, {"title": "c"}])
    assert out.count("- ") == 3
    assert "- a" in out and "- c" in out


# ── Scenario: render-time comments are engine-stripped ────────────────────────

def test_jinja_comments_stripped() -> None:
    body = "keep{# this is a render-time note that must vanish #}done"
    out = _ctx(body).render("t")
    assert "render-time note" not in out
    assert "keep" in out and "done" in out


# ── Scenario: the interim Spec 384 strippers are gone ─────────────────────────

def test_interim_384_strippers_gone() -> None:
    from agency.capabilities.analyze import _report
    assert not hasattr(_report, "strip_conditionals")
    assert not hasattr(_report, "strip_comments")
    src = inspect.getsource(_report)
    # the regex strip machinery is gone — the engine evaluates the gates now
    assert "_COND_RE" not in src and "_COMMENT_RE" not in src
    assert "re.compile" not in src


def test_report_renders_purely_through_ctx_render() -> None:
    from agency.capabilities.analyze import _report
    src = inspect.getsource(_report.render_quality_report)
    # the verb passes `findings` to the template loop — no manual block-join
    assert 'join(blocks)' not in src
    assert "strip_conditionals" not in src and "strip_comments" not in src


# ── Scenario: every template is ported (parses as Jinja; no BEGIN IF) ─────────

def test_every_template_parses_as_jinja() -> None:
    from jinja2 import Environment
    env = Environment()
    failures = []
    for p in _TEMPLATE_GLOB:
        try:
            env.parse(p.read_text())
        except Exception as exc:  # noqa: BLE001 — collect all, report together
            failures.append(f"{p.relative_to(_REPO)}: {exc}")
    assert not failures, "templates failed to parse as Jinja:\n" + "\n".join(failures)


def test_no_begin_if_marker_remains() -> None:
    offenders = [str(p.relative_to(_REPO)) for p in _TEMPLATE_GLOB
                 if "BEGIN IF" in p.read_text()]
    assert not offenders, f"BEGIN IF marker still present in: {offenders}"


# ── Scenario: missing vars still fail loudly ──────────────────────────────────

def test_missing_var_raises() -> None:
    from jinja2.exceptions import UndefinedError
    with pytest.raises(UndefinedError):
        _ctx("{{ required }}").render("t")


# ── End-to-end: analyze.report renders the findings loop through the engine ────

def test_analyze_report_end_to_end_findings_loop() -> None:
    import tempfile
    from agency.engine import Engine

    e = Engine(tempfile.mktemp(suffix=".db"), _require_skill_doc=False)
    iid = e.intent.capture_and_confirm("t", "x", "x", owner="user")
    findings = [
        {"risk_code": "R1", "file": "a.py", "line": 1, "message": "m1",
         "consequence": "c1", "remedy": "r1"},
        {"risk_code": "R4", "file": "b.py", "line": 2, "message": "m2",
         "consequence": "c2", "remedy": "r2"},
        {"risk_code": "R5", "file": "c.py", "line": 3, "message": "m3",
         "consequence": "c3", "remedy": "r3"},
    ]
    res, _inv = e.registry.invoke(e.memory, iid, "analyze", "report",
                                  agent_id="agent:test", findings=findings, mode="review")
    content = res["content"]
    # three Iron-Law finding blocks, one per finding (loop in the template)
    assert content.count("Symptom:") == 3
    # render-time author comments never reach the output
    assert "<!-- AGENT:" not in content
    assert "{#" not in content
