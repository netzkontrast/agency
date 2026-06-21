"""Acceptance — Spec 381 §3: QualityRun history graph node + trend.

Behaviour-only: a run is a graph node (not a sidecar file); the trend is a query
that reads only prior COMPLETE same-mode runs. Exercised through analyze.record_run.
"""
from __future__ import annotations

import os
import re

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/quality_run.feature")

_SEV = {"critical": "fail", "warning": "warn", "suggestion": "info"}


def _parse_findings(spec: str) -> list[dict]:
    out: list[dict] = []
    for n, tier in re.findall(r"(\d+)\s+(critical|warning|suggestion)", spec):
        out += [{"rule": "X", "severity": _SEV[tier], "file": "a.py", "line": i + 1,
                 "message": "m", "evidence": "e", "risk_code": "",
                 "source": "", "consequence": "", "remedy": ""}
                for i in range(int(n))]
    return out


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


@given(parsers.re(r'a recorded "(?P<mode>[^"]+)" run of (?P<spec>.+)'))
def _prior_run(mode, spec, engine_iid):
    engine, iid = engine_iid
    invoke(engine, iid, "analyze", "record_run",
           mode=mode, findings=_parse_findings(spec), status="complete")


@given(parsers.re(r'a recorded incomplete "(?P<mode>[^"]+)" run of (?P<spec>.+)'))
def _prior_incomplete(mode, spec, engine_iid):
    engine, iid = engine_iid
    invoke(engine, iid, "analyze", "record_run",
           mode=mode, findings=_parse_findings(spec), status="incomplete")


@when(parsers.re(r'I record an? "(?P<mode>[^"]+)" run of (?P<spec>.+)'),
      target_fixture="run_result")
def _record_run(mode, spec, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "record_run",
                       mode=mode, findings=_parse_findings(spec), status="complete")
    return result


@then(parsers.re(r'a QualityRun graph node exists for mode "(?P<mode>[^"]+)"'))
def _node_exists(mode, run_result, engine_iid):
    engine, _ = engine_iid
    runs = engine.memory.find("QualityRun")
    assert any(r.get("mode") == mode for r in runs), f"no QualityRun for {mode}: {runs}"


@then("no brooks-lint history file is written")
def _no_sidecar():
    assert not os.path.exists(".brooks-lint-history.json"), "sidecar file was written"


@then(parsers.re(r"the trend delta is (?P<delta>-?\d+)"))
def _trend_delta(delta, run_result):
    trend = run_result.get("trend") or {}
    assert trend.get("delta") == int(delta), trend


@then("the trend reports first run")
def _trend_first(run_result):
    trend = run_result.get("trend") or {}
    assert trend.get("first") is True, trend
