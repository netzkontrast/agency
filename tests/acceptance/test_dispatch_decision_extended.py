"""Acceptance — extended dispatch_decision signals S1, S6, S7, S8 (Spec 040).

Converted from tests/test_dispatch_decision_extended.py (behaviour: the new
seven signals and the full eleven-signal payload). The four original signals
(S2 file_count, S3 explore, S4 parallel, S5 duration) are already covered by
tests/acceptance/test_delegate.py; this module adds only what was missing.

Dropped as structural/meta (not behaviour):
- test_e2e_inline_text_task / test_e2e_fan_out_research / test_e2e_single_big_analysis:
  these exercise the full Jules stub chain (complex external integration); the
  observable dispatch_decision payload shape is the same contract — already
  tested here at the pure-verb level.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/dispatch_decision_extended.feature")


# ── helpers ────────────────────────────────────────────────────────────────

def _dispatch(engine, iid, **kw):
    res, _ = invoke(engine, iid, "delegate", "dispatch_decision",
                    agent_id="agent:claude", **kw)
    return res


# ── shared When steps ──────────────────────────────────────────────────────

@when("I call dispatch_decision with no arguments", target_fixture="dd")
def _dd_none(engine, confirmed_intent):
    return _dispatch(engine, confirmed_intent)


@when(parsers.parse("I call dispatch_decision with expected_return_tokens {tokens:d}"),
      target_fixture="dd")
def _dd_return_tokens(engine, confirmed_intent, tokens):
    return _dispatch(engine, confirmed_intent, expected_return_tokens=tokens)


@when("I call dispatch_decision with mutates true and file_count 6 and return_tokens 8000",
      target_fixture="dd")
def _dd_mutates(engine, confirmed_intent):
    return _dispatch(engine, confirmed_intent,
                     mutates=True, file_count=6, expected_return_tokens=8000)


@when("I call dispatch_decision with read_only true and file_count 4",
      target_fixture="dd")
def _dd_readonly_amplifies(engine, confirmed_intent):
    return _dispatch(engine, confirmed_intent, read_only=True, file_count=4)


@when("I call dispatch_decision with read_only true and no other signals",
      target_fixture="dd")
def _dd_readonly_alone(engine, confirmed_intent):
    return _dispatch(engine, confirmed_intent, read_only=True)


@when("I call dispatch_decision with driver_hint jules and file_count 4",
      target_fixture="dd")
def _dd_hint_jules(engine, confirmed_intent):
    return _dispatch(engine, confirmed_intent, driver_hint="jules", file_count=4)


@when("I call dispatch_decision with driver_hint local and file_count 4",
      target_fixture="dd")
def _dd_hint_local(engine, confirmed_intent):
    return _dispatch(engine, confirmed_intent, driver_hint="local", file_count=4)


# ── Then steps ─────────────────────────────────────────────────────────────

@then("the payload has recommendation driver rationale token_cost_estimate "
      "local_budget_token_estimate and signals_fired")
def _payload_keys(dd):
    for k in ("recommendation", "driver", "rationale",
              "token_cost_estimate", "local_budget_token_estimate",
              "signals_fired"):
        assert k in dd, f"missing key: {k}"


@then(parsers.parse('the dispatch recommendation is "{rec}"'))
def _rec(dd, rec):
    assert dd["recommendation"] == rec, dd


@then(parsers.parse('the selected driver is "{driver}"'))
def _driver(dd, driver):
    assert dd["driver"] == driver, dd


@then("no signals are fired")
def _no_signals(dd):
    assert dd["signals_fired"] == [], dd["signals_fired"]


@then("local_budget_token_estimate equals token_cost_estimate")
def _local_eq_total(dd):
    assert dd["local_budget_token_estimate"] == dd["token_cost_estimate"], dd


@then(parsers.parse('the signals include one starting with "{prefix}"'))
def _signal_prefix(dd, prefix):
    assert any(s.startswith(prefix) for s in dd["signals_fired"]), (
        f"expected a signal starting with {prefix!r}, got {dd['signals_fired']!r}"
    )
