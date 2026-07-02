"""Spec 145 — novel pre-flight composite skill.

The daily-driver: one read-only readiness audit across the 137–144 stack —
five verdicts, one {ready, blockers, warnings}, a pre-flight Artefact, and
the walkable novel-preflight skill with its voice-ready hard gate.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 145", "preflight", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, cap, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return r


def _ready_stack(e, iid):
    """A fixture novel staged to PASS the pre-flight."""
    nid = _invoke(e, iid, "novel", "create_novel", title="KP",
                  author="A")["novel_id"]
    sys_id = _invoke(e, iid, "novel", "create_character_system",
                     novel_id=nid, name="Kael")["system_id"]
    lex = _invoke(e, iid, "novel", "add_alter", system_id=sys_id,
                  name="Lex", category="anp", layer="layer-1",
                  function="Rationalist", taboo_rules="gonna")["alter_id"]
    v = _invoke(e, iid, "novel", "create_voice_profile", character_id=lex,
                sentence_avg_target=10.0,
                sentence_avg_stddev=3.0)["profile_id"]
    _invoke(e, iid, "novel", "assign_voice_to_alter", alter_id=lex,
            voice_profile_id=v)
    _invoke(e, iid, "novel", "define_mode_block", novel_id=nid,
            label="Akt I", mode="linear-introspective", from_chapter=1,
            to_chapter=12)
    _invoke(e, iid, "novel", "create_storyform", novel_id=nid,
            body={"slots": {}})
    _invoke(e, iid, "novel", "register_project_rule", novel_id=nid,
            rule_id="R-5", name="polarity", severity="critical",
            predicate_kind="mutual-exclusion",
            params={"set_a": ["cold ozone"], "set_b": ["warm skin"]})
    _invoke(e, iid, "novel", "set_reveal_rule", novel_id=nid,
            fact="phoenix", tier="reader", may_know_from_chapter=13)
    ch = _invoke(e, iid, "novel", "create_chapter", novel_id=nid, number=2,
                 title="Ch 2")["chapter_id"]
    sid = _invoke(e, iid, "novel", "create_scene", chapter_id=ch, slug="s",
                  pov="first", pov_character_id=lex)["scene_id"]
    _invoke(e, iid, "novel", "integrate_scene_body", scene_id=sid,
            body="The garden held its breath under the rain.")
    return nid, ch, sid, lex


def test_preflight_ready_on_staged_stack() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, ch, sid, lex = _ready_stack(e, iid)
    out = _invoke(e, iid, "novel", "preflight_report", scene_id=sid)
    assert out["ready"] is True, out["blockers"]
    assert out["blockers"] == []
    v = out["verdicts"]
    assert v["briefing_ready"]["passed"] is True
    assert v["canon_clean"]["passed"] is True
    assert v["reveal_clear"]["passed"] is True
    assert v["r_rules_clean"]["passed"] is True
    assert v["voice_ready"]["passed"] is True
    assert v["voice_ready"]["alter_id"] == lex
    assert e.memory.recall(out["artefact_id"]).get("kind") == "pre-flight"


def test_preflight_collects_blockers_across_the_stack() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, ch, sid, lex = _ready_stack(e, iid)
    # break three layers at once
    entry = _invoke(e, iid, "novel", "create_codex_entry", novel_id=nid,
                    slug="gap", name="Gap", kind="concept",
                    body="?")["entry_id"]
    _invoke(e, iid, "novel", "set_canon_status", node_id=entry,
            status="gap")
    _invoke(e, iid, "novel", "integrate_scene_body", scene_id=sid,
            body="[Nyx]: cold ozone met warm skin as the phoenix rose.")
    out = _invoke(e, iid, "novel", "preflight_report", scene_id=sid)
    assert out["ready"] is False
    phases = {b["phase"] for b in out["blockers"]}
    assert {"canon-clean", "reveal-clear", "r-rules-dry-run",
            "voice-ready"} <= phases
    assert out["verdicts"]["r_rules_clean"]["critical"] >= 1
    assert "phoenix" in out["verdicts"]["reveal_clear"]["premature_facts"]


def test_unvoiced_alter_blocks_voice_ready() -> None:
    e = _fresh()
    iid = _iid(e)
    nid = _invoke(e, iid, "novel", "create_novel", title="K",
                  author="A")["novel_id"]
    ch = _invoke(e, iid, "novel", "create_chapter", novel_id=nid, number=1,
                 title="Ch")["chapter_id"]
    sid = _invoke(e, iid, "novel", "create_scene", chapter_id=ch, slug="s",
                  pov="first")["scene_id"]
    out = _invoke(e, iid, "novel", "preflight_report", scene_id=sid)
    assert out["ready"] is False
    assert any(b["phase"] == "voice-ready" and "no fronting alter"
               in b["reason"] for b in out["blockers"])


def test_preflight_skill_registered_with_voice_gate() -> None:
    e = _fresh()
    skills = e.registry.get("novel").ontology.skills
    assert "novel-preflight" in skills
    phases = skills["novel-preflight"]["phases"]
    assert len(phases) == 5
    gates = [p["name"] for p in phases if p.get("gate") == "hard"]
    assert gates == ["voice-ready"]
    # all phases are read-only audits — no mutating verb appears
    for p in phases:
        for v in p.get("verbs", []):
            assert not v.split(".")[-1].startswith(("create", "add",
                                                    "record", "register",
                                                    "set_", "assign"))
    e.memory.close()
