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
    # without one it degrades to a document phase.
    "review": {"name": "review", "kind": "discipline", "phases": [
        _phase(1, "request", ["context", "diff"]),
        {"index": 2, "name": "dispatch", "produces": ["findings"],
         "invoke": {"capability": "delegate", "verb": "fan_out"},
         "inputs": ["driver", "driver_verb", "items"]},
        _phase(3, "resolve", ["addressed"], gate="hard"),
    ]},
    # executing-plans: walk a written plan's steps with review checkpoints, never
    # claiming done without a final verification gate.
    "execute": {"name": "execute", "kind": "discipline", "phases": [
        _phase(1, "load", ["plan", "steps"]),
        _phase(2, "execute", ["step_results"]),
        _phase(3, "checkpoint", ["reviewed"], gate="hard"),
        _phase(4, "verify", ["all_pass"], gate="hard"),
    ]},
    # Plan/024 PR-A — capability authoring: scaffold then lint behind a
    # hard gate. Phase 2 + 4 are BOUND (the walker runs the verbs, not
    # documents them); phase 4 binds to plugin.lint_capability per panel
    # F5a (no develop wrapper — natural home is `plugin` next to
    # lint_skill). docs/vision/CAPABILITY-AUTHORING.md is what phase 1
    # has the author read; the lint phase 4 ENFORCES it.
    "authoring-capabilities": {"name": "authoring-capabilities",
                               "kind": "authoring", "phases": [
        _phase(1, "research", ["read_doctrine"]),
        {"index": 2, "name": "scaffold", "produces": ["skeleton"],
         "invoke": {"capability": "develop", "verb": "scaffold_capability"},
         "inputs": ["name", "kind", "base_dir"]},
        _phase(3, "author", ["verbs_written"]),
        {"index": 4, "name": "lint", "produces": ["lint_result"],
         "invoke": {"capability": "plugin", "verb": "lint_capability"},
         "inputs": ["name"]},
        _phase(5, "token-check", ["budget_ok"]),
        _phase(6, "commit", ["reflection_recorded"], gate="hard"),
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


# ---- Plan/024 PR-A — scaffold_capability ----------------------------------
#
# The scaffolder's output IS the discipline's promise: a new capability
# author runs `develop.scaffold_capability(name, kind)` and the resulting
# file lints CLEAN in block mode by construction. CAPABILITY-AUTHORING.md
# §"Capability skeleton" is the source of truth; this module renders it.

SCAFFOLD_VERSION = 1

_SUPPORTED_KINDS = ("light", "medium", "heavy")


def _pascalcase(name: str) -> str:
    """`my-cap` → `MyCapCapability`. The class name convention every
    skeleton uses (matches reflect/develop/plugin precedent)."""
    parts = [p for p in name.replace("_", "-").split("-") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) + "Capability"


def _render_light_skeleton(name: str) -> str:
    """The minimal skeleton CAPABILITY-AUTHORING.md §"Class form" specifies.
    Single verb (ping) lint-clean under all five rule families."""
    cls = _pascalcase(name)
    return (
        f"# agency-scaffold: v{SCAFFOLD_VERSION}\n"
        f'"""{name} — one-line description of what this capability is for.\n\n'
        f"CAPABILITY-AUTHORING.md is the doctrine this skeleton lints against.\n"
        f'"""\n'
        f"from agency.capability import CapabilityBase, verb\n"
        f"from agency.ontology import OntologyExtension\n"
        f"\n"
        f"\n"
        f"class {cls}(CapabilityBase):\n"
        f'    name = "{name}"\n'
        f'    home = "capability"\n'
        f"    ontology = OntologyExtension()\n"
        f"\n"
        f'    @verb(role="transform")\n'
        f"    def ping(self) -> dict:\n"
        f'        """Return a sentinel for liveness checks.\n'
        f"\n"
        f"        Inputs: (none).\n"
        f'        Returns: {{result: "pong"}}.\n'
        f"        chain_next: (terminal).\n"
        f'        """\n'
        f'        return {{"result": "pong"}}\n'
    )


def _render_medium_skeleton(name: str) -> str:
    """Light + ontology stubs (nodes/edges/schemas/templates). The
    skeleton flags them as TODO so author fills in the data shape, but
    the file lints clean as-shipped (empty stubs are valid)."""
    cls = _pascalcase(name)
    return (
        f"# agency-scaffold: v{SCAFFOLD_VERSION}\n"
        f'"""{name} — one-line description.\n\n'
        f"Medium scaffold: owns ontology fragment (node types, schemas,\n"
        f"templates). Fill in the stubs below per CAPABILITY-AUTHORING.md.\n"
        f'"""\n'
        f"from agency.capability import CapabilityBase, verb\n"
        f"from agency.ontology import OntologyExtension\n"
        f"\n"
        f"\n"
        f"class {cls}(CapabilityBase):\n"
        f'    name = "{name}"\n'
        f'    home = "capability"\n'
        f"    ontology = OntologyExtension(\n"
        f"        # TODO: declare this capability's node types here\n"
        f"        nodes={{}},\n"
        f"        edges=set(),\n"
        f"        schemas={{}},\n"
        f"        templates={{}},\n"
        f"    )\n"
        f"\n"
        f'    @verb(role="transform")\n'
        f"    def ping(self) -> dict:\n"
        f'        """Return a sentinel for liveness checks.\n'
        f"\n"
        f"        Inputs: (none).\n"
        f'        Returns: {{result: "pong"}}.\n'
        f"        chain_next: (terminal).\n"
        f'        """\n'
        f'        return {{"result": "pong"}}\n'
    )


def _heavy_init_src(name: str) -> str:
    """The folder-form __init__.py re-export — Hint #1's canonical pattern."""
    cls = _pascalcase(name)
    return (
        f"# agency-scaffold: v{SCAFFOLD_VERSION}\n"
        f'"""{name} subpackage — folder-form capability (Spec 016 Hint #1).\n\n'
        f"This __init__ re-exports the {cls} class so discover() finds it\n"
        f"identically to a single-file capability.\n"
        f'"""\n'
        f"from .{name.replace('-', '_')} import {cls}  # noqa: F401\n"
    )


def scaffold_capability(name: str, kind: str = "light", base_dir=None) -> dict:
    """Emit a Spec-024 / Spec-016 compliant capability skeleton at base_dir.

    Inputs: name (str — kebab-case), kind ("light"|"medium"|"heavy"),
            base_dir (str — defaults to agency/capabilities/).
    Returns: {result: <path>, artefact: {kind, name, path, scaffold_version}}.
    chain_next: plugin.lint_capability(name) — the discipline's phase 4
                runs this immediately to verify the scaffold lints clean.
    """
    import os

    if kind not in _SUPPORTED_KINDS:
        return {"status": "input-required",
                "reason": f"unknown kind {kind!r}; expected one of {_SUPPORTED_KINDS}",
                "blocked_on": "scaffold_kind",
                "resume_with": ["kind"]}

    base = base_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "capabilities",
    )
    os.makedirs(base, exist_ok=True)

    if kind == "heavy":
        folder = os.path.join(base, name)
        os.makedirs(folder, exist_ok=True)
        init_path = os.path.join(folder, "__init__.py")
        impl_path = os.path.join(folder, f"{name.replace('-', '_')}.py")
        with open(init_path, "w") as f:
            f.write(_heavy_init_src(name))
        with open(impl_path, "w") as f:
            f.write(_render_light_skeleton(name))
        path = folder
    else:
        renderer = _render_medium_skeleton if kind == "medium" else _render_light_skeleton
        path = os.path.join(base, f"{name}.py")
        with open(path, "w") as f:
            f.write(renderer(name))

    return {
        "result": path,
        "artefact": {
            "kind": "capability-scaffold",
            "name": name,
            "path": path,
            "scaffold_version": SCAFFOLD_VERSION,
        },
    }


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

    @verb(role="act")
    def scaffold_capability(self, name: str, kind: str = "light",
                            base_dir: str = "") -> dict:
        """Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton.

        Inputs: name (kebab-case), kind (light|medium|heavy), base_dir (optional).
        Returns: {result: <path>, artefact: {kind, name, path, scaffold_version}}.
        chain_next: plugin.lint_capability(name) — verify lint-clean.
        """
        return scaffold_capability(name, kind=kind,
                                   base_dir=base_dir or None)

    @verb(role="act")
    def record_authoring_outcome(self, name: str, kind: str = "light") -> dict:
        """Record a Reflection at the end of an authoring-capabilities walk.

        The authoring-capabilities discipline's phase 6 (hard gate) is the
        commit boundary; the caller confirms then invokes this verb to write
        a `Reflection{scope:"observation"}` SERVING the calling intent. The
        observation surfaces back into future authoring walks (the
        self-improvement loop closes when Spec 014 promotes them to spec
        amendments).

        Inputs: name (capability name authored), kind (scaffold kind).
        Returns: {result: <reflection_id>}.
        chain_next: (terminal — discipline closes here).
        """
        text = (f"Authored capability {name!r} (kind={kind}) via the "
                f"authoring-capabilities discipline. Scaffold + lint cleanly "
                f"passed; reflection recorded for the self-improvement loop.")
        rid = self.ctx.record("Reflection", {
            "scope": "observation",
            "text": text,
        })
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"result": rid}
