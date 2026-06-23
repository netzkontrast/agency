"""Acceptance — finish_spec, the done-cascade trigger (Spec 388).

`workflow.finish_spec` moves a spec to /done across all three state
representations (folder + frontmatter + node) in one call. The file-move core is
tested in an ISOLATED temp Plan tree (never the real repo); the node/ADR/
architecture steps are best-effort and exercised against the live engine ctx.
"""
from __future__ import annotations

import os

from pytest_bdd import parsers, scenarios, then, when, given


scenarios("features/spec_done_cascade.feature")


def _unwrap(raw):
    if hasattr(raw, "data"):
        return raw.data
    if isinstance(raw, dict):
        return raw.get("result", raw)
    return raw


@given(parsers.parse('a draft spec "{folder}" in a temp Plan tree'),
       target_fixture="plan_tree")
def _draft_spec(tmp_path, folder):
    d = tmp_path / "Plan" / "draft" / folder
    d.mkdir(parents=True)
    (d / "spec.md").write_text(
        '---\nspec_id: "999"\nslug: demo\nstatus: partial\nstate: draft\n---\n\n'
        '# Spec 999 — demo\n\nbody\n')
    return str(tmp_path / "Plan")


@when(parsers.parse('I finish_spec "{sid}" in that tree'),
      target_fixture="finish_result")
def _finish(engine, confirmed_intent, plan_tree, sid):
    raw, _ = engine.registry.invoke(
        engine.memory, confirmed_intent, "workflow", "finish_spec",
        spec_id=sid, root=plan_tree, rebuild_architecture=False)
    return _unwrap(raw)


@then(parsers.parse('the finish result reports moved from "{state}"'))
def _moved_from(finish_result):
    assert finish_result.get("moved") is True, f"expected moved; got {finish_result}"
    assert finish_result.get("from_state") == "draft"


@then(parsers.parse('the spec now lives under "{state}" in the tree'))
def _under_done(finish_result, plan_tree, state):
    moved = os.path.join(plan_tree, state, "999-demo", "spec.md")
    assert os.path.isfile(moved), f"expected spec at {moved}"


@then(parsers.parse('the moved spec frontmatter state is "{state}"'))
def _frontmatter_done(plan_tree, state):
    txt = open(os.path.join(plan_tree, "done", "999-demo", "spec.md")).read()
    assert f"state: {state}" in txt, f"frontmatter not reconciled:\n{txt[:160]}"
    assert "state: draft" not in txt


@then("the source draft folder is gone")
def _src_gone(plan_tree):
    assert not os.path.exists(os.path.join(plan_tree, "draft", "999-demo")), \
        "the source draft folder must be moved, not copied"


@then("the finish result is a typed error")
def _typed_error(finish_result):
    assert finish_result.get("moved") is False
    assert "error" in finish_result and "404" in finish_result["error"]
