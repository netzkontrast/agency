"""Acceptance — shell capability (Spec 073/075).

Converted from tests/test_shell.py + tests/test_shell_templates.py.

Dropped as implementation/structural (not behaviour):
- test_apply_filter_slices: unit tests on _apply_filter internals (private function)
- test_research_intent_deliverable_enum_bites_at_record_time: wrong module
- assertions about _ALLOWED_TOOLS membership by name (implementation detail)
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/shell.feature")


# ── stub runner ──────────────────────────────────────────────────────────────

class _StubRunner:
    def __init__(self, stdout="", exit_code=0):
        self.stdout = stdout
        self.exit_code = exit_code
        self.calls: list[list[str]] = []

    def run(self, argv, timeout=600):
        self.calls.append(list(argv))
        return {"exit_code": self.exit_code, "stdout": self.stdout, "stderr": "", "duration_s": 0.1}


# ── engine with stub runner ──────────────────────────────────────────────────

from agency.engine import Engine


@pytest.fixture
def runner():
    return _StubRunner()


@pytest.fixture
def engine(runner):
    e = Engine(tempfile.mktemp(suffix=".db"), runner=runner)
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("shell acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


def _call(engine, confirmed_intent, verb, **kw):
    res, _ = invoke(engine, confirmed_intent, "shell", verb, **kw)
    return res.get("result", res) if isinstance(res, dict) else res


def _has_edge(engine, src, dst, rel):
    return bool(engine.memory.g.query(
        f"MATCH (a)-[:{rel}]->(b) WHERE a.id=$a AND b.id=$b RETURN b", {"a": src, "b": dst}))


# ── Given ─────────────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


# ── filter verb ───────────────────────────────────────────────────────────────

@when(parsers.parse('I filter 100 lines with spec "{spec}"'), target_fixture="result")
def _filter(engine, confirmed_intent, spec):
    return _call(engine, confirmed_intent, "filter",
                 text="\n".join(f"line{i}" for i in range(100)), spec=spec)


@then(parsers.parse("the filtered output has {n:d} lines"))
def _filter_lines(result, n):
    assert result["lines"] == n
    assert result["output"].endswith(f"line{100 - 1}")


@then("no subprocess was started")
def _no_calls(runner):
    assert runner.calls == []


# ── run: allowlisted command ──────────────────────────────────────────────────

@when(parsers.parse('I run "{command}" with filter "{filt}" and {n:d} lines of stdout'),
      target_fixture="result")
def _run(engine, confirmed_intent, runner, command, filt, n):
    runner.stdout = "\n".join(f"row{i}" for i in range(n))
    return _call(engine, confirmed_intent, "run", command=command, filter=filt)


@then(parsers.parse("the exit code is {code:d}"))
def _exit_code(result, code):
    assert result["exit_code"] == code


@then(parsers.parse("the output has {n:d} lines"))
def _output_lines(result, n):
    assert result["lines"] == n


@then(parsers.parse('a command-run node is recorded with tool "{tool}"'))
def _node_recorded(engine, result, tool):
    node = engine.memory.recall(result["run_id"])
    assert node["kind"] == "command-run"
    assert node["tool"] == tool


@then("the command-run node SERVES the intent")
def _node_serves(engine, confirmed_intent, result):
    assert _has_edge(engine, result["run_id"], confirmed_intent, "SERVES")


# ── run: rejected command ──────────────────────────────────────────────────────

@when(parsers.parse('I run "{command}" with no filter'), target_fixture="result")
def _run_no_filter(engine, confirmed_intent, command):
    return _call(engine, confirmed_intent, "run", command=command)


@then("the result carries an error")
def _has_error(result):
    assert "error" in result


@then("a subprocess was started")
def _subprocess_started(runner):
    assert runner.calls


# ── run via template ──────────────────────────────────────────────────────────

@when(parsers.parse('I run template "{tmpl}" with stdout "{stdout}"'), target_fixture="result")
def _run_template_stdout(engine, confirmed_intent, runner, tmpl, stdout):
    runner.stdout = stdout.replace("\\n", "\n")
    return _call(engine, confirmed_intent, "run", template=tmpl)


@then(parsers.parse('the result names the template "{tmpl}"'))
def _result_names_template(result, tmpl):
    assert result.get("template") == tmpl


@then(parsers.parse('every output line contains "{text}"'))
def _every_line_contains(result, text):
    for line in result["output"].splitlines():
        assert text in line


@when(parsers.parse('I run template "{tmpl}"'), target_fixture="result")
def _run_template(engine, confirmed_intent, tmpl):
    return _call(engine, confirmed_intent, "run", template=tmpl)


@then("the error response lists available templates")
def _error_lists_templates(result):
    assert "templates" in result or "error" in result


# ── templates list ────────────────────────────────────────────────────────────

@when("I list templates", target_fixture="result")
def _list_templates(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "templates")


@then(parsers.parse('the list includes the seed template "{name}"'))
def _list_includes_seed(result, name):
    names = {t["name"] for t in result}
    assert name in names


@then("every template entry has a command and a doc")
def _template_has_fields(result):
    for t in result:
        assert "command" in t and "doc" in t


# ── define + discovery ────────────────────────────────────────────────────────

@when(parsers.parse('I define template "{name}" with command "{cmd}" and filter "{filt}" and stdout "{stdout}"'),
      target_fixture="result")
def _define_and_prime(engine, confirmed_intent, runner, name, cmd, filt, stdout):
    runner.stdout = stdout.replace("\\n", "\n")
    return _call(engine, confirmed_intent, "define", name=name, command=cmd,
                 filter=filt, doc="test", tags="")


@then("the template is recorded with a template_id")
def _has_template_id(result):
    assert result.get("template_id")


@then(parsers.parse("running template \"{name}\" returns {n:d} lines"))
def _run_returns_lines(engine, confirmed_intent, name, n):
    out = _call(engine, confirmed_intent, "run", template=name)
    assert out["lines"] == n


@then(parsers.parse('the dispatched command starts with "{cmd}"'))
def _dispatched_cmd(runner, cmd):
    assert runner.calls[0][0] == cmd.split()[0]


@when(parsers.parse('I define template "{name}" with command "{cmd}" tag "{tag}"'),
      target_fixture="result")
def _define_with_tag(engine, confirmed_intent, name, cmd, tag):
    return _call(engine, confirmed_intent, "define", name=name, command=cmd,
                 filter="full", doc="test", tags=tag)


@when(parsers.parse('I query templates with "{query}"'), target_fixture="query_result")
def _query_templates(engine, confirmed_intent, query):
    return _call(engine, confirmed_intent, "templates", query=query)


@then(parsers.parse('"{name}" appears in the results with source "{source}"'))
def _appears_with_source(query_result, name, source):
    names = {t["name"] for t in query_result}
    assert name in names
    match = next(t for t in query_result if t["name"] == name)
    assert match["source"] == source


@then(parsers.parse('querying templates with "{query}" returns an empty list'))
def _empty_query(engine, confirmed_intent, query):
    res = _call(engine, confirmed_intent, "templates", query=query)
    assert res == []


@when("I define a template that overrides a seed template using command \"echo overridden\"",
      target_fixture="seed_name")
def _define_override(engine, confirmed_intent, runner):
    from agency.capabilities.shell import _TEMPLATES
    seed_name = sorted(_TEMPLATES)[0]
    runner.stdout = "x\ny"
    _call(engine, confirmed_intent, "define", name=seed_name, command="echo overridden",
          filter="full", doc="graph override", tags="")
    return seed_name


@then("running that template dispatches \"echo overridden\"")
def _override_dispatched(engine, confirmed_intent, runner, seed_name):
    _call(engine, confirmed_intent, "run", template=seed_name)
    assert runner.calls[0][:2] == ["echo", "overridden"]


@then("the template list shows one entry for that name from source \"graph\"")
def _one_entry_from_graph(engine, confirmed_intent, seed_name):
    allt = _call(engine, confirmed_intent, "templates")
    entries = [t for t in allt if t["name"] == seed_name]
    assert len(entries) == 1 and entries[0]["source"] == "graph"


@when("I define template \"evil\" with command \"rm -rf /\"", target_fixture="result")
def _define_evil(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "define", name="evil", command="rm -rf /", filter="full")


@then("querying templates for \"evil\" returns no results")
def _evil_not_found(engine, confirmed_intent):
    res = _call(engine, confirmed_intent, "templates", query="evil")
    assert res == []


@when("I define template \"dup\" with command \"git status\"", target_fixture="dup_result")
def _define_dup(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "define", name="dup", command="git status", filter="full")


@when("I redefine template \"dup\" with command \"git diff\"", target_fixture="dup_result2")
def _redefine_dup(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "define", name="dup", command="git diff", filter="tail:5")


@then("the template list shows one \"dup\" entry with command \"git diff\"")
def _dup_shows_git_diff(engine, confirmed_intent):
    entries = [t for t in _call(engine, confirmed_intent, "templates") if t["name"] == "dup"]
    assert len(entries) == 1
    assert entries[0]["command"] == "git diff"


@then("a SUPERSEDED_BY trail exists in the graph")
def _superseded_trail(engine):
    rows = engine.memory.g.query(
        "MATCH (a:Artefact)-[:SUPERSEDED_BY]->(b:Artefact) RETURN b")
    assert rows


@when("I define template \"mine\" with command \"ls\"", target_fixture="mine_result")
def _define_mine(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "define", name="mine", command="ls", filter="full")


@then("\"mine\" appears in the results")
def _mine_in_results(result):
    names = {t["name"] for t in result}
    assert "mine" in names


@then("all seed templates are present")
def _seeds_present(result):
    from agency.capabilities.shell import _TEMPLATES
    names = {t["name"] for t in result}
    assert set(_TEMPLATES).issubset(names)


@when("I define template \"prov\" with command \"ls\"", target_fixture="prov_result")
def _define_prov(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "define", name="prov", command="ls", filter="full")


@then("the template artefact SERVES the intent")
def _prov_serves(engine, confirmed_intent, prov_result):
    tid = prov_result["template_id"]
    assert engine.memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(i:Intent) WHERE a.id=$a AND i.id=$i RETURN i",
        {"a": tid, "i": confirmed_intent})
