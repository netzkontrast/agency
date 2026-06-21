"""Acceptance — the pillar event bus's declarative subscriptions (Spec 349b §2).

A capability declares `subscriptions = [Subscription(...)]`; the engine bootstrap
loop reads them and registers each handler on `agency/_events.py`. Subscribers run
in ascending priority order (the §7 ordering contract).
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _events
from agency.engine import Engine

scenarios("features/events.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@given("a fresh agency engine for the bus", target_fixture="engine")
def _given_engine(engine):
    return engine


@then(parsers.parse('the bus has a subscription named "{name}" for "{event}"'))
def _has_subscription(engine, name, event):
    # tuple shape: (event, handler, once_per, once_fail_emit, name, priority)
    names = [s[4] for s in _events.subscriptions_for(event)]
    assert name in names, names


@given("two bus subscribers registered with priorities 70 and 30",
       target_fixture="prio_event")
def _register_two():
    event = "test:priority-order"

    def _hi(engine, ev):
        return "hi"

    def _lo(engine, ev):
        return "lo"

    _events.subscribe(event, _hi, name="test.hi", priority=70)
    _events.subscribe(event, _lo, name="test.lo", priority=30)
    return event


@when("the priority event is run", target_fixture="frags")
def _run_priority(prio_event):
    return _events.run(None, prio_event, {})


@then("the lower-priority fragment comes first")
def _lower_first(frags):
    assert frags == ["lo", "hi"], frags
