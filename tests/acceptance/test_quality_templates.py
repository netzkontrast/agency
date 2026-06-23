"""Acceptance — Spec 384: brooks prose → agency templates + references.

The prose half of the Spec 379 port lands on agency's template doctrine (Spec 060
`<!-- AGENT: -->` render assets) + the on-demand reference surface
(`develop.reference`). The mode walk-guides DERIVE their ordered steps from
review-chain.json (rule 2 — single source), so their `doc-source` is that agency
file. Output templates (report + iron-law finding) live with the finding engine in
analyze/; walk guides + remedy live with the mode skills in develop/.
"""
from __future__ import annotations

from pathlib import Path

import agency.capabilities.analyze._main as analyze_main
import agency.capabilities.develop._main as develop_main
from agency.capabilities.develop._main import DEV_SKILLS
from conftest import invoke

_ANALYZE_TPL = Path(analyze_main.__file__).parent / "templates"
_DEVELOP_TPL = Path(develop_main.__file__).parent / "templates"

# The quality modes are DERIVED from the live skill set (rule 8) — the `quality-*`
# disciplines develop registers — not a pinned list.
_QUALITY_MODES = sorted(s[len("quality-"):] for s in DEV_SKILLS
                        if s.startswith("quality-"))


def _agent_block(text: str) -> bool:
    return "<!-- AGENT:" in text


# ── §3 the six mode walk templates ────────────────────────────────────────────

def test_every_quality_mode_has_a_walk_template():
    """AGENCY-DRIFT: quality-templates — the develop/templates/quality-{mode}.md set
    must cover EXACTLY the live quality-* skill set (a 7th mode skill without its
    template, or vice-versa, is drift)."""
    assert _QUALITY_MODES, "no quality-* skills registered"
    template_modes = sorted(p.stem[len("quality-"):]
                            for p in _DEVELOP_TPL.glob("quality-*.md")
                            if p.stem != "quality-remedy")
    assert set(_QUALITY_MODES) <= set(template_modes), (
        f"modes missing a walk template: {set(_QUALITY_MODES) - set(template_modes)}")


def test_each_mode_template_carries_agent_block_and_doc_source():
    for mode in _QUALITY_MODES:
        body = (_DEVELOP_TPL / f"quality-{mode}.md").read_text(encoding="utf-8")
        assert _agent_block(body), f"quality-{mode}.md missing an <!-- AGENT: --> block"
        # derives from review-chain.json → that is its drift-tracked source (rule 2)
        assert "review-chain.json" in body, f"quality-{mode}.md not sourced to the chain"
        assert "doc-source:" in body, f"quality-{mode}.md missing a doc-source marker"


# ── §1/§2 the output templates (report + iron-law finding) ─────────────────────

def test_report_template_gates_the_audit_only_graph():
    body = (_ANALYZE_TPL / "quality-report.md").read_text(encoding="utf-8")
    assert _agent_block(body) and "doc-source:" in body
    # the Module Dependency Graph is audit-mode only — a BEGIN IF conditional
    assert "BEGIN IF is_audit" in body and "Module Dependency Graph" in body, body[:400]
    # the language rule travels WITH the template (Spec 384 §1)
    assert "Language rule" in body, "report template missing the language rule block"


def test_iron_law_finding_template_has_four_slots():
    body = (_ANALYZE_TPL / "iron-law-finding.md").read_text(encoding="utf-8")
    assert "doc-source:" in body and _agent_block(body)
    for slot in ("$symptom", "$source", "$consequence", "$remedy"):
        assert slot in body, f"iron-law-finding.md missing {slot}"


def test_remedy_template_exists_with_fix_tiers():
    body = (_DEVELOP_TPL / "quality-remedy.md").read_text(encoding="utf-8")
    assert _agent_block(body) and "doc-source:" in body
    assert "$fix_tier_label" in body  # the slot the iron-law template references


# ── §5 judgment prose as on-demand references ─────────────────────────────────

def test_quality_references_resolve(engine, iid):
    for topic in ("decay-risks", "source-coverage", "remedy", "custom-risks"):
        r, _ = invoke(engine, iid, "develop", "reference", topic=topic)
        assert "doc" in r["result"], (topic, r)
        assert r["result"]["doc"].strip(), f"{topic} reference is empty"


def test_computed_references_point_at_data_not_restate_it(engine, iid):
    """source-coverage + decay-risks are COMPUTED from the JSON (rule 2): they name
    the data file and render live from it, never a frozen copy."""
    r, _ = invoke(engine, iid, "develop", "reference", topic="source-coverage")
    assert "source-coverage.json" in r["result"]["doc"]
    # and it reflects the live book registry
    from agency.capabilities.analyze import _coverage
    books = _coverage.load_source_coverage()
    assert any(b.split(" — ")[0] in r["result"]["doc"] for b in books), "no live book listed"


def test_quality_references_are_discoverable(engine, iid):
    r, _ = invoke(engine, iid, "develop", "reference", topic="__nope__")
    avail = set(r["result"]["available"])
    assert {"decay-risks", "source-coverage", "remedy", "custom-risks"} <= avail, avail
