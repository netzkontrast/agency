"""Spec 136 — dual-storyform architecture (post-Dramatica).

``StoryformSet`` groups N simultaneous storyforms; ``check_klein_c_inversion``
verifies the involutive V₄ = Z₂(class) × Z₂(dynamics) symmetry between the two
members; ``StoryformTransition`` records a Vortex whose legality is the KP
"no driver-flip within a storyform" rule; scenes route hard/soft between the
live storyforms; the composite check records a dual-storyform-report Artefact.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 136", "dual storyform", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


# The canonical KP slot table (spec §Fixture).
_A_BODY = {
    "classes": {"mc": "Mind", "os": "Psychology"},
    "dynamics": {"resolve": "Steadfast", "growth": "Stop",
                 "approach": "Be-er", "style": "Holistic",
                 "driver": "Decision", "limit": "Optionlock",
                 "outcome": "Success", "judgment": "Good"},
}
_B_BODY = {
    "classes": {"mc": "Universe", "os": "Physics"},
    "dynamics": {"resolve": "Change", "growth": "Start",
                 "approach": "Do-er", "style": "Linear",
                 "driver": "Action", "limit": "Timelock",
                 "outcome": "Failure", "judgment": "Bad"},
}


def _dual(e, iid):
    """novel + set + two member storyforms (A primary, B secondary)."""
    nid = _invoke(e, iid, "create_novel", title="KP", author="X")["novel_id"]
    set_id = _invoke(e, iid, "create_storyform_set", novel_id=nid,
                     label="kp-dual-A-B")["set_id"]
    a = _invoke(e, iid, "create_storyform", novel_id=nid,
                body=_A_BODY)["storyform_id"]
    _invoke(e, iid, "add_storyform_to_set", storyform_id=a,
            set_id=set_id, role="primary")
    # a second storyform on the SAME novel: `role` makes create mint a NEW
    # node instead of the legacy idempotent per-novel update (additive).
    b = _invoke(e, iid, "create_storyform", novel_id=nid, body=_B_BODY,
                role="secondary")["storyform_id"]
    assert b != a
    _invoke(e, iid, "add_storyform_to_set", storyform_id=b,
            set_id=set_id, role="secondary")
    return nid, set_id, a, b


# ── nodes / set membership ────────────────────────────────────────────────────

def test_storyform_set_and_transition_nodes_registered() -> None:
    e = _fresh()
    cap = e.registry.get("novel")
    assert "StoryformSet" in cap.ontology.nodes
    assert "StoryformTransition" in cap.ontology.nodes
    assert {"MEMBER_OF", "ROUTED_TO", "TRANSITIONS"} <= cap.ontology.edges
    e.memory.close()


def test_create_set_and_membership_with_roles() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, set_id, a, b = _dual(e, iid)
    members = e.memory.neighbors(set_id, "MEMBER_OF", direction="in")
    assert {m["id"] for m in members} == {a, b}
    assert e.memory.recall(a).get("role") == "primary"
    assert e.memory.recall(b).get("role") == "secondary"


def test_role_collision_rejected() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, set_id, a, b = _dual(e, iid)
    out = _invoke(e, iid, "add_storyform_to_set", storyform_id=b,
                  set_id=set_id, role="primary")
    assert out is None                            # typed failure


# ── klein-c inversion ─────────────────────────────────────────────────────────

def test_klein_c_passes_canonical_kp_fixture() -> None:
    e = _fresh()
    iid = _iid(e)
    _, set_id, _, _ = _dual(e, iid)
    out = _invoke(e, iid, "check_klein_c_inversion", storyform_set_id=set_id)
    assert out["passed"] is True
    assert out["class_pair"]["inverted"] is True
    assert all(v["inverted"] for v in out["dynamics"].values())
    assert out["non_inverted"] == []


def test_klein_c_fails_when_dynamics_not_inverse() -> None:
    e = _fresh()
    iid = _iid(e)
    _, set_id, _, b = _dual(e, iid)
    import json
    broken = dict(_B_BODY)
    broken["dynamics"] = dict(_B_BODY["dynamics"], outcome="Success")  # same as A
    e.memory.update(b, {"body": json.dumps(broken)})
    out = _invoke(e, iid, "check_klein_c_inversion", storyform_set_id=set_id)
    assert out["passed"] is False
    assert any(s["slot"] == "outcome" for s in out["non_inverted"])


def test_klein_c_fails_when_class_pair_same() -> None:
    e = _fresh()
    iid = _iid(e)
    _, set_id, _, b = _dual(e, iid)
    import json
    broken = dict(_B_BODY)
    broken["classes"] = {"mc": "Mind", "os": "Psychology"}   # no swap
    e.memory.update(b, {"body": json.dumps(broken)})
    out = _invoke(e, iid, "check_klein_c_inversion", storyform_set_id=set_id)
    assert out["passed"] is False
    assert out["class_pair"]["inverted"] is False


# ── transitions (Vortex) ──────────────────────────────────────────────────────

def test_transition_kind_enum_validated() -> None:
    e = _fresh()
    iid = _iid(e)
    _, set_id, _, _ = _dual(e, iid)
    out = _invoke(e, iid, "record_storyform_transition",
                  storyform_set_id=set_id, from_role="secondary",
                  to_role="primary", at_chapter=35, kind="nope")
    assert out is None


def test_transition_legality_legal_handoff_and_illegal_within() -> None:
    e = _fresh()
    iid = _iid(e)
    _, set_id, _, _ = _dual(e, iid)
    t1 = _invoke(e, iid, "record_storyform_transition",
                 storyform_set_id=set_id, from_role="secondary",
                 to_role="primary", at_chapter=35,
                 kind="operative")["transition_id"]
    legal = _invoke(e, iid, "check_driver_transition_legality",
                    transition_id=t1)
    assert legal["passed"] is True
    assert legal["verdict"] == "legal-transition"
    assert legal["from_driver"] == "Action" and legal["to_driver"] == "Decision"
    t2 = _invoke(e, iid, "record_storyform_transition",
                 storyform_set_id=set_id, from_role="primary",
                 to_role="primary", at_chapter=38,
                 kind="ontological")["transition_id"]
    illegal = _invoke(e, iid, "check_driver_transition_legality",
                      transition_id=t2)
    assert illegal["passed"] is False
    assert illegal["verdict"] == "illegal-within-storyform"


# ── scene routing ─────────────────────────────────────────────────────────────

def _scene(e, iid, nid):
    ch = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                 title="Ch")["chapter_id"]
    return _invoke(e, iid, "create_scene", chapter_id=ch, slug="s",
                   pov="third-limited")["scene_id"]


def test_route_hard_single_edge_soft_two_edges() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, set_id, a, b = _dual(e, iid)
    s1 = _scene(e, iid, nid)
    hard = _invoke(e, iid, "route_scene_storyform", scene_id=s1,
                   set_id=set_id, primary_role="primary", mode="hard")
    assert hard["routed_storyforms"] == [a]
    s2 = _scene(e, iid, nid)
    soft = _invoke(e, iid, "route_scene_storyform", scene_id=s2,
                   set_id=set_id, primary_role="primary", mode="soft",
                   secondary_role="secondary")
    assert set(soft["routed_storyforms"]) == {a, b}
    routed = e.memory.neighbors(s2, "ROUTED_TO", direction="out")
    assert len(routed) == 2


def test_route_soft_requires_distinct_secondary() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, set_id, _, _ = _dual(e, iid)
    s = _scene(e, iid, nid)
    out = _invoke(e, iid, "route_scene_storyform", scene_id=s,
                  set_id=set_id, primary_role="primary", mode="soft",
                  secondary_role="primary")
    assert out is None


# ── bridge frequency ──────────────────────────────────────────────────────────

def test_bridge_frequency_report_shares_and_curve() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, set_id, a, b = _dual(e, iid)
    # two chapters: ch1 all-hard, ch2 all-soft → monotone curve
    ch1 = _invoke(e, iid, "create_chapter", novel_id=nid, number=1,
                  title="I")["chapter_id"]
    ch2 = _invoke(e, iid, "create_chapter", novel_id=nid, number=2,
                  title="II")["chapter_id"]
    for ch, mode in ((ch1, "hard"), (ch2, "soft")):
        sid = _invoke(e, iid, "create_scene", chapter_id=ch, slug=f"s-{mode}",
                      pov="third-limited")["scene_id"]
        kw = {"secondary_role": "secondary"} if mode == "soft" else {}
        _invoke(e, iid, "route_scene_storyform", scene_id=sid, set_id=set_id,
                primary_role="primary", mode=mode, **kw)
    rep = _invoke(e, iid, "bridge_frequency_report", novel_id=nid)
    assert rep["curve_intact"] is True
    shares = [blk["soft_share"] for blk in rep["blocks"]]
    assert shares == sorted(shares)


# ── composite ────────────────────────────────────────────────────────────────

def test_dual_storyform_coherence_check_composes_and_records() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, set_id, _, _ = _dual(e, iid)
    _invoke(e, iid, "record_storyform_transition", storyform_set_id=set_id,
            from_role="secondary", to_role="primary", at_chapter=35,
            kind="operative")
    out = _invoke(e, iid, "dual_storyform_coherence_check",
                  storyform_set_id=set_id)
    assert {"passed", "members", "inversion", "transitions",
            "artefact_id"} <= set(out)
    assert len(out["members"]) == 2
    assert out["inversion"]["passed"] is True
    assert all(t["legality"]["passed"] for t in out["transitions"])
    assert e.memory.recall(out["artefact_id"]).get("kind") == \
        "dual-storyform-report"


# ── backward compatibility ────────────────────────────────────────────────────

def test_single_storyform_novel_unchanged() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "create_novel", title="Solo", author="A")["novel_id"]
    _invoke(e, iid, "create_storyform", novel_id=nid, body={"slots": {}})
    got = _invoke(e, iid, "get_storyform", novel_id=nid)
    assert got["storyform_id"]                    # legacy path untouched
