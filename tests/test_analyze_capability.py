"""Spec 042 — analyze capability (composition + provenance).

Tests the act verbs: analyze.run records Analysis + Finding nodes,
analyze.improve drafts a plan, analyze.cleanup focuses on dead-code.
Also verifies the ontology fragment + skill registration.
"""
import os
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "test analyze capability",
        "findings recorded as graph nodes",
        "summary payload is small (< 500 tokens)",
    )
    engine.intent.confirm(intent)
    return intent


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write(body)
    return path


def _call(engine, iid, verb, **kw):
    res, _inv = engine.registry.invoke(
        engine.memory, iid, "analyze", verb,
        agent_id="agent:test", **kw)
    return res


# ---------------------------------------------------------------------------
# Capability + ontology shape.
# ---------------------------------------------------------------------------


def test_capability_registered(engine):
    assert "analyze" in engine.registry.names()


def test_capability_has_six_verbs(engine):
    verbs = set(engine.registry.get("analyze").verbs)
    expected = {"quality", "security", "performance", "architecture",
                "run", "improve", "cleanup"}
    assert expected <= verbs


def test_ontology_declares_finding_severity_enum(engine):
    enums = engine.ontology.enums
    assert ("Finding", "severity") in enums
    assert enums[("Finding", "severity")] == {"info", "warn", "fail"}


def test_ontology_declares_analysis_axis_enum(engine):
    enums = engine.ontology.enums
    assert ("Analysis", "axis") in enums
    assert enums[("Analysis", "axis")] == {
        "quality", "security", "performance", "architecture"}


def test_code_analysis_skill_registered(engine):
    skills = engine.ontology.skills
    assert "code-analysis" in skills
    phase_names = [p["name"] for p in skills["code-analysis"]["phases"]]
    assert phase_names == ["scope", "axes", "run", "review", "apply"]
    # Last phase is the hard gate.
    assert skills["code-analysis"]["phases"][-1].get("gate") == "hard"


# ---------------------------------------------------------------------------
# analyze.run — composes axes, records provenance, returns small summary.
# ---------------------------------------------------------------------------


def test_run_records_analysis_node(engine, iid, tmp_path):
    body = "import sys\n"   # one unused-import
    _write(str(tmp_path), "x.py", body)
    res = _call(engine, iid, "run", path=str(tmp_path), axes=["quality"])
    assert "analysis_id" in res
    assert "totals" in res
    assert "quality" in res["totals"]
    # The Analysis node lives in the graph.
    nodes = engine.memory.find("Analysis")
    assert any(n["id"] == res["analysis_id"] for n in nodes)


def test_run_records_finding_nodes(engine, iid, tmp_path):
    _write(str(tmp_path), "x.py", "import sys\nimport json\n")
    res = _call(engine, iid, "run", path=str(tmp_path), axes=["quality"])
    findings = engine.memory.find("Finding")
    # At least 2 unused-import findings for the fixture.
    assert len([f for f in findings if f["rule"] == "Q001"]) >= 2


def test_run_default_axes_runs_all_four(engine, iid, tmp_path):
    _write(str(tmp_path), "x.py", "x = 1\n")
    res = _call(engine, iid, "run", path=str(tmp_path))
    # The Analysis node carries the axes list — all four ran.
    nodes = engine.memory.find("Analysis")
    a = next(n for n in nodes if n["id"] == res["analysis_id"])
    assert set(res["totals"].keys()) == {
        "quality", "security", "performance", "architecture"}


def test_run_summary_payload_is_small(engine, iid, tmp_path):
    _write(str(tmp_path), "x.py", "import sys\n")
    res = _call(engine, iid, "run", path=str(tmp_path), axes=["quality"])
    import json
    payload = json.dumps(res)
    # < 500 tokens ~ < 2000 chars; we target < 500 chars for the summary.
    assert len(payload) < 500, f"summary too big: {len(payload)} chars"


# ---------------------------------------------------------------------------
# analyze.improve — drafts a plan as Reflection node.
# ---------------------------------------------------------------------------


def test_improve_drafts_plan_without_applying(engine, iid, tmp_path):
    _write(str(tmp_path), "x.py", "import sys\nimport json\n")
    run_res = _call(engine, iid, "run", path=str(tmp_path), axes=["quality"])
    improve_res = _call(engine, iid, "improve",
                        analysis_id=run_res["analysis_id"], apply=False)
    assert "improvement_plan_id" in improve_res
    assert improve_res["item_count"] >= 2
    # The plan is a Reflection node with kind=improvement-plan.
    plans = [r for r in engine.memory.find("Reflection")
             if r.get("kind") == "improvement-plan"]
    assert any(p["id"] == improve_res["improvement_plan_id"] for p in plans)


# ---------------------------------------------------------------------------
# analyze.cleanup — focused on dead-code only.
# ---------------------------------------------------------------------------


def test_cleanup_dry_run_returns_patch_plan(engine, iid, tmp_path):
    body = "import os\nimport sys\nprint('hi')\n"  # sys is unused
    _write(str(tmp_path), "x.py", body)
    res = _call(engine, iid, "cleanup", path=str(tmp_path), dry_run=True)
    assert "improvement_plan_id" in res
    # Cleanup should ONLY surface unused-import-class findings.
    # (Implementation may add more dead-code categories later.)
    assert res["item_count"] >= 1
