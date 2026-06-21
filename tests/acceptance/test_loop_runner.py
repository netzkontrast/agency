"""Acceptance — loop external runner, model detection & egress (Spec 369).

The out-of-session twin: model detection (metadata only, secret-free), the ported
stdlib run-loop.py, and the egress-consent gate (cross-vendor consent + redaction)
for both surfaces. Carries the 362 closers — the provenance moat (the whole loop
recoverable from the graph) and spine↔runner contract parity.
"""
from __future__ import annotations

import re
import tempfile

import pytest
from pytest_bdd import given, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_runner.feature")

# Top-level stdlib modules the ported run-loop.py is allowed to import.
_STDLIB = {"__future__", "datetime", "fnmatch", "json", "pathlib", "re",
           "subprocess", "sys", "time", "typing", "os", "argparse", "shutil",
           "dataclasses", "textwrap", "collections", "io"}


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def box():
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _eng(engine):
    return engine


@given("an open loop served by a goal", target_fixture="box")
def _open_loop(engine):
    from agency._loop import frame_goal, open_loop
    gid = frame_goal(engine, "Map ACME onboarding into an agent workflow",
                     "A LOOP.md, every step mapped, nothing TBD")["goal_id"]
    engine.intent.confirm(gid)
    lid = open_loop(engine, gid, max_iterations=4, max_revisions=2)["loop_id"]
    return {"loop_id": lid, "goal_id": gid}


# ── model detection ──────────────────────────────────────────────────────────
@when("I detect models with claude and ollama installed", target_fixture="box")
def _detect(box):
    from agency._loop import detect_models
    fake_which = (lambda c: f"/usr/bin/{c}" if c in ("claude", "ollama") else None)
    box["detected"] = detect_models(which=fake_which)
    return box


@then("the available models list their argv invocations, families, and local flags")
def _detected(box):
    avail = {m["cli"]: m for m in box["detected"]["available"]}
    assert set(avail) == {"claude", "ollama"}, avail
    assert avail["ollama"]["local"] is True and avail["claude"]["local"] is False
    for m in avail.values():
        assert isinstance(m["invoke"], list) and m["invoke"], m
        assert m["family"], m


@then("no secret-shaped material appears anywhere in the result")
def _no_secrets(box):
    import json as _json
    blob = _json.dumps(box["detected"])
    assert not re.search(r"sk-[A-Za-z0-9]{8,}|api[_-]?key|token", blob, re.I), blob


# ── register_model ───────────────────────────────────────────────────────────
@then("register_model with a shell-string invoke is rejected")
def _reg_shell():
    from agency._loop import register_model
    assert "error" in register_model("claude", "anthropic", "claude -p --key sk-abc123")


@then("register_model with a key in the argv is rejected")
def _reg_key():
    from agency._loop import register_model
    res = register_model("claude", "anthropic", ["claude", "-p", "--key", "sk-abcd1234"])
    assert "error" in res, res


@then("register_model with a clean argv is accepted")
def _reg_clean():
    from agency._loop import register_model
    res = register_model("claude", "anthropic", ["claude", "-p"])
    assert res.get("registered") is True, res


# ── emitted runner ───────────────────────────────────────────────────────────
@when("I emit the runner", target_fixture="box")
def _emit_runner(engine, box, tmp_path):
    from agency._loop import frame_goal, open_loop, emit_runner
    gid = frame_goal(engine, "g", "done")["goal_id"]
    engine.intent.confirm(gid)
    lid = open_loop(engine, gid, max_iterations=3)["loop_id"]
    box["runner"] = emit_runner(engine, lid, str(tmp_path / "run"))
    return box


@then("run-loop.py loads loop.resolved.json and imports only the Python stdlib")
def _runner_stdlib(box):
    src = open(box["runner"]["file"], encoding="utf-8").read()
    assert "loop.resolved.json" in src, "runner does not read the resolved spec"
    imports = re.findall(r"^(?:import|from)\s+([\w.]+)", src, re.MULTILINE)
    nonstd = sorted({m.split(".")[0] for m in imports} - _STDLIB)
    assert not nonstd, f"runner imports non-stdlib modules: {nonstd}"


# ── egress gate ──────────────────────────────────────────────────────────────
@then("a local member requires no egress consent")
def _local_ok():
    from agency._loop import egress_consent
    res = egress_consent({"role": "judge", "family": "ollama", "local": True})
    assert res["permit"] is True and res["requires_consent"] is False, res


@when("a cross-vendor judge needs consent and the user grants it", target_fixture="box")
def _consent(engine, box):
    from agency._loop import egress_consent
    member = {"role": "judge", "family": "codex", "local": False}
    box["before"] = egress_consent(member, consent_given=False)
    gate_id = engine.memory.record("Gate", {
        "name": "egress_consent", "passed": True, "member": "codex",
        "evidence": "user granted cross-vendor send"})
    engine.memory.link(box["loop_id"], gate_id, "PASSED")
    box["after"] = egress_consent(member, consent_given=True)
    box["gate_id"] = gate_id
    return box


@then("the first send is blocked for consent and the granted consent is a graph node")
def _consent_recorded(engine, box):
    assert box["before"]["requires_consent"] is True and box["before"]["permit"] is False
    assert box["after"]["permit"] is True, box["after"]
    g = engine.memory.recall(box["gate_id"])
    assert g and g.get("name") == "egress_consent", g


@then("a secrets path is redacted before a cross-vendor send")
def _redaction():
    from agency._loop import egress_consent
    res = egress_consent({"role": "judge", "family": "codex", "local": False},
                         consent_given=True, redact_globs=["secrets/**"],
                         context_paths=["plan.md", "secrets/key.txt"])
    assert res["redacted"] == ["secrets/key.txt"], res


# ── 362 closer: contract parity ──────────────────────────────────────────────
@then("control_evaluate is deterministic and the emitted runner reads the same control fields")
def _parity(engine, box, tmp_path):
    from agency._loop import control_evaluate, emit_runner
    verdict = control_evaluate({"max_revisions": 2, "max_iterations": 4}, {"revisions": 2})
    assert verdict["permit"] is False and verdict["stop_reason"] == "max_revisions", verdict
    res = emit_runner(engine, box["loop_id"], str(tmp_path / "run"))
    src = open(res["file"], encoding="utf-8").read()
    for field in ("max_revisions", "max_iterations", "no_progress"):
        assert field in src, f"runner missing control field {field!r}"


# ── 362 closer: the provenance moat ──────────────────────────────────────────
@when("I run the full loop pipeline to completion", target_fixture="box")
def _pipeline(engine):
    from agency._loop import frame_goal, open_loop, add_criterion, add_member, advance
    from agency._loop import compile as loop_compile
    gid = frame_goal(engine, "Map ACME's manual onboarding into an agent workflow",
                     "A LOOP.md with every step mapped to a tool or human, nothing TBD")["goal_id"]
    engine.intent.confirm(gid)
    lid = open_loop(engine, gid, max_iterations=4, max_revisions=2)["loop_id"]
    add_criterion(engine, lid, "programmatic", check=["true"], expect="exit_zero", cid="build-ok")
    add_criterion(engine, lid, "judge", rubric="every step has an owner", cid="covers-goal")
    add_member(engine, lid, "judge", scope="both", family="codex")
    advance(engine, lid)                                       # planning -> plan_gate
    advance(engine, lid, judge_output='{"verdict": "pass"}')  # plan_gate -> delivering
    advance(engine, lid)                                       # delivering -> delivery_gate
    advance(engine, lid, judge_output='{"verdict": "pass"}')  # delivery_gate -> completed
    return {"loop_id": lid, "goal_id": gid, "compiled": loop_compile(engine, lid)}


@then("the whole chain is recoverable from the graph")
def _moat(engine, box):
    rows = engine.memory.g.query(
        "MATCH (l)-[:SERVES]->(i:Intent) WHERE l.id=$lid RETURN i.id AS iid",
        {"lid": box["loop_id"]})
    assert rows and rows[0]["iid"] == box["goal_id"], rows
    resolved = box["compiled"]["resolved"]
    assert resolved["goal"]["statement"], resolved["goal"]
    assert set(resolved["criteria_by_id"]) == {"build-ok", "covers-goal"}, resolved["criteria_by_id"]
    assert resolved["council_by_id"], resolved["council_by_id"]
    assert engine.memory.recall(box["loop_id"])["state"] == "completed"
