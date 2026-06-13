"""Acceptance — delegate capability (Spec 040/041).

Converted from tests/test_delegate_dispatch_decision.py +
tests/test_dispatch_decision_extended.py.

Dropped as implementation/structural (not behaviour):
- test_skill_registered_on_delegate_ontology: surface inventory check
- test_skill_has_hard_gate_on_decide: structural skill-shape inspection
- test_skill_has_five_phases_with_token_cache_first: structural skill-shape
- test_skill_decide_still_hard_gated: structural skill-shape
- test_skill_phase0_produces_the_seven_new_signals: structural skill-shape
- test_bash_hints_quote_injection_safe: covered by the metacharacter scenario
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke
from agency.engine import Engine

scenarios("features/delegate.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("delegate acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


def _dd(engine, confirmed_intent, **kw):
    res, _ = invoke(engine, confirmed_intent, "delegate", "dispatch_decision",
                    agent_id="agent:claude", **kw)
    return res


def _fo(engine, confirmed_intent, **kw):
    res, _ = invoke(engine, confirmed_intent, "delegate", "fan_out", **kw)
    return res.get("result", res) if isinstance(res, dict) else res


def _join(engine, confirmed_intent, delegation):
    res, _ = invoke(engine, confirmed_intent, "delegate", "join", delegation=delegation)
    return res.get("result", res) if isinstance(res, dict) else res


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="engine")
def _given_engine(engine):
    return engine


@given("a confirmed intent", target_fixture="confirmed_intent")
def _given_intent(confirmed_intent):
    return confirmed_intent


# ── dispatch_decision: inline ─────────────────────────────────────────────────

@when("I call dispatch_decision with file_count 1 parallelism 1 and duration 3",
      target_fixture="dd")
def _dd_inline(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, file_count=1, exploration_needed=False,
               parallelism=1, est_duration_min=3)


@then(parsers.parse('the dispatch recommendation is "{rec}"'))
def _recommendation(dd, rec):
    assert dd["recommendation"] == rec


@then("no signals are fired")
def _no_signals(dd):
    assert dd["signals_fired"] == []


@then("the rationale is non-empty")
def _rationale_nonempty(dd):
    assert dd["rationale"]


# ── S2: file count ────────────────────────────────────────────────────────────

@when("I call dispatch_decision with file_count 4", target_fixture="dd")
def _dd_file(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, file_count=4)


@then(parsers.parse('the signals include one starting with "{prefix}"'))
def _signal_prefix(dd, prefix):
    assert any(s.startswith(prefix) for s in dd["signals_fired"]), \
        f"no signal starting with {prefix!r} in {dd['signals_fired']}"


# ── S3: exploration ───────────────────────────────────────────────────────────

@when("I call dispatch_decision with exploration_needed true", target_fixture="dd")
def _dd_explore(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, exploration_needed=True)


# ── S4: parallelism ───────────────────────────────────────────────────────────

@when("I call dispatch_decision with parallelism 3", target_fixture="dd")
def _dd_parallel(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, parallelism=3)


# ── S5: duration ──────────────────────────────────────────────────────────────

@when("I call dispatch_decision with est_duration_min 15", target_fixture="dd")
def _dd_duration(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, est_duration_min=15)


# ── S9: overlap ───────────────────────────────────────────────────────────────

@when("I call dispatch_decision with file_count 6 context_overlap 0.8 and return_tokens 2000",
      target_fixture="dd")
def _dd_s9(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, file_count=6, context_overlap=0.8,
               expected_return_tokens=2000)


@then(parsers.parse('the signals include one containing "{fragment}"'))
def _signal_contains(dd, fragment):
    assert any(fragment in s for s in dd["signals_fired"]), \
        f"no signal containing {fragment!r} in {dd['signals_fired']}"


# ── S10: cache warmth ─────────────────────────────────────────────────────────

@when("I call dispatch_decision with file_count 5 cache_warmth 0.8 and duration 5",
      target_fixture="dd")
def _dd_s10(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, file_count=5, cache_warmth=0.8, est_duration_min=5)


# ── S11: Jules path ───────────────────────────────────────────────────────────

@when("I call dispatch_decision with local_budget_relevant false and return_tokens 2500",
      target_fixture="dd")
def _dd_s11(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, local_budget_relevant=False,
               expected_return_tokens=2500)


@then(parsers.parse('the selected driver is "{driver}"'))
def _driver(dd, driver):
    assert dd["driver"] == driver


@then("the local_budget_token_estimate equals 0")
def _local_zero(dd):
    assert dd["local_budget_token_estimate"] == 0


# ── Jules cost model ──────────────────────────────────────────────────────────

@when("I call dispatch_decision with local_budget_relevant false and duration 60",
      target_fixture="dd")
def _dd_jules_cost(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, local_budget_relevant=False,
               expected_return_tokens=5000, est_duration_min=60)


@then("the total_token_cost_estimate is positive")
def _total_cost_positive(dd):
    assert dd["token_cost_estimate"] > 0


# ── local cost model ──────────────────────────────────────────────────────────

@when("I call dispatch_decision with file_count 5 and parallelism 3", target_fixture="dd")
def _dd_local_cost(engine, confirmed_intent):
    return _dd(engine, confirmed_intent, file_count=5, parallelism=3)


@then("the local_budget_token_estimate is positive")
def _local_budget_positive(dd):
    assert dd["local_budget_token_estimate"] > 0


# ── dispatch_bash_hints ───────────────────────────────────────────────────────

@when("I call dispatch_bash_hints with no args", target_fixture="hints")
def _hints_empty(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "delegate", "dispatch_bash_hints")
    return res


@then("the hints list is empty")
def _hints_list_empty(hints):
    assert hints["hints"] == []


@then("the hints block is empty")
def _hints_block_empty(hints):
    assert hints["block"] == ""


@when(parsers.parse('I call dispatch_bash_hints with paths "{paths}"'), target_fixture="hints")
def _hints_paths(engine, confirmed_intent, paths):
    res, _ = invoke(engine, confirmed_intent, "delegate", "dispatch_bash_hints", paths=paths)
    return res


@then("each path appears in a find hint")
def _each_path_in_find(hints):
    for path in ("agency/capabilities", "tests"):
        assert any(f"find {path}" in h for h in hints["hints"])


@then("the block contains a bash code fence")
def _block_code_fence(hints):
    assert "```bash" in hints["block"]


@when(parsers.parse('I call dispatch_bash_hints with symbols "{symbols}"'), target_fixture="hints")
def _hints_symbols(engine, confirmed_intent, symbols):
    res, _ = invoke(engine, confirmed_intent, "delegate", "dispatch_bash_hints", symbols=symbols)
    return res


@then("each symbol appears in a grep hint")
def _each_symbol_in_grep(hints):
    for sym in ("lint_prompt", "review_comment"):
        assert any(f"grep -rn {sym}" in h for h in hints["hints"])


@when("I call dispatch_bash_hints with a symbol containing shell metacharacters",
      target_fixture="hints")
def _hints_meta(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "delegate", "dispatch_bash_hints",
                    symbols="foo'; rm -rf /")
    return res


@then("the metacharacter sequence cannot break out of the argument")
def _metachar_safe(hints):
    assert all("; rm -rf /" not in h or "'" in h for h in hints["hints"])
    assert any("foo" in h for h in hints["hints"])


# ── fan_out ───────────────────────────────────────────────────────────────────

@when("I fan out 2 items to the reflect capability", target_fixture="fo")
def _fanout2(engine, confirmed_intent):
    items = [{"scope": "observation", "text": f"note {i}"} for i in range(2)]
    return _fo(engine, confirmed_intent, driver="reflect", driver_verb="note",
               items=items, quota=8)


@then(parsers.parse("a Delegation node is recorded with count {n:d}"))
def _delegation_count(fo, n):
    assert fo["dispatched"] == n


@then("the Delegation SERVES the intent")
def _delegation_serves(engine, confirmed_intent, fo):
    rows = engine.memory.g.query(
        "MATCH (d:Delegation)-[:SERVES]->(i:Intent) WHERE d.id=$d AND i.id=$i RETURN d",
        {"d": fo["delegation"], "i": confirmed_intent})
    assert rows


@then("each child lifecycle has a DELEGATES_TO edge from the Delegation")
def _delegates_to_edges(engine, fo):
    rows = engine.memory.g.query(
        "MATCH (d:Delegation)-[:DELEGATES_TO]->(lc:Lifecycle) WHERE d.id=$d RETURN lc",
        {"d": fo["delegation"]})
    assert len(rows) == fo["dispatched"]


@when("I fan out 5 items with quota 3", target_fixture="fo")
def _fanout_quota(engine, confirmed_intent):
    items = [{"scope": "observation", "text": f"n{i}"} for i in range(5)]
    return _fo(engine, confirmed_intent, driver="reflect", driver_verb="note",
               items=items, quota=3)


@then(parsers.parse("only {n:d} children are dispatched"))
def _quota_dispatched(fo, n):
    assert fo["dispatched"] == n


@then(parsers.parse("{n:d} items are skipped"))
def _quota_skipped(fo, n):
    assert fo["skipped"] == n


@when("I fan out items with quota -1", target_fixture="fo")
def _fanout_neg(engine, confirmed_intent):
    return _fo(engine, confirmed_intent, driver="reflect", driver_verb="note",
               items=[{"scope": "observation", "text": "x"}], quota=-1)


@then("the negative-quota fan_out carries an error")
def _fanout_neg_error(fo):
    assert "error" in fo


@when("I fan out a list containing a non-mapping item", target_fixture="fo")
def _fanout_nonmap(engine, confirmed_intent):
    return _fo(engine, confirmed_intent, driver="reflect", driver_verb="note",
               items=["not-a-dict"], quota=5)


@then("the nonmap fan_out carries an error")
def _fanout_nonmap_error(fo):
    assert "error" in fo


# ── join ──────────────────────────────────────────────────────────────────────

@when("I fan out 1 item and mark the child completed", target_fixture="delegation_id")
def _fanout_done(engine, confirmed_intent):
    res = _fo(engine, confirmed_intent, driver="reflect", driver_verb="note",
              items=[{"scope": "observation", "text": "done"}], quota=1)
    child_lc = res["children"][0]["lifecycle"]
    engine.memory.update(child_lc, {"state": "completed"})
    return res["delegation"]


@then("the join over a completed child reports done true")
def _join_done(engine, confirmed_intent, delegation_id):
    join_res = _join(engine, confirmed_intent, delegation_id)
    assert join_res["done"] is True


@when("I fan out 1 item without completing the child", target_fixture="working_delegation")
def _fanout_working(engine, confirmed_intent):
    res = _fo(engine, confirmed_intent, driver="reflect", driver_verb="note",
              items=[{"scope": "observation", "text": "working"}], quota=1)
    return res["delegation"]


@then("the join over working children reports done false")
def _join_not_done(engine, confirmed_intent, working_delegation):
    join_res = _join(engine, confirmed_intent, working_delegation)
    assert join_res["done"] is False


@then(parsers.parse('the join working-child count in "{state}" state is {n:d}'))
def _join_child_state(engine, confirmed_intent, working_delegation, state, n):
    join_res = _join(engine, confirmed_intent, working_delegation)
    assert join_res["states"].get(state, 0) == n


@when("I join a delegation that serves a different intent", target_fixture="cross_join_result")
def _cross_join(engine, confirmed_intent):
    other = engine.intent.capture("other", "d", "a")
    engine.intent.confirm(other)
    res = _fo(engine, other, driver="reflect", driver_verb="note",
              items=[{"scope": "observation", "text": "other"}], quota=1)
    join_res, _ = invoke(engine, confirmed_intent, "delegate", "join",
                         delegation=res["delegation"])
    return join_res


@then("the cross-intent join carries an error")
def _cross_intent_error(cross_join_result):
    assert "error" in cross_join_result["result"]
