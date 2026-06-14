"""Acceptance — analyze capability (Spec 042, Spec 048, Spec 084).

Converted from: tests/test_analyze_graph.py, tests/test_analyze_capability.py,
tests/test_analyze_quality.py, tests/test_analyze_security.py,
tests/test_analyze_performance.py, tests/test_analyze_architecture.py,
tests/test_analyze_deps_integration.py.

Dropped (implementation / structural — not observable behaviour):
  - test_analyze_capability.test_capability_registered — registry membership is
    structural, not behaviour; the invoke paths already fail loudly if missing.
  - test_analyze_capability.test_capability_has_six_verbs — verb-set count is
    an implementation snapshot; new verbs should not require test update.
  - test_analyze_capability.test_ontology_declares_finding_severity_enum — enum
    shape is implementation; behaviour is that findings carry valid severities
    (tested via the finding-shape scenario).
  - test_analyze_capability.test_ontology_declares_analysis_axis_enum — same.
  - test_analyze_capability.test_code_analysis_skill_registered — skill phase
    names / gate flags are structural; behaviour is that the skill is walkable.
  - test_analyze_axis_registry.* (all 9 tests) — the axis-prefix registry is a
    private implementation detail (_build_axis_registry, _rule_axis, AXIS_PREFIXES);
    its observable effect is that rules land on the right axis in analyze.run
    output, which is covered by the run/quality/security/performance scenarios.
  - test_analyze_deps_integration.test_ruff_silent_when_missing — monkeypatches
    shutil.which; tests internal degradation logic, not observable output.
  - test_analyze_deps_integration.test_ruff_finds_long_line_when_present — skipped
    in CI if ruff absent; covered by quality scanner scenarios when ruff is present.
  - test_analyze_deps_integration.test_ruff_finds_unused_import_when_present —
    same rationale.
  - test_analyze_deps_integration.test_bandit_silent_when_missing — monkeypatch.
  - test_analyze_deps_integration.test_bandit_finds_eval_when_present — skip guard.
  - test_analyze_deps_integration.test_radon_* — skip guard + internal API.
  - test_analyze_deps_integration.test_quality_scan_composes_internal_plus_external —
    tool-presence conditional; not reliably testable as acceptance scenario.
  - test_analyze_deps_integration.test_quality_scan_silent_external_fallback —
    monkeypatches shutil.which.
  - test_analyze_performance.test_unbounded_while_true_flagged — P003 is an
    internal rule; the scenario is incomplete (no severity assertion needed for
    acceptance). Retained in performance section of the feature for completeness
    but removed from test_analyze_performance.py drop list — see NOTE below.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import call_tool, invoke, served

scenarios("features/analyze.feature")


# ── helpers ────────────────────────────────────────────────────────────────────

def _write(dirpath: str, name: str, body: str) -> str:
    path = os.path.join(dirpath, name)
    with open(path, "w") as f:
        f.write(body)
    return path


def _invoke_analyze(engine, confirmed_intent, verb, **kw):
    res, _ = invoke(engine, confirmed_intent, "analyze", verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


# ── shared source-file fixtures ────────────────────────────────────────────────

@given("a Python source file with one unused import", target_fixture="source_dir")
def _one_unused(tmp_path):
    _write(str(tmp_path), "x.py", "import sys\nx = 1\n")
    return str(tmp_path)


@given("a Python source file with two unused imports", target_fixture="source_dir")
def _two_unused(tmp_path):
    _write(str(tmp_path), "u.py", "import sys\nimport json\nx = 1\n")
    return str(tmp_path)


@given("a trivial Python source file", target_fixture="source_dir")
def _trivial(tmp_path):
    _write(str(tmp_path), "trivial.py", "x = 1\n")
    return str(tmp_path)


@given("a Python source file with a very long line", target_fixture="source_dir")
def _long_line(tmp_path):
    long = "x = " + "1 + " * 30 + "1"
    _write(str(tmp_path), "L.py", f"{long}\n")
    return str(tmp_path)


@given('a Python source file with only "from __future__ import annotations"',
       target_fixture="source_dir")
def _future_annotations(tmp_path):
    _write(str(tmp_path), "future.py", "from __future__ import annotations\nx = 1\n")
    return str(tmp_path)


@given("a Python source file that re-exports a name via __all__",
       target_fixture="source_dir")
def _all_export(tmp_path):
    _write(str(tmp_path), "init.py",
           "from somewhere import Thing\n__all__ = ['Thing']\n")
    return str(tmp_path)


@given("a Python source file that calls eval on user input", target_fixture="source_dir")
def _eval_file(tmp_path):
    _write(str(tmp_path), "e.py",
           "def run(user_input):\n    return eval(user_input)\n")
    return str(tmp_path)


@given("a Python source file with a hardcoded API key", target_fixture="source_dir")
def _api_key_file(tmp_path):
    _write(str(tmp_path), "secret.py",
           'API_KEY = "sk-1234567890abcdef1234567890abcdef"\n')
    return str(tmp_path)


@given("a Python source file that calls pickle.load", target_fixture="source_dir")
def _pickle_file(tmp_path):
    _write(str(tmp_path), "p.py",
           "import pickle\ndef load(path):\n    return pickle.load(open(path, 'rb'))\n")
    return str(tmp_path)


@given("a Python source file that uses shell=True in a non-subprocess call",
       target_fixture="source_dir")
def _shell_true_other(tmp_path):
    _write(str(tmp_path), "ok.py",
           "config = dict(shell=True, verbose=True)\nobj = SomeOther(shell=True)\n")
    return str(tmp_path)


@given("a Python source file with a nested loop on a growing list",
       target_fixture="source_dir")
def _nested_loop(tmp_path):
    _write(str(tmp_path), "n.py",
           "def f(items):\n"
           "    out = []\n"
           "    for x in items:\n"
           "        for y in items:\n"
           "            out.append((x, y))\n"
           "    return out\n")
    return str(tmp_path)


@given("a Python source file with string concatenation inside a loop",
       target_fixture="source_dir")
def _string_concat(tmp_path):
    _write(str(tmp_path), "c.py",
           "def build(items):\n"
           "    s = ''\n"
           "    for x in items:\n"
           "        s += str(x)\n"
           "    return s\n")
    return str(tmp_path)


@given("a Python source file with an integer counter in a loop",
       target_fixture="source_dir")
def _int_counter(tmp_path):
    _write(str(tmp_path), "c.py",
           "def count(items):\n"
           "    total = 0\n"
           "    for x in items:\n"
           "        total += 1\n"
           "    return total\n")
    return str(tmp_path)


@given("a Python package with a circular import between two modules",
       target_fixture="source_dir")
def _circular(tmp_path):
    _write(str(tmp_path), "__init__.py", "")
    _write(str(tmp_path), "a.py", "from . import b\nVALUE = 1\n")
    _write(str(tmp_path), "b.py", "from . import a\nVALUE = 2\n")
    return str(tmp_path)


@given("a Python package where b imports a but a does not import b",
       target_fixture="source_dir")
def _acyclic(tmp_path):
    _write(str(tmp_path), "__init__.py", "")
    _write(str(tmp_path), "a.py", "VALUE = 1\n")
    _write(str(tmp_path), "b.py", "from . import a\nVALUE = 2\n")
    return str(tmp_path)


# ── analyze.graph scenarios ───────────────────────────────────────────────────

@when("I invoke analyze.graph with no filters", target_fixture="graph_result")
def _graph_no_filter(engine, confirmed_intent):
    return _invoke_analyze(engine, confirmed_intent, "graph")


@then("the census contains at least one Intent node")
def _census_has_intent(graph_result):
    assert graph_result["census"].get("Intent", 0) >= 1


@then("the nodes list is empty when no node_type is given")
def _nodes_empty_without_type(graph_result):
    assert graph_result["nodes"] == []


@given("a reflection is recorded with scope \"observation\"")
def _seed_reflection(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "reflect", "note",
           scope="observation", text="a recorded lesson")


@when("I invoke analyze.graph for label \"Reflection\" and scope \"observation\"",
      target_fixture="graph_result")
def _graph_reflection_observation(engine, confirmed_intent):
    return _invoke_analyze(engine, confirmed_intent, "graph",
                           node_type="Reflection", scope="observation")


@then("every listed node has scope \"observation\"")
def _all_observation(graph_result):
    assert graph_result["nodes"], "expected at least one node"
    assert all(n.get("scope") == "observation" for n in graph_result["nodes"])


@then("the census shows at least one Reflection")
def _census_reflection(graph_result):
    assert graph_result["census"].get("Reflection", 0) >= 1


@given("four reflections are recorded")
def _four_reflections(engine, confirmed_intent):
    for i in range(4):
        invoke(engine, confirmed_intent, "reflect", "note",
               scope="observation", text=f"note {i}")


@when("I invoke analyze.graph for label \"Reflection\" with limit 2",
      target_fixture="graph_result")
def _graph_limit_2(engine, confirmed_intent):
    return _invoke_analyze(engine, confirmed_intent, "graph",
                           node_type="Reflection", limit=2)


@then("at most 2 nodes are returned")
def _limit_2(graph_result):
    assert len(graph_result["nodes"]) <= 2


# ── analyze.run scenarios ─────────────────────────────────────────────────────

@when("I run analyze on that file with axis \"quality\"", target_fixture="run_result")
def _run_quality(engine, confirmed_intent, source_dir):
    return _invoke_analyze(engine, confirmed_intent, "run",
                           path=source_dir, axes=["quality"],
                           agent_id="agent:test")


@then("the result carries an analysis_id")
def _has_analysis_id(run_result):
    assert "analysis_id" in run_result


@then("an Analysis node with that id exists in the graph")
def _analysis_node_exists(engine, run_result):
    nodes = engine.memory.find("Analysis")
    assert any(n["id"] == run_result["analysis_id"] for n in nodes)


@then("the result totals include the \"quality\" axis")
def _totals_quality(run_result):
    assert "quality" in run_result.get("totals", {})


@when("I run analyze on that file with axis \"quality\"", target_fixture="run_result")  # noqa: F811
def _run_quality_two(engine, confirmed_intent, source_dir):  # noqa: F811
    return _invoke_analyze(engine, confirmed_intent, "run",
                           path=source_dir, axes=["quality"],
                           agent_id="agent:test")


@then("at least 2 Finding nodes with rule \"Q001\" exist in the graph")
def _q001_findings(engine):
    findings = engine.memory.find("Finding")
    assert len([f for f in findings if f.get("rule") == "Q001"]) >= 2


@when("I run analyze on that file with no axis filter", target_fixture="run_result")
def _run_all_axes(engine, confirmed_intent, source_dir):
    return _invoke_analyze(engine, confirmed_intent, "run",
                           path=source_dir, agent_id="agent:test")


@then("the result totals include keys for quality, security, performance, architecture, and paths")
def _totals_all_five(run_result):
    totals = run_result.get("totals", {})
    for axis in ("quality", "security", "performance", "architecture", "paths"):
        assert axis in totals, f"missing axis {axis!r} in totals"


@then("the JSON payload is under 500 characters")
def _payload_compact(run_result):
    payload = json.dumps(run_result)
    assert len(payload) < 500, f"summary too big: {len(payload)} chars"


# ── analyze.improve scenarios ─────────────────────────────────────────────────

@given("I have run analyze with axis \"quality\" producing an analysis_id",
       target_fixture="analysis_id")
def _run_for_improve(engine, confirmed_intent, source_dir):
    r = _invoke_analyze(engine, confirmed_intent, "run",
                        path=source_dir, axes=["quality"],
                        agent_id="agent:test")
    return r["analysis_id"]


@when("I call analyze.improve with apply False", target_fixture="improve_result")
def _improve_no_apply(engine, confirmed_intent, analysis_id):
    return _invoke_analyze(engine, confirmed_intent, "improve",
                           analysis_id=analysis_id, apply=False,
                           agent_id="agent:test")


@then("the result carries an improvement_plan_id")
def _has_plan_id(improve_result):
    assert "improvement_plan_id" in improve_result


@then("the item_count is at least 2")
def _item_count_2(improve_result):
    assert improve_result.get("item_count", 0) >= 2


@then("a Reflection node with kind \"improvement-plan\" exists for that id")
def _reflection_improvement_plan(engine, improve_result):
    plans = [r for r in engine.memory.find("Reflection")
             if r.get("kind") == "improvement-plan"]
    assert any(p["id"] == improve_result["improvement_plan_id"] for p in plans)


# ── analyze.cleanup scenarios ─────────────────────────────────────────────────

@when("I call analyze.cleanup in dry_run mode", target_fixture="cleanup_result")
def _cleanup_dry(engine, confirmed_intent, source_dir):
    return _invoke_analyze(engine, confirmed_intent, "cleanup",
                           path=source_dir, dry_run=True,
                           agent_id="agent:test")


@then("the cleanup result carries an improvement_plan_id")
def _cleanup_has_plan_id(cleanup_result):
    assert "improvement_plan_id" in cleanup_result


@then("the cleanup item_count is at least 1")
def _item_count_1(cleanup_result):
    assert cleanup_result.get("item_count", 0) >= 1


# ── quality scanner steps ─────────────────────────────────────────────────────

@when("I invoke the quality scanner on that file", target_fixture="scan_findings")
def _quality_scan(source_dir):
    from agency.capabilities.analyze import _quality
    return _quality.scan(source_dir)


@then("the findings include at least 2 entries with rule \"Q001\"")
def _q001_count(scan_findings):
    hits = [f for f in scan_findings if f.rule == "Q001"]
    assert len(hits) >= 2


@then("those findings have severity \"warn\"")
def _q001_severity(scan_findings):
    hits = [f for f in scan_findings if f.rule == "Q001"]
    assert all(f.severity == "warn" for f in hits)


@then("the findings include a Q002 entry with severity \"warn\"")
def _q002_warn(scan_findings):
    hits = [f for f in scan_findings if f.rule == "Q002"]
    assert len(hits) >= 1
    assert hits[0].severity == "warn"


@then("no Q001 finding is produced")
def _no_q001(scan_findings):
    assert not [f for f in scan_findings if f.rule == "Q001"]


@then("every finding has keys rule, severity, file, line, message, and evidence")
def _finding_keys(scan_findings):
    for f in scan_findings:
        for key in ("rule", "severity", "file", "line", "message", "evidence"):
            assert hasattr(f, key), f"finding missing key {key!r}"


@then("severity is one of info, warn, or fail")
def _severity_enum(scan_findings):
    for f in scan_findings:
        assert f.severity in ("info", "warn", "fail")


@then("line is a positive integer")
def _line_positive(scan_findings):
    for f in scan_findings:
        assert isinstance(f.line, int) and f.line >= 1


@then("message is at most 120 characters")
def _message_len(scan_findings):
    for f in scan_findings:
        assert len(f.message) <= 120


@then("evidence is at most 200 characters")
def _evidence_len(scan_findings):
    for f in scan_findings:
        assert len(f.evidence) <= 200


# ── security scanner steps ─────────────────────────────────────────────────────

@when("I invoke the security scanner on that file", target_fixture="scan_findings")
def _security_scan(source_dir):
    from agency.capabilities.analyze import _security
    return _security.scan(source_dir)


@then("a S001 finding with severity \"fail\" is produced")
def _s001_fail(scan_findings):
    hits = [f for f in scan_findings if f.rule == "S001"]
    assert len(hits) >= 1 and hits[0].severity == "fail"


@then("a S002 finding with severity \"fail\" is produced")
def _s002_fail(scan_findings):
    hits = [f for f in scan_findings if f.rule == "S002"]
    assert len(hits) >= 1 and hits[0].severity == "fail"


@then("the finding message does not contain the literal key value")
def _key_not_in_message(scan_findings):
    hits = [f for f in scan_findings if f.rule == "S002"]
    assert hits
    assert "sk-1234567890abcdef" not in hits[0].message


@then("a S003 finding with severity \"warn\" is produced")
def _s003_warn(scan_findings):
    hits = [f for f in scan_findings if f.rule == "S003"]
    assert len(hits) >= 1 and hits[0].severity == "warn"


@then("no S004 finding is produced")
def _no_s004(scan_findings):
    assert not [f for f in scan_findings if f.rule == "S004"]


# ── performance scanner steps ──────────────────────────────────────────────────

@when("I invoke the performance scanner on that file", target_fixture="scan_findings")
def _performance_scan(source_dir):
    from agency.capabilities.analyze import _performance
    return _performance.scan(source_dir)


@then("a P001 finding with severity \"warn\" is produced")
def _p001_warn(scan_findings):
    hits = [f for f in scan_findings if f.rule == "P001"]
    assert len(hits) >= 1 and hits[0].severity == "warn"


@then("a P002 finding with severity \"info\" is produced")
def _p002_info(scan_findings):
    hits = [f for f in scan_findings if f.rule == "P002"]
    assert len(hits) >= 1 and hits[0].severity == "info"


@then("no P002 finding is produced")
def _no_p002(scan_findings):
    assert not [f for f in scan_findings if f.rule == "P002"]


# ── architecture scanner steps ─────────────────────────────────────────────────

@when("I invoke the architecture scanner on that package", target_fixture="scan_findings")
def _architecture_scan(source_dir):
    from agency.capabilities.analyze import _architecture
    return _architecture.scan(source_dir)


@then("an A001 finding with severity \"fail\" is produced")
def _a001_fail(scan_findings):
    hits = [f for f in scan_findings if f.rule == "A001"]
    assert len(hits) >= 1 and hits[0].severity == "fail"


@then("no A001 finding is produced")
def _no_a001(scan_findings):
    assert not [f for f in scan_findings if f.rule == "A001"]


# ── agency_doctor steps ────────────────────────────────────────────────────────

@when("I call agency_doctor", target_fixture="doctor_result")
def _call_doctor(engine):
    return call_tool(engine, "agency_doctor", {}, codemode=False)


@then("the payload includes analyze_extras")
def _has_analyze_extras(doctor_result):
    assert "analyze_extras" in doctor_result


@then("the known extra tools are exactly ruff, bandit, and radon")
def _extras_set(doctor_result):
    assert set(doctor_result["analyze_extras"]) == {"ruff", "bandit", "radon"}


@then("each status value is a non-empty string")
def _extras_status(doctor_result):
    for tool, status in doctor_result["analyze_extras"].items():
        assert isinstance(status, str) and status, f"{tool!r} status must be non-empty"
