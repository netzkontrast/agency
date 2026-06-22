"""Acceptance — skill authoring grounding context (Spec 374 Slice 1).

The grounding builder (`skill_generator.ground`) reads a capability's live
surface — verbs, signatures (sans injected params), docstrings, ontology — into
a structured dict. Pure + deterministic; the no-host fallback an author reads by
hand. Assertions derive from the live registry (rule 8 — no snapshotted lists).
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when


scenarios("features/skill_author.feature")

GROUND_CAP = "analyze"


def _ground(engine, iid, capability):
    raw, _ = engine.registry.invoke(
        engine.memory, iid, "skill_generator", "ground", capability=capability)
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I ground skill authoring for the "{cap}" capability'),
      target_fixture="grounding")
def _do_ground(engine, confirmed_intent, cap):
    return _ground(engine, confirmed_intent, cap)


@when(parsers.parse('I ground skill authoring for the "{cap}" capability again'),
      target_fixture="grounding_again")
def _do_ground_again(engine, confirmed_intent, cap):
    return _ground(engine, confirmed_intent, cap)


# ── Then ──────────────────────────────────────────────────────────────────────

@then("the grounding lists exactly the live verbs of that capability")
def _lists_live_verbs(engine, grounding):
    live = set(engine.registry.get(GROUND_CAP).verbs)
    grounded = {v["name"] for v in grounding["verbs"]}
    assert grounded == live, (
        f"grounding must list exactly the live verbs; got {grounded} vs {live}")


@then("each grounded verb mirrors its live role and docstring")
def _verbs_mirror_source(engine, grounding):
    cap = engine.registry.get(GROUND_CAP)
    for v in grounding["verbs"]:
        fn = cap.verbs[v["name"]].get("fn")
        assert v["doc"] == (fn.__doc__ or ""), (
            f"verb {v['name']!r} doc must mirror the live source (one source)")
        assert v["role"] == cap.role(v["name"]), (
            f"verb {v['name']!r} role must mirror the live registry")
        assert v["signature"].startswith("("), (
            f"verb {v['name']!r} must carry a call signature")


@then("each grounded verb signature omits the injected parameters")
def _signature_omits_injected(grounding):
    # `self` / `ctx` / declared injects are engine-supplied, not author-facing —
    # an author referencing the verb never passes them, so the grounding must not
    # advertise them.
    for v in grounding["verbs"]:
        first = v["signature"].lstrip("(").split(",", 1)[0].split(":", 1)[0].strip()
        assert first not in ("self", "ctx"), (
            f"verb {v['name']!r} signature leaks an injected param: {v['signature']}")


@then("the grounding summarises the capability's ontology")
def _has_ontology(grounding):
    assert "ontology" in grounding
    for k in ("nodes", "edges", "skills"):
        assert k in grounding["ontology"], f"ontology summary missing {k!r}"


@then("the two groundings are identical")
def _deterministic(grounding, grounding_again):
    assert grounding == grounding_again, "grounding must be deterministic (A7)"


@then("the grounding result is an error naming the unknown capability")
def _error_unknown(grounding):
    assert "error" in grounding, f"expected a typed error; got {grounding!r}"
    assert "no-such-cap" in grounding["error"]
