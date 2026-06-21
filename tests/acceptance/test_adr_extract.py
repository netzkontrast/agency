"""Acceptance — ADR spec→decision extraction + ready predicate (Spec 356 Slice 1).

Behaviour through the real Engine registry:
- `adr.extract_decisions(spec_id, apply=False)` previews evidence-anchored WH(Y)
  candidates from an ingested spec Document (decidable — no API key);
- `apply=True` drafts `Decision`s that REFINE the spec, idempotently;
- `adr.spec_decisions_ready(spec_id)` gates /open→/inprogress on every extracted
  decision being approved (355), and a zero-decision spec never vacuously passes.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/adr_extract.feature")


_TWO = """---
spec_id: "TEST-1"
domain: core
---
# Test spec

## Why
The store needs cross-session persistence. Without this, history is lost.

## Design
We decided for a single append-only GraphQLite graph instead of a relational mirror.
We chose bi-temporal versioning rather than destructive overwrites.

## Failure modes
Reads must be supersession-aware or they return stale data.
"""

_NONE = """---
spec_id: "TEST-2"
domain: core
---
# Docs spec

## Why
This documents the directory layout.

## Design
This section lists the directories. It describes the file naming convention.
"""


def _ingest(engine, intent, tmp_path, body, name):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    res, _ = invoke(engine, intent, "document", "ingest", path=str(path))
    return res.get("document_id")


@given("an ingested spec with two design decisions", target_fixture="spec_id")
def _spec_two(engine, confirmed_intent, tmp_path):
    return _ingest(engine, confirmed_intent, tmp_path, _TWO, "spec-two.md")


@given("an ingested spec with no decisions", target_fixture="spec_id")
def _spec_none(engine, confirmed_intent, tmp_path):
    return _ingest(engine, confirmed_intent, tmp_path, _NONE, "spec-none.md")


@when("I extract decisions from it as a preview", target_fixture="extract")
def _preview(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "extract_decisions",
                    spec_id=spec_id, apply=False)
    return res


@when("I apply extraction to draft the decisions", target_fixture="extract")
def _apply(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "extract_decisions",
                    spec_id=spec_id, apply=True)
    return res


@when("I apply extraction again", target_fixture="extract")
def _apply_again(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "extract_decisions",
                    spec_id=spec_id, apply=True)
    return res


@when("I check whether the spec is ready", target_fixture="ready")
def _ready(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "spec_decisions_ready",
                    spec_id=spec_id)
    return res


@when(parsers.parse('I approve every decision of the spec as owner "{approver}"'))
def _approve_all(engine, confirmed_intent, spec_id, approver):
    res, _ = invoke(engine, confirmed_intent, "adr", "spec_decisions_ready",
                    spec_id=spec_id)
    for d in res.get("decisions", []):
        # Extracted skeletons fail the automated DoD → the owner reviews + overrides.
        invoke(engine, confirmed_intent, "adr", "approve",
               decision_id=d["id"], approver=approver, override=True)


@then("at least two candidates are returned")
def _two_candidates(extract):
    assert len(extract.get("candidates", [])) >= 2, extract


@then("every candidate has an evidence span")
def _evidence(extract):
    cands = extract.get("candidates", [])
    assert cands and all(c.get("evidence_span") for c in cands), extract


@then("the spec has exactly two decisions")
def _two_decisions(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "spec_decisions_ready",
                    spec_id=spec_id)
    assert len(res.get("decisions", [])) == 2, res


@then("the spec is not ready to advance")
def _not_ready(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "spec_decisions_ready",
                    spec_id=spec_id)
    assert res.get("ready") is False, res


@then("the spec is ready to advance")
def _is_ready(engine, confirmed_intent, spec_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "spec_decisions_ready",
                    spec_id=spec_id)
    assert res.get("ready") is True, res


@then(parsers.parse('the not-ready reason is "{reason}"'))
def _reason(ready, reason):
    assert ready.get("reason") == reason, ready
