"""Tests for the `dispatch-decision` skill + `delegate.dispatch_decision` /
`delegate.dispatch_bash_hints` verbs.

The skill is the canonical decision point before any fan-out. It encodes the
token-economics heuristic that used to live in AGENCY_PROTOCOL.md §9a — but
since the heuristic is about ORCHESTRATOR decision-making (not about Jules's
behavior), it belongs in a walkable skill, not in the agent doctrine doc.

Per the canon (CORE.md:47-62) — a skill IS a Lifecycle template; the walker
records the gated walk in the bi-temporal graph.
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "decide dispatch vs inline",
        "recommendation matches the heuristic on every fixture",
        "triggers list reports exactly which criteria fired",
    )
    engine.intent.confirm(intent)
    return intent


def _call(engine, iid, verb, **kw):
    res, _inv = engine.registry.invoke(
        engine.memory, iid, "delegate", verb, agent_id="agent:claude", **kw
    )
    return res


# ---------------------------------------------------------------------------
# dispatch_decision verb — the heuristic itself.
# ---------------------------------------------------------------------------


def test_inline_when_no_triggers_fire(engine, iid):
    res = _call(engine, iid, "dispatch_decision",
                file_count=2, exploration_needed=False,
                parallelism=1, est_duration_min=3)
    assert res["recommendation"] == "inline"
    assert res["triggers"] == []
    assert "~700 tokens" in res["rationale"]


def test_dispatch_when_file_count_threshold(engine, iid):
    res = _call(engine, iid, "dispatch_decision", file_count=4)
    assert res["recommendation"] == "dispatch"
    assert "file_count>=4" in res["triggers"]


def test_dispatch_when_exploration_needed(engine, iid):
    res = _call(engine, iid, "dispatch_decision", exploration_needed=True)
    assert res["recommendation"] == "dispatch"
    assert "exploration_needed" in res["triggers"]


def test_dispatch_when_parallelism_threshold(engine, iid):
    res = _call(engine, iid, "dispatch_decision", parallelism=3)
    assert res["recommendation"] == "dispatch"
    assert "parallelism>=3" in res["triggers"]


def test_dispatch_when_long_running(engine, iid):
    res = _call(engine, iid, "dispatch_decision", est_duration_min=15)
    assert res["recommendation"] == "dispatch"
    assert "est_duration_min>=15" in res["triggers"]


def test_multiple_triggers_reported(engine, iid):
    res = _call(engine, iid, "dispatch_decision",
                file_count=5, parallelism=4, est_duration_min=30)
    assert res["recommendation"] == "dispatch"
    assert set(res["triggers"]) == {
        "file_count>=4", "parallelism>=3", "est_duration_min>=15",
    }


# ---------------------------------------------------------------------------
# dispatch_bash_hints verb — the cheap-context block for dispatch prompts.
# ---------------------------------------------------------------------------


def test_bash_hints_empty_when_no_args(engine, iid):
    res = _call(engine, iid, "dispatch_bash_hints")
    assert res["hints"] == []
    assert res["block"] == ""


def test_bash_hints_renders_find_per_path(engine, iid):
    res = _call(engine, iid, "dispatch_bash_hints",
                paths="agency/capabilities,tests")
    assert any("find agency/capabilities" in h for h in res["hints"])
    assert any("find tests" in h for h in res["hints"])
    assert "```bash" in res["block"]
    assert "Context — read these first" in res["block"]


def test_bash_hints_renders_grep_per_symbol(engine, iid):
    res = _call(engine, iid, "dispatch_bash_hints",
                symbols="lint_prompt,review_comment")
    assert any("grep -rn 'lint_prompt'" in h for h in res["hints"])
    assert any("grep -rn 'review_comment'" in h for h in res["hints"])


# ---------------------------------------------------------------------------
# dispatch-decision skill registration — the canon-aligned shape.
# ---------------------------------------------------------------------------


def test_skill_registered_on_delegate_ontology(engine):
    """The skill lands on `delegate.ontology.skills` so it shows up in
    the engine's skill registry and `help` discovery."""
    skills = engine.registry.ontology.skills
    assert "dispatch-decision" in skills
    sk = skills["dispatch-decision"]
    phase_names = [p["name"] for p in sk["phases"]]
    assert phase_names == [
        "estimate-shape", "apply-heuristic", "assemble-bash-hints", "decide",
    ]


def test_skill_has_hard_gate_on_decide(engine):
    sk = engine.registry.ontology.skills["dispatch-decision"]
    last = sk["phases"][-1]
    assert last["name"] == "decide"
    assert last.get("gate") == "hard"
