"""Spec 017 — graph-native dogfood ledgers.

Tests:
  - dogfood.note records a Reflection with plan_slug
  - dogfood.render queries by plan_slug and emits markdown
  - empty render returns clean markdown ("(none yet)"); never raises
  - plan_slug is OPTIONAL on the Reflection ontology (backward compat)
  - dogfood.collect still works (deprecated docstring; not removed)
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
    return engine.intent.capture_and_confirm(
        "test dogfood graph-native", "x", "x", owner="user")


def _call(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "dogfood", verb,
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# dogfood.note
# ---------------------------------------------------------------------------


def test_note_records_reflection_with_plan_slug(engine, iid):
    r = _call(engine, iid, "note",
              observation="dispatch_decision hard-codes default driver",
              plan_slug="040-subagent-decision-heuristics")
    assert "reflection_id" in r
    assert r["plan_slug"] == "040-subagent-decision-heuristics"
    # The Reflection node carries plan_slug.
    refs = engine.memory.find("Reflection")
    me = next(rr for rr in refs if rr["id"] == r["reflection_id"])
    assert me["plan_slug"] == "040-subagent-decision-heuristics"
    assert me["scope"] == "observation"
    assert "dispatch_decision" in me["text"]


def test_note_links_serves_intent(engine, iid):
    r = _call(engine, iid, "note",
              observation="x",
              plan_slug="017-graph-native-dogfood-ledgers")
    rows = engine.memory.g.query(
        "MATCH (r:Reflection)-[:SERVES]->(i:Intent) "
        "WHERE r.id = $rid RETURN i",
        {"rid": r["reflection_id"]})
    assert len(rows) == 1
    assert rows[0]["i"]["properties"]["id"] == iid


# ---------------------------------------------------------------------------
# dogfood.render
# ---------------------------------------------------------------------------


def test_render_returns_markdown_with_observations(engine, iid):
    _call(engine, iid, "note",
          observation="first observation about analyze.paths",
          plan_slug="048-intent-chain-and-owners")
    _call(engine, iid, "note",
          observation="second observation about IP002 threshold",
          plan_slug="048-intent-chain-and-owners")
    r = _call(engine, iid, "render",
              plan_slug="048-intent-chain-and-owners")
    assert "content" in r
    assert "# DOGFOOD-NOTES" in r["content"]
    assert "048-intent-chain-and-owners" in r["content"]
    assert "first observation about analyze.paths" in r["content"]
    assert "second observation about IP002 threshold" in r["content"]


def test_render_empty_plan_returns_clean_markdown(engine, iid):
    r = _call(engine, iid, "render", plan_slug="999-nonexistent")
    assert "content" in r
    assert "999-nonexistent" in r["content"]
    assert "none yet" in r["content"].lower()


def test_render_scopes_to_plan_slug(engine, iid):
    """Reflections under one plan don't appear in another's render."""
    _call(engine, iid, "note", observation="plan A obs",
          plan_slug="plan-A")
    _call(engine, iid, "note", observation="plan B obs",
          plan_slug="plan-B")
    r_a = _call(engine, iid, "render", plan_slug="plan-A")
    r_b = _call(engine, iid, "render", plan_slug="plan-B")
    assert "plan A obs" in r_a["content"]
    assert "plan B obs" not in r_a["content"]
    assert "plan B obs" in r_b["content"]
    assert "plan A obs" not in r_b["content"]


def test_render_is_pure_no_graph_writes(engine, iid):
    _call(engine, iid, "note", observation="x", plan_slug="p")
    before = len(list(engine.memory.find("Reflection")))
    _call(engine, iid, "render", plan_slug="p")
    after = len(list(engine.memory.find("Reflection")))
    assert before == after, "render is a transform — no writes"


# ---------------------------------------------------------------------------
# Backward compat — plan_slug optional on Reflection.
# ---------------------------------------------------------------------------


def test_reflect_note_still_works_without_plan_slug(engine, iid):
    """reflect.note (the existing verb) doesn't take plan_slug — it
    should still create valid Reflections."""
    r, _ = engine.registry.invoke(
        engine.memory, iid, "reflect", "note",
        agent_id="agent:test", scope="technical",
        text="reflection without plan_slug")
    assert "result" in r


def test_collect_still_works_deprecated(engine, iid, tmp_path):
    """dogfood.collect is deprecated (per Spec 017 §Done When) but
    still functional for back-compat with Spec 014's pipeline."""
    plan_dir = tmp_path / "Plan"
    plan_dir.mkdir()
    one = plan_dir / "001-test"
    one.mkdir()
    (one / "DOGFOOD-NOTES.md").write_text(
        "**Observation 1 — test obs.** the body here.\n")
    r = _call(engine, iid, "collect", plan_dir=str(plan_dir))
    assert r["count"] == 1
    assert "test obs" in r["observations"][0]["title"]


def test_collect_docstring_marks_deprecated(engine):
    """The collect verb's docstring includes the deprecation note."""
    cap = engine.registry.get("dogfood")
    collect_spec = cap.verbs["collect"]
    doc = collect_spec["fn"].__doc__ or ""
    # Spec 017 §Done When: "Deprecated for ongoing use; prefer
    # dogfood.note + dogfood.render."
    assert "Deprecated" in doc or "deprecated" in doc
    assert "dogfood.note" in doc


def test_dogfood_has_five_verbs(engine):
    """Spec 020 v1 added `export`; Spec 020 v2 added `import`; Spec 017
    added `note` + `render`; collect was pre-existing. Five verbs total.
    (Toolchain execution lives in the broader `shell` capability — Spec 073.)"""
    cap = engine.registry.get("dogfood")
    assert {"note", "render", "collect", "export", "import"} == set(cap.verbs)


def test_render_respects_max_tokens(engine, iid):
    """sc:sc-analyze F3 review: render must cap token output and emit
    an omission marker when observations exceed the budget."""
    # Many large observations under one plan.
    long_obs = "lorem ipsum dolor sit amet " * 40   # ~200 chars each
    for _ in range(30):
        _call(engine, iid, "note", observation=long_obs,
              plan_slug="big-plan")
    r = _call(engine, iid, "render", plan_slug="big-plan", max_tokens=500)
    # Budget enforced (small slop for omission marker).
    assert r["tokens"] <= 700
    # Omitted count surfaced for the caller.
    assert r["omitted"] > 0
    # Marker present.
    assert "omitted" in r["content"].lower()


def test_render_returns_token_count_when_under_budget(engine, iid):
    _call(engine, iid, "note", observation="short obs",
          plan_slug="small-plan")
    r = _call(engine, iid, "render", plan_slug="small-plan", max_tokens=5000)
    assert r["tokens"] > 0
    assert r["omitted"] == 0
    assert r["count"] == 1
