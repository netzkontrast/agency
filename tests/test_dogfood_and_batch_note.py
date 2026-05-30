"""Tests for the v1 self-improvement primitives:

- `dogfood.collect(plan_dir)` — reads DOGFOOD-NOTES.md observations from a
  plan tree and returns them as data.
- `reflect.batch_note(scope, texts)` — bulk version of `reflect.note` that
  lands one Reflection node per text in a single invocation.
- The rebound `jules-self-improvement` skill that chains the two: Phase 1
  collects, Phase 2 folds into the graph.
"""
import os

import pytest

from agency.skill import SkillRun

# Spec 016 v2 Phase 5 — `engine` + `iid` fixtures now come from
# tests/conftest.py. This file is the proof-of-concept migration:
# 13 lines deleted, behaviour unchanged. The other 10 files with the
# same duplicate fixture block migrate opportunistically per Spec
# 016 v2 frontmatter (no "must-migrate-all" mandate).


def _call(engine, iid, cap, verb, **kw):
    res, _inv = engine.registry.invoke(
        engine.memory, iid, cap, verb, agent_id="agent:claude", **kw
    )
    return res


# ---------------------------------------------------------------------------
# dogfood.collect — parses DOGFOOD-NOTES.md.
# ---------------------------------------------------------------------------


SAMPLE_NOTES = """# DOGFOOD-NOTES

Running record.

## 2026-05-30 — first dispatch

**Observation 1 — dispatch hardcodes require_plan_approval=False.**
I had to dispatch without the plan-approval gate.

Subsequent paragraph about something else.

**Observation 2 — provenance is a one-graph traversal.**
The moat is real even for tactical dispatches.

## 2026-05-30 (later) — codex review

**Dogfood lesson 5 (architectural):** the probe is a stop-gap for the watcher.
"""


def test_collect_parses_observations_and_lessons(engine, iid, tmp_path):
    plan_root = tmp_path / "Plan"
    plan_subdir = plan_root / "012-some-spec"
    plan_subdir.mkdir(parents=True)
    (plan_subdir / "DOGFOOD-NOTES.md").write_text(SAMPLE_NOTES)

    res = _call(engine, iid, "dogfood", "collect", plan_dir=str(plan_root))
    assert res["count"] == 3
    assert res["plans"] == ["012-some-spec"]

    obs = res["observations"]
    assert obs[0]["kind"] == "observation"
    assert obs[0]["index"] == 1
    assert "dispatch hardcodes" in obs[0]["title"]
    assert "plan-approval gate" in obs[0]["text"]
    assert obs[0]["plan"] == "012-some-spec"

    assert obs[2]["kind"] == "dogfood lesson"
    assert obs[2]["index"] == 5

    # texts is a flat list ready for batch_note.
    assert res["texts"] == [o["text"] for o in obs]


def test_collect_returns_empty_when_plan_dir_missing(engine, iid):
    res = _call(engine, iid, "dogfood", "collect", plan_dir="/nonexistent/path")
    assert res["count"] == 0
    assert res["observations"] == []
    assert any("not found" in w for w in res["warnings"])


def test_collect_skips_plans_without_dogfood_notes(engine, iid, tmp_path):
    plan_root = tmp_path / "Plan"
    (plan_root / "001-no-notes").mkdir(parents=True)
    (plan_root / "002-with-notes").mkdir()
    (plan_root / "002-with-notes" / "DOGFOOD-NOTES.md").write_text(
        "**Observation 1 — x.** body."
    )

    res = _call(engine, iid, "dogfood", "collect", plan_dir=str(plan_root))
    assert res["plans"] == ["002-with-notes"]
    assert res["count"] == 1


def test_collect_against_real_repo_plan_tree(engine, iid):
    """Smoke test against the actual Plan/ tree — exercises against the
    real DOGFOOD-NOTES.md files we ship (Plan/012 + Plan/013). Doesn't
    assert specific counts (those will grow); asserts the file format
    we use parses without error."""
    # Resolve repo root regardless of pytest's cwd.
    here = os.path.dirname(os.path.abspath(__file__))
    plan_dir = os.path.join(here, "..", "Plan")
    res = _call(engine, iid, "dogfood", "collect", plan_dir=plan_dir)
    assert res["count"] > 0, "expected at least one Observation in the real plan tree"
    # Every observation has a non-empty title OR text.
    for o in res["observations"]:
        assert o["title"] or o["text"]


# ---------------------------------------------------------------------------
# reflect.batch_note — bulk Reflection ingestion.
# ---------------------------------------------------------------------------


def test_batch_note_records_one_reflection_per_text(engine, iid):
    res = _call(engine, iid, "reflect", "batch_note",
                scope="observation",
                texts=["dispatch raced the gate", "ssl flakiness blocks status"])
    assert res["count"] == 2
    assert len(res["ids"]) == 2

    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $sc RETURN r",
        {"sc": "observation"},
    )
    assert len(rows) == 2


def test_batch_note_skips_empty_texts(engine, iid):
    res = _call(engine, iid, "reflect", "batch_note",
                scope="observation",
                texts=["one real entry", "", None])
    assert res["count"] == 1


def test_batch_note_with_invalid_scope_raises(engine, iid):
    """The closed `scope` enum still applies in batch mode — one bad scope
    fails the whole batch (no Reflection nodes left dangling)."""
    with pytest.raises(ValueError, match="scope"):
        _call(engine, iid, "reflect", "batch_note",
              scope="dogfood",  # not in the closed REFLECT_SCOPES set
              texts=["x"])


# ---------------------------------------------------------------------------
# jules-self-improvement skill — end-to-end chain through both new verbs.
# ---------------------------------------------------------------------------


def test_skill_walk_chains_collect_into_batch_note(engine, iid, tmp_path):
    plan_root = tmp_path / "Plan"
    plan_subdir = plan_root / "999-fixture"
    plan_subdir.mkdir(parents=True)
    (plan_subdir / "DOGFOOD-NOTES.md").write_text(
        "**Observation 1 — alpha.** alpha body.\n\n"
        "**Observation 2 — beta.** beta body.\n"
    )

    sk = engine.ontology.skill("jules-self-improvement")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)

    # Phase 1 — dogfood.collect(plan_dir).
    res = run.submit({"plan_dir": str(plan_root)})
    assert res["status"] == "working"

    # Phase 2 — reflect.batch_note(scope, texts). The caller chains by
    # extracting the texts list from Phase 1's result.
    collection = _call(engine, iid, "dogfood", "collect", plan_dir=str(plan_root))
    res = run.submit({"scope": "observation", "texts": collection["texts"]})
    assert res["status"] == "completed"

    # Both observations landed as Reflection nodes.
    rows = engine.memory.g.query(
        "MATCH (r:Reflection) WHERE r.scope = $sc RETURN r",
        {"sc": "observation"},
    )
    reflection_texts = [r["r"]["properties"]["text"] for r in rows]
    assert any("alpha body" in t for t in reflection_texts)
    assert any("beta body" in t for t in reflection_texts)


def test_skill_phase1_is_now_invoke_bound(engine):
    sk = engine.ontology.skill("jules-self-improvement")
    p1 = sk["phases"][0]
    assert p1["name"] == "collect-dogfood"
    assert p1["invoke"] == {"capability": "dogfood", "verb": "collect"}
    p2 = sk["phases"][1]
    assert p2["name"] == "fold-into-graph"
    assert p2["invoke"] == {"capability": "reflect", "verb": "batch_note"}
