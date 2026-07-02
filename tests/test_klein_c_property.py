"""Spec 246 — dual-storyform Klein-c property tests.

The V₄ = Z₂(class) × Z₂(dynamics) structure verified as an ALGEBRAIC property
over the generated space of legal pairs (rule 8 — the pair space is derived
from the slot taxonomy, never a pinned table), plus single-slot mutation
diagnostics and the typed failure modes (degenerate set, unknown slot value).
Deterministic enumeration stands in for Hypothesis — the legal space is small
enough to sweep exhaustively (2⁸ dynamics orientations × 2 class orientations).
"""
from __future__ import annotations

import itertools
import tempfile

from agency.engine import Engine
from agency.capabilities.novel.clusters.dual_storyform import (
    _CLASS_INVERSE, _DYNAMICS_INVERSE)


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 246", "klein-c property", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


_SLOTS = sorted(_DYNAMICS_INVERSE)
_CLASS_ORIENTATIONS = [{"mc": "Mind", "os": "Psychology"},
                       {"mc": "Universe", "os": "Physics"}]


def _class_partner(c: dict) -> dict:
    return {"mc": _CLASS_INVERSE[c["mc"]], "os": _CLASS_INVERSE[c["os"]]}


def _legal_pairs(limit: int = 220):
    """Every legal (A,B) pair derived from the taxonomy: each dynamics slot
    picks an orientation of its Z₂ pair; the class picks one of two. The
    space is 2⁸×2 = 512; we sweep ≥ limit of it deterministically."""
    ordered_pairs = [sorted(_DYNAMICS_INVERSE[s]) for s in _SLOTS]
    count = 0
    for class_o in _CLASS_ORIENTATIONS:
        for bits in itertools.product((0, 1), repeat=len(_SLOTS)):
            a_dyn = {s: ordered_pairs[i][b]
                     for i, (s, b) in enumerate(zip(_SLOTS, bits))}
            b_dyn = {s: ordered_pairs[i][1 - b]
                     for i, (s, b) in enumerate(zip(_SLOTS, bits))}
            yield ({"classes": class_o, "dynamics": a_dyn},
                   {"classes": _class_partner(class_o), "dynamics": b_dyn})
            count += 1
            if count >= limit:
                return


def _set_with(e, iid, a_body, b_body):
    nid = _invoke(e, iid, "create_novel", title="P", author="X")["novel_id"]
    set_id = _invoke(e, iid, "create_storyform_set", novel_id=nid,
                     label="p")["set_id"]
    a = _invoke(e, iid, "create_storyform", novel_id=nid,
                body=a_body)["storyform_id"]
    _invoke(e, iid, "add_storyform_to_set", storyform_id=a, set_id=set_id,
            role="primary")
    b = _invoke(e, iid, "create_storyform", novel_id=nid, body=b_body,
                role="secondary")["storyform_id"]
    _invoke(e, iid, "add_storyform_to_set", storyform_id=b, set_id=set_id,
            role="secondary")
    return set_id, b


def test_every_legal_pair_satisfies_klein_c_by_construction() -> None:
    """≥200 generated legal pairs — checked as PURE data through the check's
    slot logic (one engine, one set, body swapped per pair for speed)."""
    e = _fresh()
    iid = _iid(e)
    import json
    a_body, b_body = next(_legal_pairs(1))
    set_id, b_node = _set_with(e, iid, a_body, b_body)
    a_node = next(m["id"] for m in
                  e.memory.neighbors(set_id, "MEMBER_OF", direction="in")
                  if m.get("role") == "primary")
    checked = 0
    for a_b, b_b in _legal_pairs(220):
        e.memory.update(a_node, {"body": json.dumps(a_b)})
        e.memory.update(b_node, {"body": json.dumps(b_b)})
        out = _invoke(e, iid, "check_klein_c_inversion",
                      storyform_set_id=set_id)
        assert out["passed"] is True, (a_b, b_b, out["diagnostic"])
        assert out["flip_class"] == "preserved"
        assert out["flip_dynamics"] == "preserved"
        checked += 1
    assert checked >= 200
    e.memory.close()


def test_involution_and_commutation_of_the_two_flips() -> None:
    """flip∘flip == identity (swapping A and B is also legal) and the two Z₂
    generators commute (breaking one never breaks the other)."""
    e = _fresh()
    iid = _iid(e)
    import json
    a_body, b_body = next(_legal_pairs(1))
    set_id, b_node = _set_with(e, iid, a_body, b_body)
    a_node = next(m["id"] for m in
                  e.memory.neighbors(set_id, "MEMBER_OF", direction="in")
                  if m.get("role") == "primary")
    # involution: the swapped pair is equally legal
    e.memory.update(a_node, {"body": json.dumps(b_body)})
    e.memory.update(b_node, {"body": json.dumps(a_body)})
    assert _invoke(e, iid, "check_klein_c_inversion",
                   storyform_set_id=set_id)["passed"] is True
    # commutation: break ONLY the class flip → dynamics stays preserved
    broken_class = dict(b_body, classes=dict(a_body["classes"]))
    e.memory.update(a_node, {"body": json.dumps(a_body)})
    e.memory.update(b_node, {"body": json.dumps(broken_class)})
    out = _invoke(e, iid, "check_klein_c_inversion",
                  storyform_set_id=set_id)
    assert out["flip_class"] == "broken"
    assert out["flip_dynamics"] == "preserved"
    # and vice versa: break ONLY one dynamics slot → class stays preserved
    broken_dyn = dict(b_body,
                      dynamics=dict(b_body["dynamics"],
                                    limit=a_body["dynamics"]["limit"]))
    e.memory.update(b_node, {"body": json.dumps(broken_dyn)})
    out2 = _invoke(e, iid, "check_klein_c_inversion",
                   storyform_set_id=set_id)
    assert out2["flip_class"] == "preserved"
    assert out2["flip_dynamics"] == "broken"
    e.memory.close()


def test_single_slot_mutation_names_slot_and_flip() -> None:
    e = _fresh()
    iid = _iid(e)
    import json
    a_body, b_body = next(_legal_pairs(1))
    set_id, b_node = _set_with(e, iid, a_body, b_body)
    for slot in _SLOTS:
        mutated = dict(b_body,
                       dynamics=dict(b_body["dynamics"],
                                     **{slot: a_body["dynamics"][slot]}))
        e.memory.update(b_node, {"body": json.dumps(mutated)})
        out = _invoke(e, iid, "check_klein_c_inversion",
                      storyform_set_id=set_id)
        assert out["passed"] is False
        offending = [d["slot"] for d in out["non_inverted"]]
        assert offending == [slot]               # exactly the mutation
        assert out["flip_dynamics"] == "broken"
        assert out["flip_class"] == "preserved"
        assert slot in out["diagnostic"]
        assert "dynamics" in out["diagnostic"]
    e.memory.close()


def test_failure_modes_degenerate_and_unknown_slot() -> None:
    e = _fresh()
    iid = _iid(e)
    import json
    set_id, b_node = _set_with(e, iid, {"slots": {}}, {"slots": {}})
    out = _invoke(e, iid, "check_klein_c_inversion",
                  storyform_set_id=set_id)
    assert out["passed"] is False
    assert out["diagnostic"] == "insufficient_slots"
    a_body, b_body = next(_legal_pairs(1))
    a_node = next(m["id"] for m in
                  e.memory.neighbors(set_id, "MEMBER_OF", direction="in")
                  if m.get("role") == "primary")
    e.memory.update(a_node, {"body": json.dumps(a_body)})
    weird = dict(b_body,
                 dynamics=dict(b_body["dynamics"], limit="weeklock"))
    e.memory.update(b_node, {"body": json.dumps(weird)})
    out2 = _invoke(e, iid, "check_klein_c_inversion",
                   storyform_set_id=set_id)
    assert out2["passed"] is False
    assert "unknown_slot: limit=weeklock" in out2["diagnostic"]
    e.memory.close()
