"""develop — the development-workflow capability.

Implements the disciplines that help build the system further, AS first-class
agency skills: each is a Lifecycle template (an ordered phase-graph ending in a
hard gate) the engine's skill walker can walk, recording every phase as
provenance. The capability OWNS these skill schemas (its `OntologyExtension`) —
adding the dev toolkit is adding this file.

Disciplines: brainstorm (discover requirements), plan (bite-sized implementation
plan), tdd (the Iron Law: RED before GREEN, enforced by ordering), debug (trace
to root cause), verify (evidence before completion), spec-panel (multi-expert
spec critique), review (request + work through findings). The matching installable
SKILL.md files live in `skills/`.
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb
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
    # the dispatch phase is BOUND to delegate.fan_out: walking review with a
    # registry dispatches a reviewer for real (a child Lifecycle + Invocation);
    # without one it degrades to a document phase. (superpowers-port Phase 1.)
    "review": {"name": "review", "kind": "discipline", "phases": [
        _phase(1, "request", ["context", "diff"]),
        {"index": 2, "name": "dispatch", "produces": ["findings"],
         "invoke": {"capability": "delegate", "verb": "fan_out"},
         "inputs": ["driver", "driver_verb", "items"]},
        _phase(3, "resolve", ["addressed"], gate="hard"),
    ]},
    # executing-plans: walk a written plan's steps with review checkpoints, never
    # claiming done without a final verification gate. (superpowers-port Phase 3.)
    "execute": {"name": "execute", "kind": "discipline", "phases": [
        _phase(1, "load", ["plan", "steps"]),
        _phase(2, "execute", ["step_results"]),
        _phase(3, "checkpoint", ["reviewed"], gate="hard"),
        _phase(4, "verify", ["all_pass"], gate="hard"),
    ]},
}


# A discipline's heavy how-to travels as an ON-DEMAND reference (T3 progressive
# disclosure via code-mode) — fetched by `reference`, never carried in any system
# prompt. Original, principle-focused notes (the knowledge travels, re-expressed).
REFERENCES: dict[str, str] = {
    "testing-skills": (
        "# Testing a discipline with subagents\n\n"
        "A discipline is only real if a fresh agent, given ONLY the discipline, follows it. Test it like code:\n"
        "- Dispatch a subagent (delegate.fan_out) into a clean context with just the phase-graph and a task that tempts a shortcut.\n"
        "- Read the recorded walk: did it reach each phase's `produces` before advancing? Did the hard gate hold?\n"
        "- A discipline that lets the agent skip a phase is a FAILING test — tighten the ordering or the gate, not the prose.\n"
        "- Turn each rationalization ('too simple to test', 'I'll verify later') into a fixture the gate must reject.\n"
    ),
    "skill-descriptions": (
        "# Writing a description that triggers\n\n"
        "A discipline is only used if its description fires at the right moment. `plugin.lint_skill` enforces the shape; the why:\n"
        "- Third person, present tense — it is read by a dispatcher, not spoken by you.\n"
        "- Lead with 'Use when …' and concrete SYMPTOMS (the error, the smell, the decision), not the solution — the reader matches on their situation.\n"
        "- Name the trigger, not the tool: 'Use when a test fails intermittently', not 'Runs the flaky-test finder'.\n"
        "- Keep it under 500 chars; specificity beats completeness.\n"
    ),
    "best-practices": (
        "# Agency authoring best practices\n\n"
        "Port discipline as STRUCTURE, not exhortation:\n"
        "- Prefer an ordered phase-graph + a hard gate over 'you MUST' prose — the agent cannot rationalize past an ordering it cannot reach.\n"
        "- Make rationalization tables into checks (a transform verb that returns violations), so judgment is code, not a plea.\n"
        "- Every unit of work is provenance: a recorded skill walk or Invocation that SERVES the intent. Discovery is search/get_schema/execute, not recall.\n"
        "- Bind a phase to a real verb where one exists so walking the discipline EXECUTES; degrade to a document phase where none does.\n"
    ),
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


class DevelopCapability(CapabilityBase):
    name = "develop"
    home = "lifecycle"
    ontology = develop_ontology

    @verb(role="transform")
    def checklist(self, discipline: str) -> dict:
        return checklist(discipline)

    @verb(role="transform")
    def reference(self, topic: str) -> dict:
        "Fetch a discipline's heavy how-to on demand (T3): testing-skills, skill-descriptions, best-practices."
        doc = REFERENCES.get(topic)
        if doc is None:
            return {"result": {"error": f"unknown reference {topic!r}", "available": sorted(REFERENCES)}}
        return {"result": {"topic": topic, "doc": doc}}
