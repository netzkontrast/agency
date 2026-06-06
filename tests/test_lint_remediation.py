"""Spec 074 — prescriptive lint: actionable remediation + accept mechanism.

Every finding carries steps + reference (the HOW); a per-rule catalog is the
single source; an `# agency-accept-warn: <kind> <reason>` marker (+ standing
accepts for the cancelled-069 wire-form WARNs) moves a finding to `accepted` so
the open-WARN set reflects genuine work; `lint_explain(rule)` returns the recipe.
"""
from __future__ import annotations

import types

from agency.capabilities.plugin import _main as P
from agency.engine import Engine


def _cap(name, verbs):
    return types.SimpleNamespace(name=name, verbs={v: {"fn": (lambda: None), "role": "act"} for v in verbs})


# --- remediation enrichment ---------------------------------------------------

def test_finding_gains_steps_and_reference():
    raw = {"verb": None, "kind": "surface_size", "msg": "x", "fix": "y"}
    out = P._with_remediation(raw)
    assert out["kind"] == "surface_size" and out["msg"] == "x"   # additive
    assert isinstance(out["steps"], list) and out["steps"]       # the HOW
    assert out["reference"]
    assert out["severity"] == "warn"


def test_catalog_covers_every_shipped_warn_kind():
    # meta-lint: no rule ships a bare verdict (OQ1)
    e = Engine(":memory:")
    try:
        kinds = set()
        for n in e.registry.names():
            for w in P.lint_capability(e.registry.get(n)).get("warnings", []):
                kinds.add(w["kind"])
            for w in P.lint_capability(e.registry.get(n)).get("accepted", []):
                kinds.add(w["kind"])
        for w in P.lint_surface(e.registry)["warnings"] + P.lint_surface(e.registry).get("accepted", []):
            kinds.add(w["kind"])
    finally:
        e.memory.close()
    missing = [k for k in kinds if k not in P._REMEDIATION]
    assert missing == [], f"rule kinds without a remediation recipe: {missing}"


# --- accept mechanism ---------------------------------------------------------

def test_accept_marker_parsing():
    src = "code\n# agency-accept-warn: surface_size jules is legitimately broad\nmore"
    acc = P._accepted_kinds(src)
    assert "surface_size" in acc and "broad" in acc["surface_size"]


def test_standing_accepts_cover_cancelled_069_kinds():
    acc = P._accepted_kinds("")   # no markers — just the standing set
    assert "name_token_budget" in acc
    assert "bare_name_collision" in acc and "bare_name_contract_shadow" in acc


def test_lint_surface_splits_open_vs_accepted():
    e = Engine(":memory:")
    try:
        res = P.lint_surface(e.registry)
    finally:
        e.memory.close()
    open_kinds = {w["kind"] for w in res["warnings"]}
    accepted_kinds = {w["kind"] for w in res["accepted"]}
    # the cancelled-069 wire-form collisions are accepted, not open
    assert "bare_name_collision" in accepted_kinds
    assert "bare_name_collision" not in open_kinds
    # accepted findings carry their reason
    assert all(w.get("accept_reason") for w in res["accepted"])


# --- lint_explain verb --------------------------------------------------------

def test_lint_explain_returns_recipe():
    e = Engine(":memory:")
    try:
        res, _ = e.registry.invoke(e.memory, _iid(e), "plugin", "lint_explain", rule="surface_size")
        payload = res["result"] if isinstance(res, dict) and "result" in res else res
    finally:
        e.memory.close()
    assert payload["kind"] == "surface_size"
    assert payload["steps"] and payload["reference"]


def test_lint_explain_unknown_rule():
    e = Engine(":memory:")
    try:
        res, _ = e.registry.invoke(e.memory, _iid(e), "plugin", "lint_explain", rule="nope")
        payload = res["result"] if isinstance(res, dict) and "result" in res else res
    finally:
        e.memory.close()
    assert "error" in payload


def _iid(e):
    iid = e.intent.capture("p", "d", "a")
    e.intent.confirm(iid)
    return iid
