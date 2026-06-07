"""Spec 002 — Boundary/Driver Protocol family + DriverRegistry.

The six ad-hoc injector seams (jules/vcs/embedder/runner/token_counter/
skills_client) unify into one named table reached via ctx.get_driver(name).
"""
import pytest

from agency.capability import (Boundary, CapabilityContext, Driver, DriverMissing,
                               DriverRegistry)
from agency.engine import Engine


def test_registry_register_get_has_names():
    r = DriverRegistry()
    assert r.names() == [] and not r.has("x")
    sentinel = object()
    r.register("x", sentinel)
    assert r.has("x") and r.names() == ["x"]
    assert r.get("x") is sentinel


def test_get_missing_raises_driver_missing_a_lookuperror():
    r = DriverRegistry()
    with pytest.raises(DriverMissing):
        r.get("nope")
    assert issubclass(DriverMissing, LookupError)        # legacy except-paths still catch


def test_engine_unifies_the_six_boundaries():
    e = Engine(":memory:")
    try:
        for n in ("jules", "vcs", "embedder", "runner", "token_counter", "skills_client"):
            assert e.drivers.has(n), f"missing driver {n!r}"
        # injectors are DERIVED from the registry — one source of truth
        assert e.registry.injectors["vcs"]() is e.drivers.get("vcs")
        assert e.registry.injectors["client"]() is e.drivers.get("jules")
    finally:
        e.memory.close()


def test_drivers_kwarg_overrides_a_boundary():
    sentinel = object()
    e = Engine(":memory:", drivers={"jules": sentinel})
    try:
        assert e.drivers.get("jules") is sentinel
        assert e.registry.injectors["client"]() is sentinel
    finally:
        e.memory.close()


def test_legacy_kwarg_still_registers_as_a_driver():
    stub = object()
    e = Engine(":memory:", jules_client=stub)             # deprecated forwarder kept (D-4)
    try:
        assert e.drivers.get("jules") is stub
    finally:
        e.memory.close()


def test_ctx_get_driver_reaches_the_registry():
    e = Engine(":memory:")
    try:
        iid = e.intent.capture("t", "get a driver", "ok")
        e.intent.confirm(iid)
        ctx = CapabilityContext(memory=e.memory, ontology=e.ontology, registry=e.registry,
                                intent_id=iid, drivers=e.drivers)
        assert ctx.get_driver("vcs") is e.drivers.get("vcs")
        with pytest.raises(DriverMissing):
            ctx.get_driver("nope")
    finally:
        e.memory.close()


def test_markers_impose_no_behaviour_change():
    # memberless runtime_checkable Protocols → no-op isinstance (PEP 544): the
    # concrete clients need NO base-class change to be Boundaries/Drivers.
    assert isinstance(object(), Boundary)
    assert isinstance(object(), Driver)
