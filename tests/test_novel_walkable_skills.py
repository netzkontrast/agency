"""Spec 103/104 — 3 walkable skills closing goal criterion 3.

Per the goal's writing-process surface: character / world / scene
stages each need a walkable skill (phase-graph the engine walker
delivers one phase at a time, with a hard-elicit terminator).

- character-architect (4 phases) — TSDP/IFS + Big Five + Enneagram +
  archetype + voice-signature; hard confirm.
- world-bible-architect (5 phases) — geography / cultures / religions
  / languages / magic_systems / axioms; hard canon-lock.
- scene-bridge-auditor (5 phases) — Q1-Q5 (purpose / POV / stakes /
  conflict / payoff) from the scene-craft canon; hard sign-off.

Per kohaerenz §05-structure-scene-coherence: scene-bridge Q1-Q5 IS the
canonical scene-coherence checklist; ships as a walkable skill rather
than verbs per the decidability brief ("tools assert structure; skills
assert meaning").
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "novel skills") -> str:
    iid = e.intent.capture(purpose, "walkable", "verified")
    e.intent.confirm(iid)
    return iid


# ─────────────────────── registration ───────────────────────


def test_three_new_skills_registered() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    for name in ("character-architect", "world-bible-architect",
                 "scene-bridge-auditor"):
        assert name in cap.ontology.skills, f"missing skill: {name}"
    e.memory.close()


# ─────────────────────── character-architect ───────────────────────


def test_character_architect_is_four_phased_with_hard_gate() -> None:
    e = _fresh()
    sk = e.ontology.skill("character-architect")
    assert sk["kind"] == "conceptualizer"
    assert len(sk["phases"]) == 4
    assert sk["phases"][-1].get("gate") == "hard"
    names = [p["name"] for p in sk["phases"]]
    assert names == ["psychology", "archetype", "voice", "confirmation"]
    e.memory.close()


def test_character_architect_walks_to_completion() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("character-architect")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"big_five": "OCEAN baseline", "enneagram": "5w4",
         "ifs_parts": "manager,exile"},
        {"jung_archetype": "Shadow", "moral_alignment": "neutral-good"},
        {"voice_signature": "wry-laconic", "register": "third-limited"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()


# ─────────────────────── world-bible-architect ───────────────────────


def test_world_bible_architect_is_five_phased_with_hard_gate() -> None:
    e = _fresh()
    sk = e.ontology.skill("world-bible-architect")
    assert sk["kind"] == "conceptualizer"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    names = [p["name"] for p in sk["phases"]]
    assert names == ["geography", "cultures", "religions-languages",
                     "magic-systems", "canon-lock"]
    e.memory.close()


def test_world_bible_architect_walks_to_completion() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("world-bible-architect")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"continents": "Aurelia", "biomes": "tundra,forest",
         "time_period": "post-cataclysm"},
        {"cultures": "Vortheim-clan,Sablestrand-republic",
         "core_values": "lineage-vs-merit"},
        {"religions": "single-god,pantheon",
         "languages": "Vor / Sable / lingua-franca"},
        {"magic_systems": "hard:rune-binding", "hard_or_soft": "hard"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes", "axioms_canon_locked": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()


# ─────────────────────── scene-bridge-auditor ───────────────────────


def test_scene_bridge_auditor_is_five_phased_with_hard_gate() -> None:
    e = _fresh()
    sk = e.ontology.skill("scene-bridge-auditor")
    assert sk["kind"] == "auditor"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    # Q1-Q5 = purpose / POV / stakes / conflict / payoff
    names = [p["name"] for p in sk["phases"]]
    assert names == ["Q1-purpose", "Q2-POV", "Q3-stakes",
                     "Q4-conflict", "Q5-payoff-and-signoff"]
    e.memory.close()


def test_scene_bridge_auditor_walks_to_completion() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("scene-bridge-auditor")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"scene_purpose": "advance MC resolve"},
        {"pov_choice": "third-limited", "narrator_voice": "wry"},
        {"stakes_internal": "MC certainty", "stakes_external": "ally trust"},
        {"conflict_axis": "MC vs IC dynamic",
         "tension_arc": "rising"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes",
                       "scene_signoff": "ship to draft"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()
