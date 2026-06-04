"""Tests for Spec 040 — Subagent-Decision Heuristics extension.

Covers the 11 signals separately (one swing per signal) plus 5
end-to-end scenarios from the spec's §"Done When". The four original
signals (S2 file_count, S3 explore, S4 parallel, S5 duration) are
already covered by tests/test_delegate_dispatch_decision.py; this
file focuses on the new seven (S1, S6, S7, S8, S9, S10, S11) and
the new payload shape (driver, token_cost_estimate,
local_budget_token_estimate, signals_fired).
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
        "decide dispatch vs inline (extended heuristic)",
        "the 11-signal decision payload is well-formed",
        "signals_fired matches the spec's at-a-glance table",
    )
    engine.intent.confirm(intent)
    return intent


def _call(engine, iid, **kw):
    res, _inv = engine.registry.invoke(
        engine.memory, iid, "delegate", "dispatch_decision",
        agent_id="agent:claude", **kw
    )
    return res


# ---------------------------------------------------------------------------
# Payload shape (Spec 040 §Done When line 94–100).
# ---------------------------------------------------------------------------


def test_payload_has_all_six_required_keys(engine, iid):
    res = _call(engine, iid)
    for k in ("recommendation", "driver", "rationale",
              "token_cost_estimate", "local_budget_token_estimate",
              "signals_fired"):
        assert k in res, f"missing key: {k}"


def test_inline_driver_is_inline(engine, iid):
    res = _call(engine, iid)
    assert res["recommendation"] == "inline"
    assert res["driver"] == "inline"
    assert res["signals_fired"] == []
    assert res["local_budget_token_estimate"] == res["token_cost_estimate"]


# ---------------------------------------------------------------------------
# S1 — expected_return_tokens (NEW). Heavy return favours dispatch.
# ---------------------------------------------------------------------------


def test_s1_high_return_tokens_dispatches(engine, iid):
    res = _call(engine, iid, expected_return_tokens=8000)
    assert res["recommendation"] == "dispatch"
    assert any(s.startswith("S1") for s in res["signals_fired"])


def test_s1_low_return_tokens_does_not_swing(engine, iid):
    res = _call(engine, iid, expected_return_tokens=2000)
    assert res["recommendation"] == "inline"


# ---------------------------------------------------------------------------
# S6 — mutates (NEW). Disqualifier 1: mutating tasks stay inline.
# ---------------------------------------------------------------------------


def test_s6_mutates_disqualifies_even_with_positive_signals(engine, iid):
    res = _call(engine, iid,
                expected_return_tokens=10000,   # would normally dispatch
                file_count=8,                    # would normally dispatch
                mutates=True)
    assert res["recommendation"] == "inline"
    assert any("S6" in s for s in res["signals_fired"])
    assert "mutat" in res["rationale"].lower()


# ---------------------------------------------------------------------------
# S7 — read_only (NEW). Amplifies positive signals when other signals fire.
# ---------------------------------------------------------------------------


def test_s7_read_only_amplifies_when_other_signals_fire(engine, iid):
    res = _call(engine, iid, file_count=5, read_only=True)
    assert res["recommendation"] == "dispatch"
    assert any("S7" in s for s in res["signals_fired"])


def test_s7_alone_does_not_swing_decision(engine, iid):
    res = _call(engine, iid, read_only=True)
    # No other positive signal → still inline; S7 only amplifies.
    assert res["recommendation"] == "inline"


# ---------------------------------------------------------------------------
# S8 — driver_hint (NEW). Acts as tie-breaker when not in conflict.
# ---------------------------------------------------------------------------


def test_s8_driver_hint_jules_picked_when_not_conflicting(engine, iid):
    res = _call(engine, iid,
                expected_return_tokens=6000,
                driver_hint="jules")
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "jules"


def test_s8_driver_hint_local_picked_when_not_conflicting(engine, iid):
    res = _call(engine, iid, file_count=5, driver_hint="local")
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "local"


# ---------------------------------------------------------------------------
# S9 — context_overlap (NEW). Disqualifier 2a: high overlap → inline.
# ---------------------------------------------------------------------------


def test_s9_high_overlap_with_low_return_keeps_inline(engine, iid):
    res = _call(engine, iid,
                file_count=6,           # would normally dispatch
                context_overlap=0.8,    # parent already loaded the files
                expected_return_tokens=2000)
    assert res["recommendation"] == "inline"
    assert any("S9" in s for s in res["signals_fired"])


def test_s9_low_overlap_does_not_block_dispatch(engine, iid):
    res = _call(engine, iid, file_count=6, context_overlap=0.1)
    assert res["recommendation"] == "dispatch"


# ---------------------------------------------------------------------------
# S10 — cache_warmth (NEW). Disqualifier 2b: hot cache + short → inline.
# ---------------------------------------------------------------------------


def test_s10_hot_cache_with_short_duration_keeps_inline(engine, iid):
    res = _call(engine, iid,
                file_count=5,           # would normally dispatch
                cache_warmth=0.8,
                est_duration_min=5)
    assert res["recommendation"] == "inline"
    assert any("S10" in s for s in res["signals_fired"])


def test_s10_cold_cache_does_not_block_dispatch(engine, iid):
    res = _call(engine, iid, file_count=5, cache_warmth=0.0)
    assert res["recommendation"] == "dispatch"


# ---------------------------------------------------------------------------
# S11 — local_budget_relevant (NEW). Jules side-step: relaxes S1/S9/S10.
# ---------------------------------------------------------------------------


def test_s11_jules_path_relaxes_overlap_disqualifier(engine, iid):
    """Spec §"jules-outside-budget-wins": S11=False relaxes S1+S9+S10
    so a heavy-token task dispatches to Jules where it wouldn't have
    dispatched to local."""
    res = _call(engine, iid,
                expected_return_tokens=3000,    # below local cutoff
                context_overlap=0.8,             # would block local
                cache_warmth=0.8,                # would block local
                local_budget_relevant=False)
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "jules"
    assert any("S11" in s for s in res["signals_fired"])
    assert res["local_budget_token_estimate"] == 0    # Jules consumes no local budget


def test_s11_jules_path_disregards_low_return_cutoff(engine, iid):
    res = _call(engine, iid,
                expected_return_tokens=2500,    # below 5000 local cutoff
                local_budget_relevant=False)
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "jules"


# ---------------------------------------------------------------------------
# Token-cost estimates: the two-budget split.
# ---------------------------------------------------------------------------


def test_jules_dispatch_has_zero_local_budget(engine, iid):
    res = _call(engine, iid,
                expected_return_tokens=10000,
                est_duration_min=60,
                local_budget_relevant=False)
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "jules"
    assert res["local_budget_token_estimate"] == 0
    assert res["token_cost_estimate"] > 0    # total work cost is non-zero


def test_local_dispatch_has_nonzero_local_budget(engine, iid):
    res = _call(engine, iid, file_count=5, parallelism=3)
    assert res["driver"] == "local"
    assert res["local_budget_token_estimate"] > 0
    assert res["token_cost_estimate"] >= res["local_budget_token_estimate"]


# ---------------------------------------------------------------------------
# End-to-end scenarios from §"Done When" line 113–119.
# ---------------------------------------------------------------------------


def test_e2e_inline_text_task(engine, iid):
    """Small interactive task. Inline wins on every axis."""
    res = _call(engine, iid,
                expected_return_tokens=500,
                file_count=1,
                exploration_needed=False,
                parallelism=1,
                est_duration_min=2,
                read_only=True)
    assert res["recommendation"] == "inline"
    assert res["driver"] == "inline"


def test_e2e_fan_out_research(engine, iid):
    """3 parallel read-only specialists. Dispatch to local subagents."""
    res = _call(engine, iid,
                expected_return_tokens=6000,
                file_count=4,
                exploration_needed=True,
                parallelism=4,
                est_duration_min=10,
                read_only=True)
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "local"            # parallelism>=3 picks local
    assert "S4:parallel" in res["signals_fired"]


def test_e2e_single_big_analysis(engine, iid):
    """One long analysis pass. Spec line 116 expects fan-out shape
    (single big analysis means heavy + long). With ≥45min and not
    interactive → Jules path."""
    res = _call(engine, iid,
                expected_return_tokens=8000,
                file_count=12,
                exploration_needed=True,
                est_duration_min=50,
                read_only=True)
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "jules"            # ≥45min picks jules


def test_e2e_cache_warm_inline_wins(engine, iid):
    """S10 beats S2 — high file_count would normally dispatch, but a
    hot parent cache + short duration keeps it inline. Spec line 116."""
    res = _call(engine, iid,
                file_count=6,                  # S2 would dispatch
                cache_warmth=0.8,              # S10 disqualifier
                est_duration_min=5,
                expected_return_tokens=1500)
    assert res["recommendation"] == "inline"
    assert any("S10" in s for s in res["signals_fired"])


def test_e2e_jules_outside_budget_wins(engine, iid):
    """S11=False relaxes S1/S9/S10 — a task that would be too cheap to
    dispatch locally still dispatches to Jules because Jules has its own
    budget. Spec line 117–119."""
    res = _call(engine, iid,
                expected_return_tokens=2500,   # below local cutoff
                context_overlap=0.8,           # would block local
                cache_warmth=0.7,              # would block local
                est_duration_min=40,
                local_budget_relevant=False)
    assert res["recommendation"] == "dispatch"
    assert res["driver"] == "jules"
    assert res["local_budget_token_estimate"] == 0


# ---------------------------------------------------------------------------
# Skill registration: 5 phases starting with estimate-tokens-and-cache.
# ---------------------------------------------------------------------------


def test_skill_has_five_phases_with_token_cache_first(engine):
    sk = engine.registry.ontology.skills["dispatch-decision"]
    phase_names = [p["name"] for p in sk["phases"]]
    assert phase_names == [
        "estimate-tokens-and-cache",
        "estimate-shape",
        "apply-heuristic",
        "assemble-bash-hints",
        "decide",
    ]


def test_skill_decide_still_hard_gated(engine):
    sk = engine.registry.ontology.skills["dispatch-decision"]
    last = sk["phases"][-1]
    assert last["name"] == "decide"
    assert last.get("gate") == "hard"


def test_skill_phase0_produces_the_seven_new_signals(engine):
    sk = engine.registry.ontology.skills["dispatch-decision"]
    p0 = sk["phases"][0]
    assert p0["name"] == "estimate-tokens-and-cache"
    produces = set(p0["produces"])
    # The five new caller-provided signals; S6 + S7 + S8 are also new
    # but conceptually about role/hint, recorded here for one-shot capture.
    assert {"expected_return_tokens", "mutates", "read_only",
            "context_overlap", "cache_warmth",
            "local_budget_relevant"}.issubset(produces)
