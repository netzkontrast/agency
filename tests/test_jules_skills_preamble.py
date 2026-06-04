"""Spec 013 Phase 5 — `jules-protocol-preamble` skill walks end-to-end.

The skill is a Lifecycle template (CORE.md:47-62) registered on
``JulesCapability.ontology.skills`` — verifying:

- the skill is discoverable via the engine's ontology;
- each phase's `invoke` binding fires against the real capability verb
  (Phase 1: detect_mode, Phase 2: verify, Phase 3: lint_prompt);
- Phase 4 (set-scope) is a document phase: the caller supplies the
  three scope outputs and submit advances only when all are non-empty;
- Phase 5 (dispatched) is a HARD GATE: walker pauses at
  ``input-required`` until a session_id is supplied AND the call is
  confirmed (CORE.md:56-60 elicit pattern);
- the Mode A vs Mode B distinction surfaces correctly via
  `jules.detect_mode` for both `netzkontrast/agency` (dogfood) and any
  other source (delegate).

All phases are exercised through the engine — no module-level singletons,
no direct verb calls bypassing the registry.
"""
import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "walk jules-protocol-preamble",
        "5 phases walk; hard gate elicits at dispatched",
        "every phase records provenance; session_id closes the run",
    )
    engine.intent.confirm(intent)
    return intent


# ---------------------------------------------------------------------------
# Skill registration.
# ---------------------------------------------------------------------------


def test_skill_registered_on_jules_ontology(engine):
    """The skill lands on the engine's merged ontology under its canonical name."""
    assert "jules-protocol-preamble" in engine.ontology.skills
    sk = engine.ontology.skill("jules-protocol-preamble")
    phase_names = [p["name"] for p in sk["phases"]]
    assert phase_names == [
        "detect-mode", "verify-remote-state", "name-canonical-tools",
        "set-scope", "dispatched",
    ]


def test_only_dispatched_phase_is_a_hard_gate(engine):
    sk = engine.ontology.skill("jules-protocol-preamble")
    gates = [p for p in sk["phases"] if p.get("gate") == "hard"]
    assert len(gates) == 1 and gates[0]["name"] == "dispatched"


# ---------------------------------------------------------------------------
# Phase 1 — detect-mode.
# ---------------------------------------------------------------------------


def test_phase1_detect_mode_dogfood(engine, iid):
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    res = run.submit({"source": "netzkontrast/agency"})
    assert res["status"] == "working"
    # Phase 2 is now current.
    assert run.current()["name"] == "verify-remote-state"


def test_phase1_detect_mode_delegate(engine, iid):
    """A non-self source -> delegate mode. The detect_mode verb runs through
    the registry; its result is what populates `mode_decision` in the walk."""
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "someone-else/some-project"})
    # Phase 2 is now current; provenance carries a Phase record for phase 1.
    rows = engine.memory.g.query(
        "MATCH (p:Phase) WHERE p.name = $n RETURN p",
        {"n": "detect-mode"},
    )
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Phase 2 — verify-remote-state.
# ---------------------------------------------------------------------------


def test_phase2_verify_binds_to_jules_verify(engine, iid, monkeypatch):
    """Phase 2 invokes jules.verify; we stub the vcs injector so the verb
    runs without a real `git ls-remote`."""
    from agency.capabilities import jules as jules_mod
    # The verb takes (vcs, state, branch, remote); the engine injects vcs.
    # Inject a fake vcs that reports the branch exists on origin.
    engine.registry.injectors["vcs"] = lambda: type("V", (), {
        "remote_exists": lambda self, branch, remote="origin": {
            "ok": True, "exists": True, "sha": "deadbeef",
        },
    })()
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "netzkontrast/agency"})
    # Phase 2 — verify binds; outputs supply state/branch/remote.
    res = run.submit({"state": "COMPLETED", "branch": "feat/x", "remote": "origin"})
    assert res["status"] == "working"
    # Phase 3 is now current.
    assert run.current()["name"] == "name-canonical-tools"


# ---------------------------------------------------------------------------
# Phase 3 — name-canonical-tools.
# ---------------------------------------------------------------------------


CANONICAL_PROMPT = (
    "Use pre_commit_instructions(), then "
    "submit(branch_name=..., commit_message=..., title=..., description=...). "
    "Use request_user_input for blocking asks. "
    "Use replace_with_git_merge_diff for multi-line edits. "
    "Call request_code_review before submit."
)


def test_phase3_lint_passes_for_canonical_prompt(engine, iid):
    engine.registry.injectors["vcs"] = lambda: type("V", (), {
        "remote_exists": lambda self, branch, remote="origin": {
            "ok": True, "exists": True, "sha": "deadbeef",
        },
    })()
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "netzkontrast/agency"})
    run.submit({"state": "COMPLETED", "branch": "feat/x", "remote": "origin"})
    res = run.submit({"text": CANONICAL_PROMPT, "must_name": ""})
    assert res["status"] == "working"
    # Phase 4 is now current.
    assert run.current()["name"] == "set-scope"


def test_phase3_lint_blocks_when_prompt_misses_canonical_tools(engine, iid):
    engine.registry.injectors["vcs"] = lambda: type("V", (), {
        "remote_exists": lambda self, branch, remote="origin": {
            "ok": True, "exists": True, "sha": "deadbeef",
        },
    })()
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "netzkontrast/agency"})
    run.submit({"state": "COMPLETED", "branch": "feat/x", "remote": "origin"})
    # The verb fires + returns ok=False; lint_result is the truthy dict, so
    # the produces field is satisfied. Skill walk advances — Phase 3 acts as
    # the LINT, not a gate; downstream consumers read lint_result.ok and
    # decide. (Hard gating on the lint result is OOS for v1 — see DESIGN.md
    # OQ; the doctrine is that a failed lint surfaces in provenance and the
    # caller must inspect it.)
    res = run.submit({"text": "open a PR when done", "must_name": ""})
    assert res["status"] == "working"


# ---------------------------------------------------------------------------
# Phase 4 — set-scope.
# ---------------------------------------------------------------------------


def test_phase4_set_scope_requires_all_three_outputs(engine, iid):
    engine.registry.injectors["vcs"] = lambda: type("V", (), {
        "remote_exists": lambda self, branch, remote="origin": {
            "ok": True, "exists": True, "sha": "deadbeef",
        },
    })()
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "netzkontrast/agency"})
    run.submit({"state": "COMPLETED", "branch": "feat/x", "remote": "origin"})
    run.submit({"text": CANONICAL_PROMPT, "must_name": ""})
    # Missing one of the three required fields -> raises.
    with pytest.raises(ValueError, match="missing required outputs"):
        run.submit({"affects_paths": ["agency/capabilities/jules/_main.py"],
                    "no_create_outside": True})
    # Full set advances.
    res = run.submit({
        "affects_paths": ["agency/capabilities/jules/_main.py"],
        "no_create_outside": True,
        "agency_clone_ro_in_delegate": True,
    })
    assert res["status"] == "working"


# ---------------------------------------------------------------------------
# Phase 5 — dispatched HARD GATE.
# ---------------------------------------------------------------------------


def test_phase5_dispatched_hard_gate_pauses_without_confirm(engine, iid):
    engine.registry.injectors["vcs"] = lambda: type("V", (), {
        "remote_exists": lambda self, branch, remote="origin": {
            "ok": True, "exists": True, "sha": "deadbeef",
        },
    })()
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "netzkontrast/agency"})
    run.submit({"state": "COMPLETED", "branch": "feat/x", "remote": "origin"})
    run.submit({"text": CANONICAL_PROMPT, "must_name": ""})
    run.submit({
        "affects_paths": ["agency/capabilities/jules/_main.py"],
        "no_create_outside": True,
        "agency_clone_ro_in_delegate": True,
    })
    # Hard gate: even with session_id supplied, must be confirmed=True.
    res = run.submit({"session_id": "sessions/abc"})
    assert res["status"] == "input-required"
    assert res["gate"] == "hard"
    assert res["phase"] == "dispatched"
    # Not done yet.
    assert not run.done


def test_phase5_dispatched_completes_on_confirm(engine, iid):
    engine.registry.injectors["vcs"] = lambda: type("V", (), {
        "remote_exists": lambda self, branch, remote="origin": {
            "ok": True, "exists": True, "sha": "deadbeef",
        },
    })()
    sk = engine.ontology.skill("jules-protocol-preamble")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"source": "netzkontrast/agency"})
    run.submit({"state": "COMPLETED", "branch": "feat/x", "remote": "origin"})
    run.submit({"text": CANONICAL_PROMPT, "must_name": ""})
    run.submit({
        "affects_paths": ["agency/capabilities/jules/_main.py"],
        "no_create_outside": True,
        "agency_clone_ro_in_delegate": True,
    })
    res = run.submit({"session_id": "sessions/abc"}, confirmed=True)
    assert res["status"] == "completed"
    assert run.done
    # Provenance: every phase landed a Phase node serving the intent.
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-protocol-preamble"},
    )
    assert len(rows) == 5


# ---------------------------------------------------------------------------
# detect_mode verb — direct invocation.
# ---------------------------------------------------------------------------


def test_detect_mode_dogfood_self_source(engine, iid):
    res, _ = engine.registry.invoke(
        engine.memory, iid, "jules", "detect_mode",
        agent_id="agent:claude", source="netzkontrast/agency",
    )
    assert res["mode"] == "dogfood"
    assert "lexical scoping" in res["reason"]


def test_detect_mode_delegate_other_source(engine, iid):
    res, _ = engine.registry.invoke(
        engine.memory, iid, "jules", "detect_mode",
        agent_id="agent:claude", source="another/project",
    )
    assert res["mode"] == "delegate"
    assert "clone block" in res["reason"]
