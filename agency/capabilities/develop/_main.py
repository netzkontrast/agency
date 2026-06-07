"""develop — the development-workflow capability.

Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance.

Use when: building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, or running a skill to its first hard gate.
Triggers:
- About to implement a feature or fix without a discipline
- A new capability needing a skeleton that lints clean
- A multi-phase workflow that should pause at a human gate
Red flags:
- Writing implementation before a failing test → walk capability_develop_skill_walk with tdd
- Hand-rolling a capability skeleton → use capability_develop_scaffold_capability
"""
from __future__ import annotations

from ...capability import RenderTemplates, CapabilityBase, verb
from ...ontology import OntologyExtension
from ...skill import SkillRun


def _phase(index, name, produces, gate=None, verbs=None):
    p = {"index": index, "name": name, "produces": list(produces)}
    if gate:
        p["gate"] = gate
    if verbs:                       # Spec 092 G4 — reasoning-method cues for this phase
        p["verbs"] = list(verbs)
    return p


DEV_SKILLS = {
    # Spec 092 G4 — the `intent` critical-thinking methods are surfaced as phase cues
    # at the step that needs them, so reasoning fires in the workflow instead of staying
    # a dormant capability (the methods default their subject to the serving intent).
    "brainstorm": {"name": "brainstorm", "kind": "discipline", "phases": [
        _phase(1, "explore", ["questions", "assumptions"],
               verbs=["intent.decompose", "intent.assumptions", "intent.first_principles"]),
        _phase(2, "present", ["design", "tradeoffs"],
               verbs=["intent.tradeoffs", "intent.steelman", "intent.second_order"]),
        _phase(3, "confirm", ["user_confirmed"], gate="hard"),
    ]},
    "plan": {"name": "plan", "kind": "discipline", "phases": [
        _phase(1, "map", ["files", "steps"], verbs=["intent.decompose"]),
        _phase(2, "self-review", ["gaps_checked"],
               verbs=["intent.premortem", "intent.inversion"]),
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
        _phase(1, "review", ["expert_findings"],
               verbs=["intent.steelman", "intent.assumptions", "intent.premortem"]),
        _phase(2, "synthesize", ["revised_spec"], verbs=["intent.tradeoffs"]),
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
    # Spec 041 — deepening the tdd + debug disciplines with Superpowers material
    # (knowledge re-expressed, principle-focused). Fetched on demand via develop.reference.
    "testing-anti-patterns": (
        "# Testing anti-patterns (the Red-Flags table)\n\n"
        "A test that can't fail proves nothing. Reject these rationalizations BEFORE writing impl:\n"
        "- 'I'll mock it' — mocking the thing under test asserts your mock, not the code. Mock the BOUNDARY (a Driver), never the subject.\n"
        "- 'too simple to test' — the simple path is where the silent regression hides; write the one-line test.\n"
        "- 'I'll verify later' — later never comes; RED before GREEN is the Iron Law, enforced by phase ordering.\n"
        "- 'the test passes' (but you never saw it FAIL) — a test you didn't watch fail may be asserting nothing; force the failure first.\n"
        "- pinning a live-derived number (a token count, a verb count) — gates a snapshot, not behaviour. Assert invariants + relationships (CLAUDE.md rule 8).\n"
    ),
    "debugging-anti-patterns": (
        "# Debugging discipline (the 3-fix limit → escalate)\n\n"
        "Gather evidence at the boundary, trace to the ROOT cause, fix once. The escalation rule:\n"
        "- After 3 failed fixes for the same symptom, STOP patching — the bug is architectural; re-frame, don't re-try.\n"
        "- Bisect to the polluter: find the first commit/test/input that flips the behaviour (a `find-polluter` sweep), don't guess.\n"
        "- Reproduce deterministically before fixing; a fix for a non-reproduced bug fixes nothing.\n"
        "- A flaky test is a real bug (shared state, ordering, time) — quarantine + root-cause, never `@retry`.\n"
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


def _skill_walk(ctx, name: str, inputs: dict, resume_from: str = "") -> dict:
    """The atomic walker (Spec 018 Win 1). Walk a registered skill to the first
    hard gate in ONE call, returning the documented status contract. Composes
    `SkillRun` — the boilerplate (open run, submit each phase, stop at the gate)
    collapses into this function."""
    ontology = ctx.ontology
    skills = getattr(ontology, "skills", {}) or {}
    if name not in skills:
        return {"status": "failed", "phase": None,
                "error": f"unknown skill {name!r}",
                "available": sorted(skills),
                "skill_id": None, "completed_phases": []}
    schema = ontology.skill(name)
    memory, registry, intent_id = ctx.memory, ctx.registry, ctx.intent_id
    inputs = dict(inputs or {})

    if resume_from:
        run = SkillRun.resume(memory, intent_id, schema, resume_from, registry=registry)
        confirm_gate = True            # re-entering a paused walk IS the gate confirmation
    else:
        run = SkillRun(memory, intent_id, schema, registry=registry)
        confirm_gate = False

    accumulated: dict = {}
    completed: list = []
    while not run.done:
        phase = run.current()
        is_gate = phase.get("gate") == "hard"
        confirmed = is_gate and confirm_gate
        call_outputs = {k: v for k, v in inputs.items() if v not in (None, "")}
        if is_gate and not confirmed:
            # The gate's produces are what the caller supplies on RESUME
            # (resume_with), not what's needed to REACH the pause. Fill any
            # missing produce with a placeholder so submit's missing-check
            # passes and the pause path records the blocked Gate; the
            # placeholder never persists (submit returns before the Phase
            # record on the unconfirmed-gate path).
            for k in phase["produces"]:
                call_outputs.setdefault(k, "<pending>")
        try:
            res = run.submit(call_outputs, confirmed=confirmed)
        except Exception as e:
            # A phase failed — a missing required produce OR a bound verb
            # raising. ABORT the walk (no half-applied state past the failing
            # phase) and record a failed Gate so the abort is audit provenance,
            # parallel to the C3 pause persistence (Spec 018 Win 1 contract).
            gid = memory.record("Gate", {
                "name": phase["name"], "passed": False, "paused": False,
                "evidence": f"phase {phase['name']!r} failed: {type(e).__name__}: {e}",
            })
            memory.link(run.skill_id, gid, "BLOCKED_ON")
            memory.link(gid, intent_id, "SERVES")
            return {"status": "failed", "phase": phase["name"],
                    "error": f"{type(e).__name__}: {e}",
                    "skill_id": run.skill_id, "completed_phases": completed}
        if res["status"] == "input-required":
            return {"status": "input-required", "phase": res["phase"],
                    "blocked_on": res["blocked_on"],
                    "resume_with": list(phase["produces"]),
                    "skill_id": run.skill_id,
                    "partial_outputs": accumulated}
        accumulated.update(res.get("outputs", {}))
        completed.append(res["phase"])
        if is_gate and confirmed:
            confirm_gate = False       # only the re-entered gate auto-confirms; later gates pause
    return {"status": "completed", "skill_id": run.skill_id, "outputs": accumulated}


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


def _skill_docstring_src(name: str) -> str:
    """Spec 080 — the Agent-Skill sections for a scaffolded (ping-only)
    capability, emitted INTO the module docstring (the single source). `as_
    capability` derives the SkillDoc from these, so a new cap is a complete,
    lint-clean Agent Skill by construction — no separate literal. The author
    edits the docstring as the real verbs land; `develop.validate_skill` checks it."""
    return (
        f"{name} is a scaffolded capability; replace this overview and the ping "
        f"verb with the real surface.\n\n"
        f"Use when: the {name} capability's liveness needs a check, or as the "
        f"starting point for authoring its real verbs.\n"
        f"Triggers:\n"
        f"- A liveness check for the {name} capability\n"
        f"- A starting point for authoring {name} verbs\n"
    )


def _render_light_skeleton(name: str) -> str:
    """The minimal skeleton CAPABILITY-AUTHORING.md §"Class form" specifies.
    Single verb (ping) lint-clean under all five rule families."""
    cls = _pascalcase(name)
    return (
        f"# agency-scaffold: v{SCAFFOLD_VERSION}\n"
        f'"""{name} — one-line description of what this capability is for.\n\n'
        f"{_skill_docstring_src(name)}"
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
        f"{_skill_docstring_src(name)}"
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
    render_templates = RenderTemplates.from_module(__file__)
    ontology = develop_ontology

    @verb(role="transform")
    def validate_skill(self, name: str = "") -> dict:
        """Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit.

        Spec 080 — the skill-authoring validation surface (dogfood, not a script):
        runs ``plugin.lint_skill_doc`` AND a dry-run ``emit_skill`` (which catches
        frontmatter/reference problems) against a capability's ``skill_doc``, so an
        author confirms a capability is a complete Agent Skill before commit. The
        ``authoring-capabilities`` discipline calls this before its commit gate.

        Inputs: name (capability name; "" validates ALL caps that declare a skill_doc).
        Returns: ``{ok, results: {<cap>: {ok, violations:[…], skill_doc: bool}}}`` —
                 ``ok`` is the AND across the validated caps.
        chain_next: fix violations in the capability's SkillDoc, then re-validate.
        """
        from ..plugin import lint_skill_doc
        from ...skill_emit import emit_skill
        reg = self.ctx.registry
        targets = [name] if name else sorted(reg.names())
        results: dict = {}
        for cap_name in targets:
            try:
                cap = reg.get(cap_name)
            except KeyError:
                results[cap_name] = {"ok": False, "skill_doc": False,
                                     "violations": [{"rule": "unknown-capability",
                                                     "message": f"no capability {cap_name!r}"}]}
                continue
            doc = getattr(cap, "skill_doc", None)
            if doc is None:
                # only a finding when the cap HAS verbs (a skill must document them)
                if cap.verbs:
                    results[cap_name] = {"ok": False, "skill_doc": False,
                                         "violations": [{"rule": "skill-doc-required",
                                                         "message": "capability declares verbs but no skill_doc"}]}
                continue
            res = lint_skill_doc(cap_name, doc, cap.verbs)
            violations = list(res["violations"])
            if res["ok"]:
                try:
                    emit_skill(cap_name, doc, cap.verbs)   # dry run — raises on emit-lint failure
                except Exception as ex:
                    violations.append({"rule": "emit", "message": str(ex)})
            results[cap_name] = {"ok": not violations, "skill_doc": True,
                                 "violations": violations}
        return {"result": {"ok": all(r["ok"] for r in results.values()) if results else True,
                           "results": results}}

    @verb(role="transform")
    def checklist(self, discipline: str) -> dict:
        """Project a discipline (skill walk) into a step-by-step checklist.

        Inputs: discipline (str — registered skill name).
        Returns: ``{result: [{step, gate}, …]}`` ordered by phase index.
        chain_next: walk the steps via the relevant capability verbs.
        """
        return checklist(discipline)

    @verb(role="transform")
    def reference(self, topic: str) -> dict:
        """Fetch a discipline's heavy how-to on demand (T3 disclosure).

        Inputs: topic (one of testing-skills | skill-descriptions | best-practices | …).
        Returns: ``{topic, doc}`` on hit; ``{error, available}`` on miss
                 (both at the wire — engine strips the internal envelope).
        chain_next: terminal — caller reads the doc.
        """
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
    def skill_walk(self, name: str, inputs: dict, resume_from: str = "") -> dict:
        """Walk a registered skill to the first hard gate in ONE call (the atomic walker).

        Replaces the 5× ``SkillRun(...).submit(...)`` boilerplate: supply the
        skill name + a flat ``inputs`` map (keyed by the phases' ``produces``),
        and the walker runs every plain/bound phase, executes the bound verbs,
        and PAUSES at the first hard gate. Resume by re-calling with
        ``resume_from=<skill_id>`` and the gate's ``resume_with`` keys populated
        — re-entering a paused walk confirms that gate and continues.

        Inputs: name (registered skill, e.g. 'tdd'), inputs (map of produce→value),
                resume_from (a prior skill_id to resume; "" starts fresh).
        Returns (the status contract):
          - ``{status: "completed", skill_id, outputs}``
          - ``{status: "input-required", phase, blocked_on, resume_with, skill_id, partial_outputs}``
          - ``{status: "failed", phase, error, skill_id, completed_phases}``
        chain_next: on input-required, re-call with resume_from + resume_with keys.
        """
        return _skill_walk(self.ctx, name, inputs, resume_from=resume_from)

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
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")           # Spec 058 — provenance traversal
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"result": rid}
