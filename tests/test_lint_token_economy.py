"""Spec 067 — lint rules that test the token-economy goals.

The executable goal-test for the token-economy cluster (Spec 066): name-token
budget, capability surface size, bare-name uniqueness, skill-surface parity. All
WARN-first (the 056/058 migration discipline); each child spec (068–071) drives
its WARN count to zero then flips its rule to BLOCK. brief-budget already ships as
Spec 023 `_check_token_budget` (parity-asserted here, not re-implemented).
"""
from __future__ import annotations

import types

from agency.capabilities.plugin import _main as P
from agency.engine import Engine


def _cap(name, verbs):
    return types.SimpleNamespace(name=name, verbs={v: {"fn": (lambda: None), "role": "act"} for v in verbs})


# --- name_token_budget --------------------------------------------------------

def test_name_token_budget_flags_long_wire_name():
    # capability_develop_record_authoring_outcome ~ 8 cl100k tokens > budget 6
    cap = _cap("develop", ["record_authoring_outcome"])
    findings = P._check_name_token_budget(cap)
    assert any(f["kind"] == "name_token_budget" for f in findings)


def test_name_token_budget_passes_short_name():
    assert P._check_name_token_budget(_cap("gate", ["check"])) == []


# --- surface_size -------------------------------------------------------------

def test_surface_size_flags_over_budget():
    cap = _cap("jules", [f"v{i}" for i in range(13)])  # 13 > 12
    findings = P._check_surface_size(cap)
    assert any(f["kind"] == "surface_size" for f in findings)


def test_surface_size_passes_at_budget():
    assert P._check_surface_size(_cap("analyze", [f"v{i}" for i in range(12)])) == []


# --- bare_name_unique (registry-level) ----------------------------------------

def _registry(cap_verbs, ontology=None):
    caps = {n: types.SimpleNamespace(name=n, verbs={v: {} for v in vs}) for n, vs in cap_verbs.items()}
    reg = types.SimpleNamespace()
    reg.names = lambda: list(caps)
    reg.get = lambda n: caps[n]
    reg.ontology = ontology
    return reg


def test_bare_name_collision_flagged():
    reg = _registry({"document": ["render"], "dogfood": ["render", "note"], "reflect": ["note"]})
    findings = P._check_bare_name_unique(reg)
    collided = {f["verb"] for f in findings if f["kind"] == "bare_name_collision"}
    assert collided == {"render", "note"}


def test_bare_name_contract_shadow_flagged():
    reg = _registry({"reflect": ["search"]})  # shadows the `search` contract tool
    findings = P._check_bare_name_unique(reg)
    assert any(f["kind"] == "bare_name_contract_shadow" and f["verb"] == "search" for f in findings)


def test_bare_name_unique_clean_when_disjoint():
    reg = _registry({"a": ["x"], "b": ["y"]})
    assert P._check_bare_name_unique(reg) == []


# --- skill_name_parity (registry-level) ---------------------------------------

def test_skill_name_parity_flags_ontology_key_without_folder():
    onto = types.SimpleNamespace(skills={"tdd": {}, "code-analysis": {}})  # tdd has no skills/tdd/ folder
    reg = _registry({"a": ["x"]}, ontology=onto)
    findings = P._check_skill_name_parity(reg)
    assert any(f["kind"] == "skill_name_parity" and "tdd" in f["msg"] for f in findings)


# --- lint_surface entry point + parity ----------------------------------------

def test_lint_surface_runs_registry_rules():
    reg = _registry({"document": ["render"], "dogfood": ["render"]},
                    ontology=types.SimpleNamespace(skills={}))
    res = P.lint_surface(reg)
    assert res["ok"] is True and res["mode"] == "warn"
    # Spec 074 — bare_name_collision is a standing-accept, so it lands in `accepted`
    # (with a reason), not the open `warnings` bucket.
    assert any(f["kind"] == "bare_name_collision" for f in res["accepted"])


def test_brief_budget_rule_is_wired():
    # Spec 023 brief budget must remain in the lint_capability pipeline (parity).
    import inspect
    src = inspect.getsource(P.lint_capability)
    assert "_check_token_budget" in src


# --- live-registry snapshot (the recorded baseline, drift-guarded) ------------

def test_live_surface_warns_match_the_known_baseline():
    # Spec 074 — the wire-form WARNs + the tracked skill divergence are now
    # ACCEPTED (standing reasons), so the OPEN set is empty and the baseline lives
    # in the `accepted` bucket. This records that the cluster's WARNs are
    # fixed-or-accepted, not lurking.
    e = Engine(":memory:")
    try:
        res = P.lint_surface(e.registry)
    finally:
        e.memory.close()
    assert res["warnings"] == []  # OPEN = none
    accepted = res["accepted"]
    collisions = {f["verb"] for f in accepted if f["kind"] == "bare_name_collision"}
    assert collisions == {"note", "render", "verify"}  # the Spec 049 §4 set
    shadows = {f["verb"] for f in accepted if f["kind"] == "bare_name_contract_shadow"}
    assert "search" in shadows
    assert any(f["kind"] == "skill_name_parity" for f in accepted)
    assert all(f.get("accept_reason") for f in accepted)  # every accept carries a reason
