"""Acceptance — spec-state lifecycle (Spec 357): specs as Lifecycles.

Behaviour through the real Engine registry:
- `workflow.open_spec` mints a SpecLifecycle on the `spec` machine (state draft);
- `workflow.move_spec` advances it via ctx.lifecycle.move (illegal edges rejected);
- the open→inprogress transition is gated by the ADR hinge
  (`adr.spec_decisions_ready`) — blocked until every extracted decision is approved;
- `workflow.board` reports the live SpecLifecycles grouped by state.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/spec_state.feature")


_PLAIN = """---
spec_id: "WF-1"
domain: core
---
# A plain spec

## Why
It needs a state machine.

## Design
We use a folder per stage.
"""

_TWO = """---
spec_id: "WF-2"
domain: core
---
# A spec with decisions

## Why
The store needs cross-session persistence.

## Design
We decided for a single append-only GraphQLite graph instead of a relational mirror.
We chose bi-temporal versioning rather than destructive overwrites.

## Failure modes
Reads must be supersession-aware.
"""


def _ingest(engine, intent, tmp_path, body, name):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    res, _ = invoke(engine, intent, "document", "ingest", path=str(p))
    return res.get("document_id")


@given("an ingested spec document", target_fixture="spec_id")
def _plain(engine, confirmed_intent, tmp_path):
    return _ingest(engine, confirmed_intent, tmp_path, _PLAIN, "plain.md")


@given("an ingested spec document with two extracted decisions", target_fixture="spec_id")
def _with_decisions(engine, confirmed_intent, tmp_path):
    doc = _ingest(engine, confirmed_intent, tmp_path, _TWO, "two.md")
    invoke(engine, confirmed_intent, "adr", "extract_decisions",
           spec_id=doc, apply=True)
    return doc


@when("I open the spec lifecycle")
def _open(engine, confirmed_intent, spec_id):
    invoke(engine, confirmed_intent, "workflow", "open_spec", spec_id=spec_id)


@when(parsers.parse('I move the spec to "{to_state}"'), target_fixture="move_res")
def _move(engine, confirmed_intent, spec_id, to_state):
    res, _ = invoke(engine, confirmed_intent, "workflow", "move_spec",
                    spec_id=spec_id, to_state=to_state)
    return res


@when(parsers.parse('I approve every decision of the spec as owner "{approver}"'))
def _approve_all(engine, confirmed_intent, spec_id, approver):
    res, _ = invoke(engine, confirmed_intent, "adr", "spec_decisions_ready",
                    spec_id=spec_id)
    for d in res.get("decisions", []):
        invoke(engine, confirmed_intent, "adr", "approve",
               decision_id=d["id"], approver=approver, override=True)


@then(parsers.parse('the spec state is "{state}"'))
def _state_is(engine, confirmed_intent, spec_id, state):
    res, _ = invoke(engine, confirmed_intent, "workflow", "board")
    board = res.get("board", {})
    found = [s for s, items in board.items()
             for it in items if it["spec_id"] == spec_id]
    assert found == [state], (found, res)


@then("the spec move is rejected")
def _rejected(move_res):
    assert move_res.get("moved") is not True, move_res
    assert move_res.get("error") or move_res.get("blocked"), move_res


@then("the spec move is blocked")
def _blocked(move_res):
    assert move_res.get("blocked") is True, move_res


@given("a Plan tree with a clean, a drifted, and a legacy spec",
       target_fixture="plan_root")
def _plan_tree(tmp_path):
    root = tmp_path / "Plan"

    def _w(rel, state):
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        fm = (f'---\nspec_id: "{rel}"\nstate: "{state}"\n---\n# spec\n' if state
              else f'---\nspec_id: "{rel}"\n---\n# spec\n')
        (d / "spec.md").write_text(fm, encoding="utf-8")

    _w("draft/001-clean", "draft")     # clean — folder == frontmatter
    _w("open/002-drift", "draft")      # drift — folder open ≠ frontmatter draft
    _w("003-legacy", "")               # legacy flat — no state folder, no state:
    return str(root)


@when("I index the Plan tree", target_fixture="index_res")
def _index(engine, confirmed_intent, plan_root):
    res, _ = invoke(engine, confirmed_intent, "workflow", "index", root=plan_root)
    return res


@then("the index flags the drifted spec")
def _flag_drift(index_res):
    drift = [r for r in index_res["rows"] if "drift" in r["flags"]]
    assert len(drift) == 1 and "002-drift" in drift[0]["spec"], index_res


@then("the index marks the legacy spec")
def _flag_legacy(index_res):
    assert any("003-legacy" in r["spec"] and "legacy" in r["flags"]
               for r in index_res["rows"]), index_res


@then("the clean spec has no flags")
def _clean_no_flags(index_res):
    clean = [r for r in index_res["rows"] if "001-clean" in r["spec"]]
    assert clean and clean[0]["flags"] == [], index_res
