"""Spec 092 G2 — author-time lints for the two reserved-name collisions."""
import tempfile

import pytest

from agency.capability import CapabilityBase, verb
from agency.capabilities.plugin._main import _check_reserved_names
from agency.engine import Engine


def test_reserved_param_name_is_flagged():
    class Bad(CapabilityBase):
        name = "badparamcap"
        home = "capability"

        @verb(role="transform")
        def oops(self, intent_id: str = "") -> dict:
            """Gist. Inputs: intent_id. Returns: nothing. chain_next: none."""
            return {}

    findings = _check_reserved_names(Bad.as_capability())
    hits = [f for f in findings if f["kind"] == "reserved_param_name"]
    assert hits and hits[0]["verb"] == "oops" and hits[0]["hard"] is True


def test_string_artefact_return_key_is_flagged_as_warn():
    class Bad(CapabilityBase):
        name = "badretcap"
        home = "capability"

        @verb(role="act")
        def oops(self, x: str = "") -> dict:
            """Gist. Inputs: x. Returns: a doc. chain_next: none."""
            aid = "some-id"
            return {"result": "r", "artefact": aid}     # string under 'artefact' → collision

    findings = _check_reserved_names(Bad.as_capability())
    hits = [f for f in findings if f["kind"] == "reserved_return_key"]
    assert hits and hits[0]["hard"] is False


def test_dict_artefact_return_key_is_not_flagged():
    class Good(CapabilityBase):
        name = "goodretcap"
        home = "capability"

        @verb(role="act")
        def fine(self, x: str = "") -> dict:
            """Gist. Inputs: x. Returns: a doc. chain_next: none."""
            return {"result": "r", "artefact": {"kind": "thing", "x": x}}   # dict → OK

    findings = _check_reserved_names(Good.as_capability())
    assert not any(f["kind"] == "reserved_return_key" for f in findings)


def test_injected_param_names_are_allowed():
    # a verb may legitimately declare an inject name (vcs/runner/skills_client) as a param
    class Ok(CapabilityBase):
        name = "okinjectcap"
        home = "capability"

        @verb(role="effect", inject=["vcs"])
        def act(self, vcs, branch: str = "") -> dict:
            """Gist. Inputs: branch. Returns: ok. chain_next: none."""
            return {}

    assert _check_reserved_names(Ok.as_capability()) == []


def test_all_real_capabilities_are_collision_free():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        dirty = {n: _check_reserved_names(e.registry.get(n)) for n in e.registry.names()}
        dirty = {n: f for n, f in dirty.items() if f}
        assert dirty == {}, f"reserved-name collisions in shipped caps: {dirty}"
    finally:
        e.memory.close()
