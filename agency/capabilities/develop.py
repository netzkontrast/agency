"""develop — the development-workflow capability.

Implements the SuperClaude + superpowers development disciplines that help us
build the system further, AS first-class agency skills: each is a Lifecycle
template (an ordered phase-graph ending in a hard gate) the engine's skill walker
can walk, recording every phase as provenance. The capability OWNS these skill
schemas (its `OntologyExtension`) — adding the dev toolkit is adding this file.

Disciplines (sources): brainstorm (superpowers brainstorming · sc-brainstorm),
plan (superpowers writing-plans · sc-workflow), tdd (superpowers
test-driven-development — the Iron Law: RED before GREEN, enforced by ordering),
debug (superpowers systematic-debugging), verify (superpowers
verification-before-completion), spec-panel (sc-spec-panel), review (superpowers
requesting/receiving-code-review). The matching installable SKILL.md files live in
`skills/`.
"""
from __future__ import annotations

from ..capability import Capability
from ..ontology import OntologyExtension


def _phase(index, name, produces, gate=None):
    p = {"index": index, "name": name, "produces": list(produces)}
    if gate:
        p["gate"] = gate
    return p


DEV_SKILLS = {
    "brainstorm": {"name": "brainstorm", "kind": "discipline", "phases": [
        _phase(1, "explore", ["questions", "assumptions"]),
        _phase(2, "present", ["design", "tradeoffs"]),
        _phase(3, "confirm", ["user_confirmed"], gate="hard"),
    ]},
    "plan": {"name": "plan", "kind": "discipline", "phases": [
        _phase(1, "map", ["files", "steps"]),
        _phase(2, "self-review", ["gaps_checked"]),
        _phase(3, "approve", ["user_confirmed"], gate="hard"),
    ]},
    # the Iron Law (RED before GREEN) is enforced by the phase ordering itself.
    "tdd": {"name": "tdd", "kind": "discipline", "phases": [
        _phase(1, "red", ["failing_test"]),
        _phase(2, "green", ["implementation"]),
        _phase(3, "refactor", ["refactored"]),
        _phase(4, "verify", ["tests_pass"], gate="hard"),
    ]},
    "debug": {"name": "debug", "kind": "discipline", "phases": [
        _phase(1, "gather", ["evidence"]),
        _phase(2, "hypothesize", ["hypothesis"]),
        _phase(3, "trace", ["root_cause"]),
        _phase(4, "fix", ["fix_verified"], gate="hard"),
    ]},
    "verify": {"name": "verify", "kind": "discipline", "phases": [
        _phase(1, "identify", ["command"]),
        _phase(2, "run", ["output"]),
        _phase(3, "confirm", ["evidence_matches"], gate="hard"),
    ]},
    "spec-panel": {"name": "spec-panel", "kind": "discipline", "phases": [
        _phase(1, "review", ["expert_findings"]),
        _phase(2, "synthesize", ["revised_spec"]),
        _phase(3, "approve", ["user_confirmed"], gate="hard"),
    ]},
    "review": {"name": "review", "kind": "discipline", "phases": [
        _phase(1, "request", ["context", "diff"]),
        _phase(2, "assess", ["findings"]),
        _phase(3, "resolve", ["addressed"], gate="hard"),
    ]},
}


def checklist(discipline: str) -> dict:
    """Return a development discipline's ordered phases (its checklist). Pure
    compute over the shipped skill schemas — the agent asks 'what are the steps of
    tdd?' and gets the phase-graph back as a token-tiny delta."""
    sk = DEV_SKILLS.get(discipline)
    if not sk:
        return {"result": {"error": f"unknown discipline {discipline!r}",
                           "available": sorted(DEV_SKILLS)}}
    steps = [{"index": p["index"], "name": p["name"],
              "produces": p["produces"], "gate": p.get("gate")} for p in sk["phases"]]
    return {"result": {"discipline": discipline, "steps": steps}}


develop_ontology = OntologyExtension(skills=dict(DEV_SKILLS))

develop_capability = Capability(
    name="develop",
    home="lifecycle",
    verbs={"checklist": {"role": "transform", "fn": checklist}},
    ontology=develop_ontology,
)
