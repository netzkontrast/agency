# agency-scaffold: v1
# agency-accept-warn: surface_size — develop is the development-workflow HUB: plan
# authoring (draft_plan/record_step_outcome/plan_status), the skill walker
# (skill_walk/checklist/reference), capability authoring (scaffold_capability/
# validate_skill/optimize_skilldoc/reload), the session driver
# (session_init/session_check/session_resume/mode_select), and estimate/index/
# ping. 17 distinct primitives > 12 budget by design — each pulls a separate
# workflow primitive; consolidating would re-grow kw-arg signatures. Tiered
# discovery (Spec 068) covers the cost.
"""develop — the development-workflow capability.

Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance. For ANY code lookup — where/how a symbol works, a call path X→Y, blast radius — reach for codegraph FIRST (`codegraph explore "<q>"` is the one-call primary: relevant source + call paths + impact; `codegraph node <sym|file>` for one symbol's source + caller/callee trail; `codegraph query <name>` to locate) BEFORE grep/Read — it IS the index, so a grep/Read sweep re-does its work. Full token-efficient guide: `develop.reference("codegraph")`.

Use when: building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, running a skill to its first hard gate, reloading edited capability code mid-session, or looking up code (use codegraph).
Triggers:
- About to implement a feature or fix without a discipline
- A new capability needing a skeleton that lints clean
- A multi-phase workflow that should pause at a human gate
- A capability was just edited or scaffolded and needs to go live without a restart
- A 'where/how does X work', call-path, or blast-radius question → `codegraph explore "<q>"` (one call), not a grep/Read sweep
Red flags:
- Writing implementation before a failing test → walk capability_develop_skill_walk with tdd
- Hand-rolling a capability skeleton → use capability_develop_scaffold_capability
- Restarting the session to pick up a capability edit → develop.reload re-imports it in place
- grep/Read loop to understand code while `.codegraph/` exists → `codegraph explore` already indexed it (`develop.reference("codegraph")`)
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, RenderTemplates, CapabilityBase, verb
from ...ontology import OntologyExtension
from ...skill import SkillRun, phase as _phase  # Spec 286 — shared phase() builder


# Spec 287 — PlanStep execution states (closed enum; ontology-enforced).
PLAN_STEP_STATES = frozenset({"pending", "done", "blocked", "skipped"})


DEV_SKILLS = {
    # Spec 092 G4 — the `intent` critical-thinking methods are surfaced as phase cues
    # at the step that needs them, so reasoning fires in the workflow instead of staying
    # a dormant capability (the methods default their subject to the serving intent).
    "brainstorm": {"name": "brainstorm", "kind": "discipline", "phases": [
        # Spec 285 Part B — `explore` is a generative phase: when a
        # sampling-capable host is bound, the engine drafts the opening
        # `questions` via MCP sampling instead of pausing for the agent to
        # supply them (graceful pause when no host). `assumptions` is still
        # the agent's to fill (the design judgement the walk preserves).
        _phase(1, "explore", ["questions", "assumptions"],
               verbs=["intent.decompose", "intent.assumptions", "intent.first_principles"],
               sample={"produces_key": "questions",
                       "system": "You are a rigorous design partner. List the "
                                 "sharpest open questions for the stated intent.",
                       "prompt": "Enumerate the key open questions to resolve "
                                 "before designing this. One per line."}),
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
    # Spec 287 — first-class plan-authoring → execution-with-checkpoints
    # (superpowers writing-plans + executing-plans + subagent-driven-development;
    # superclaude sc-workflow + sc-task). The plan is graph provenance, not a
    # file (rule 2): the draft-plan phase is BOUND to develop.draft_plan, which
    # mints a Plan + PlanStep nodes SERVING the intent. Hard gates: plan
    # sign-off, the per-run checkpoint, and final synthesis. The execute-step
    # phase cues delegate.dispatch_decision (Spec 040) — delegate vs. inline per
    # the 11 signals.
    "plan-execute": {"name": "plan-execute", "kind": "discipline", "phases": [
        _phase(1, "frame", ["requirements"],
               verbs=["intent.decompose", "intent.assumptions"]),
        {"index": 2, "name": "draft-plan", "produces": ["plan"],
         "invoke": {"capability": "develop", "verb": "draft_plan"},
         "inputs": ["title", "steps"]},
        _phase(3, "plan-signoff", ["user_confirmed"], gate="hard"),
        _phase(4, "execute-step", ["step_results"],
               verbs=["delegate.dispatch_decision"]),
        _phase(5, "checkpoint", ["reviewed"], gate="hard"),
        _phase(6, "synthesize", ["summary"], gate="hard"),
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
    # CodeGraph — code-intelligence tool (a pre-built symbol/call/impact graph).
    # The complete vendor docs, refactored token-efficient + decision-focused; the
    # heavy how-to travels on demand via `develop.reference("codegraph")`, never in
    # any system prompt. Use BEFORE grep/find/Read for understanding/locating code.
    "codegraph": (
        "# CodeGraph — code intelligence (use BEFORE grep/find/Read)\n\n"
        "A pre-built SQLite knowledge graph of every symbol, edge, and file (FTS5 "
        "+ call graph + impact radius). When a `.codegraph/` dir exists it answers "
        "\"what/where/how does X work\", call paths, and blast-radius in ONE call — "
        "sub-ms, 100% local, auto-synced on save. Reach for it BEFORE grep/find/Read "
        "to understand or locate code. (This repo is indexed — `.codegraph/` is present.)\n\n"
        "## The rule\n"
        "It IS the index, so a grep/read loop repeats work it already did:\n"
        "- Answer structural questions DIRECTLY; treat returned source as already "
        "read — don't re-verify with grep.\n"
        "- Don't fan code exploration out to a file-reading sub-agent — that re-does "
        "the index; one call replaces the sweep.\n"
        "- After you EDIT, watch for the `⚠️` staleness banner; a pending "
        "file → `Read` it directly (watcher debounces ~2s).\n"
        "- No `.codegraph/` dir → inactive (indexing is the user's call); use "
        "grep/Read. `codegraph init` builds the index.\n\n"
        "## Pick the tool by intent\n"
        "| Need | MCP tool (if wired) | CLI (always works, same output) |\n"
        "|---|---|---|\n"
        "| Almost anything: \"how does X work\", a flow \"X→Y\", survey an area | "
        "`codegraph_explore` (PRIMARY — one call: relevant source grouped by file + "
        "relationship map + blast radius) | `codegraph explore \"<question \\| symbols>\"` |\n"
        "| One symbol's full source + caller/callee trail | `codegraph_node` | "
        "`codegraph node <symbol>` |\n"
        "| Read a whole file (line-numbered, like Read) + its dependents | "
        "`codegraph_node` (path) | `codegraph node <file> [--offset N --limit M]` |\n"
        "| Locate a symbol by name | `codegraph_search` | "
        "`codegraph query <name> [-k <kind> -l <n>]` |\n"
        "| Every call site (incl. callback registration) | `codegraph_callers` | "
        "`codegraph callers <symbol>` |\n"
        "| What a symbol calls | (inline in explore/node) | `codegraph callees <symbol>` |\n"
        "| Blast radius of a change | (inline in explore) | "
        "`codegraph impact <symbol> [-d <depth>]` |\n"
        "| Test files hit by changed files | — | "
        "`git diff --name-only \\| codegraph affected --stdin` |\n"
        "| Index health / pending syncs | `codegraph_status` | `codegraph status` |\n\n"
        "`codegraph_explore` is the default — most questions need ONLY it. The 4 "
        "default MCP tools are explore/node/search/callers; callees/impact/files/"
        "status are CLI-only by default (their info rides inline on the four) — "
        "re-enable via `CODEGRAPH_MCP_TOOLS=explore,node,search,callers,impact`. "
        "Reach for raw Read/Grep only to confirm a detail codegraph didn't cover.\n\n"
        "## Scope\n"
        "20+ languages (TS/JS · Python · Go · Rust · Java · C# · PHP · Ruby · C/C++ · "
        "ObjC · Swift · Kotlin · Scala · Dart · Lua · R · Svelte/Vue/Astro · Liquid · "
        "Pascal). Framework-aware routes (Django/Flask/FastAPI/Express/NestJS/Rails/"
        "Spring/Laravel/Gin/Axum/…) link URL patterns → handlers; cross-language "
        "iOS/RN/Expo bridges. Auto-skips node_modules/dist/.venv/etc · `.gitignore`d "
        "· >1MB files.\n\n"
        "## Setup (zero-config)\n"
        "`codegraph install` wires the MCP server into agents (Claude Code/Cursor/"
        "Codex/opencode/Gemini/Kiro/…); `codegraph init` builds a project's index "
        "(then auto-syncs — no manual `sync` needed). `codegraph upgrade` updates. "
        "100% local, no API keys, SQLite only.\n"
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


def _assumption_gate(ctx, raw_phase: dict, call_outputs: dict, accumulated: dict):
    """Spec 285 Part B — enforced no-assumption gate.

    A `requires_input` phase must not advance on an assumed value. When a
    required key is missing from both the call inputs and the accumulated
    outputs, source structured options from the phase's `resolve_via` verb (a
    FastMCP-annotated verb in the skill's OWN capability — a provenance-recording
    Invocation), then ELICIT the user in the flow. Mutates `call_outputs` with
    the answer and returns None to proceed; returns an input-required dict to
    ABORT the walk when no elicit-capable host is bound (pause, never assume)."""
    requires = raw_phase.get("requires_input") or []
    if not requires:
        return None

    def _missing():
        return [k for k in requires
                if call_outputs.get(k) in (None, "") and accumulated.get(k) in (None, "")]

    missing = _missing()
    if not missing:
        return None
    options = None
    rv = raw_phase.get("resolve_via")
    if rv:
        try:
            res = ctx.call(rv["capability"], rv["verb"], keys=",".join(missing))
            options = res.get("options") if isinstance(res, dict) else res
        except Exception:
            options = None
    host = ctx.host
    if host.can_elicit():
        from agency._host_bridge import HostUnavailable
        try:
            outcome = host.elicit(
                f"Phase {raw_phase['name']!r} needs {missing} — choose (no assumptions).",
                options=options if isinstance(options, list) else None)
        except HostUnavailable:
            outcome = None
        if outcome is not None and outcome.accepted:
            data = outcome.data
            if isinstance(data, dict):
                for k, v in data.items():
                    if v not in (None, ""):
                        call_outputs[k] = v
            elif len(missing) == 1 and data not in (None, ""):
                call_outputs[missing[0]] = data
            missing = _missing()
    if missing:
        return {"status": "input-required", "phase": raw_phase["name"],
                "blocked_on": f"assumption:{','.join(missing)}",
                "resume_with": missing, "options": options}
    return None


def _sample_phase(ctx, raw_phase: dict, call_outputs: dict):
    """Spec 285 Part B — a `sample` phase generates its `produces_key` via host
    sampling when a sampling-capable host is bound; otherwise returns an
    input-required dict so the host supplies it on resume (graceful fallback)."""
    sample = raw_phase.get("sample")
    if not sample:
        return None
    pk = sample.get("produces_key")
    if not pk or call_outputs.get(pk) not in (None, ""):
        return None
    host = ctx.host
    if host.can_sample():
        from agency._host_bridge import HostUnavailable
        try:
            comp = host.sample(sample.get("prompt") or sample.get("system") or "",
                               system=sample.get("system"))
            if getattr(comp, "text", ""):
                call_outputs[pk] = comp.text
        except HostUnavailable:
            pass
    if call_outputs.get(pk) in (None, ""):
        return {"status": "input-required", "phase": raw_phase["name"],
                "blocked_on": f"sample:{pk}", "resume_with": [pk]}
    return None


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
        raw_phase = run.phases[run.i]          # full dict (sample/requires_input/resolve_via)
        is_gate = phase.get("gate") == "hard"
        confirmed = is_gate and confirm_gate
        call_outputs = {k: v for k, v in inputs.items() if v not in (None, "")}
        # Spec 285 Part B — enforced assumption-gate (elicit-or-pause), then
        # host-sample to advance. Both abort the walk with input-required when
        # the host can't satisfy them; otherwise they mutate call_outputs.
        _ag = _assumption_gate(ctx, raw_phase, call_outputs, accumulated)
        if _ag is not None:
            return {**_ag, "skill_id": run.skill_id, "partial_outputs": accumulated}
        _sg = _sample_phase(ctx, raw_phase, call_outputs)
        if _sg is not None:
            return {**_sg, "skill_id": run.skill_id, "partial_outputs": accumulated}
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
            # Spec 282 Workstream H — propagate the resume hint (the exact
            # resume_from PHASE NAME + the missing outputs) so the caller
            # isn't left guessing how to continue a paused walk.
            return {"status": "input-required", "phase": res["phase"],
                    "blocked_on": res["blocked_on"],
                    "resume_from": res.get("resume_from", res["phase"]),
                    "resume_with": list(phase["produces"]),
                    "hint": res.get("hint",
                                    f"resume with resume_from={res['phase']!r}"),
                    "skill_id": run.skill_id,
                    "partial_outputs": accumulated}
        accumulated.update(res.get("outputs", {}))
        completed.append(res["phase"])
        if is_gate and confirmed:
            confirm_gate = False       # only the re-entered gate auto-confirms; later gates pause
    return {"status": "completed", "skill_id": run.skill_id, "outputs": accumulated}


# Spec 114 — session-driver protocol: the plugin IS the primary session driver.
# A SessionLifecycle node tracks the agent's current mode + the intent it serves;
# ModeShift records explicit transitions; DecisionRecord captures binding
# decisions; SessionReflection is the synthesize_session artefact at end-of-
# session. See Plan/114-plugin-as-session-driver/spec.md.
SESSION_MODE = {"brainstorming", "spec-authoring", "coding", "review",
                "synthesize"}
SESSION_STATUS = {"active", "paused", "archived"}

SESSION_DRIVER_SKILL = {
    "name": "session-driver-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "init",
         "produces": ["session_lifecycle_id", "intent_id", "mode"]},
        {"index": 2, "name": "mode-select",
         "produces": ["confirmed_mode"]},
        {"index": 3, "name": "work-loop",
         "produces": ["work_done"]},
        {"index": 4, "name": "synthesize",
         "produces": ["lessons_recorded"]},
        {"index": 5, "name": "archive",
         "produces": ["session_archived"], "gate": "hard"},
    ],
}

develop_ontology = OntologyExtension(
    skills={**DEV_SKILLS, "session-driver-pass": SESSION_DRIVER_SKILL},
    edges={"HAS_STEP"},                          # Spec 287 — Plan → PlanStep
    nodes={
        "SessionLifecycle": ["mode", "status"],
        "ModeShift": ["from_mode", "to_mode"],   # optional: reason
        # DecisionRecord lives on dogfood (Spec 114 §"Session-tracking cluster")
        # Spec 287 — plan provenance (rule 2: the plan is graph nodes, rendered
        # to markdown on demand, never a parsed file).
        "Plan": ["title"],                       # optional: status
        "PlanStep": ["plan", "index", "description"],   # optional: state, evidence
        # the autolearning maintenance loop — each run is a node, chained
        # PRECEDES the next (the loop's memory; see develop.maintain).
        "MaintenanceRun": ["focus"],             # optional: status, selected, next_candidate
    },
    enums={
        ("SessionLifecycle", "mode"): SESSION_MODE,
        ("SessionLifecycle", "status"): SESSION_STATUS,
        ("ModeShift", "from_mode"): SESSION_MODE,
        ("ModeShift", "to_mode"): SESSION_MODE,
        ("PlanStep", "state"): PLAN_STEP_STATES,        # Spec 287
    },
    # session-reflection schema lives on reflect (the producing cap)
)


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


def _grab_section(text: str, *headers: str) -> str:
    """Best-effort pull of a labelled section's body from a docstring/doc.
    Matches ``Header:`` (Spec 080 grammar) case-insensitively and returns the
    rest of that line + any indented/bulleted continuation lines."""
    import re
    lines = text.splitlines()
    pat = re.compile(r"^\s*(?:%s)\s*:\s*(.*)$"
                     % "|".join(re.escape(h) for h in headers), re.IGNORECASE)
    for i, ln in enumerate(lines):
        m = pat.match(ln)
        if not m:
            continue
        body = [m.group(1).strip()] if m.group(1).strip() else []
        for cont in lines[i + 1:]:
            if cont.strip().startswith(("-", "•", "*")) or (
                    cont.startswith((" ", "\t")) and cont.strip()):
                body.append(cont.strip())
            elif not cont.strip():
                continue
            else:
                break
        return " ".join(body).strip()
    return ""


def _functional_fields(text: str, kind: str) -> dict:
    """Extract the functional framework's slot values from an existing doc
    (Spec 306 — derive the candidate from the source's own content; rule 2)."""
    if kind == "skilldoc":
        # Reuse the canonical Spec 080 skill-grammar parser (disclosure.py) —
        # the single source SkillDocs already derive from — rather than
        # re-parsing Use-when/Triggers/Red-flags here.
        from agency.disclosure import parse_module_skill
        parsed = parse_module_skill(text, "", []) or {}
        return {
            "use_when": parsed.get("description", "").removeprefix("Use when ").strip(),
            "triggers": "; ".join(parsed.get("triggers", [])),
            "red_flags": "; ".join(parsed.get("red_flags", [])),
        }
    if kind == "tool-desc":
        # Spec 023 verb-docstring grammar: brief + Inputs + Returns + chain_next.
        return {
            "brief": (text.strip().splitlines() or [""])[0].strip(),
            "inputs": _grab_section(text, "Inputs", "Args", "Arguments"),
            "returns": _grab_section(text, "Returns", "Return"),
            "chain_next": _grab_section(text, "chain_next", "chain next", "Next"),
        }
    # template
    return {"slots": _grab_section(text, "Slots", "Fields")}


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
    # Spec 153 Slice 6 — the engine loads + enforces the MaintenanceRun schema.
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = develop_ontology

    # ---- Spec 287 — plan authoring + execution provenance -----------------

    @verb(role="act")
    def maintain(self, focus: str = "", record: bool = True) -> dict:
        """Drive — and AUTOLEARN — the recurring "Agency Steward" maintenance loop.

        The maintenance discipline lives HERE as a verb, not in a fragile external
        prompt: each call returns the hardened phase plan + an evidence-grounded
        candidate shortlist COMPUTED from the live graph, and records a
        ``MaintenanceRun`` linked ``PRECEDES`` from the prior run — so the task
        learns across scheduled runs (the run chain + the reflection backlog are
        its memory). Reference it from the steward prompt: call ``develop.maintain``
        at session start, follow the returned ``phases``, and the loop compounds.

        The candidate shortlist is derived, not snapshot (rule 8): the observation
        ``Reflection`` backlog (lessons to fold) + open Intents ranked by their
        live ``SERVES`` reach. The seven phases encode the steward discipline
        (orient → select → build → simplify → pillars → learn → ship).

        Inputs: focus (optional steer for this run), record (persist the run node).
        Returns: ``{run_id, phases, prior, signals, candidates, next_step}``.
        chain_next: walk the phases; end with ``reflect.note`` + a handover, then
                    ``branch.finish_branch`` to merge into main.
        """
        phases = [
            "0 orient — read AGENTS/CLAUDE/CORE/GOALS/TODO; `!codegraph init` then "
            "`!codegraph index`; agency_welcome + analyze.graph + manage.state; "
            "read the last MaintenanceRun + handover",
            "1 select — rank candidates by reach x coherence-debt x unblock x "
            "pillar-completeness-gap; record the ranking; pick exactly ONE",
            "2 build — harden the spec, then implement ONE shippable slice "
            "test-first (RED -> GREEN; behaviour, not internals)",
            "3 simplify — /simplify the touched code + its coupled blast radius",
            "4 pillars — prove Intent/Capability/Lifecycle/Memory each own write+read, "
            "no dormant surface, the Document convergence holds; drift clean; suite green",
            "5 learn — reflect.note the lessons; dogfood.parse_amendment; write + "
            "prompt.audit the handover",
            "6 ship — branch.finish_branch; drive CI green; merge the PR into main",
        ]
        # --- autolearn memory: the prior run chain ---
        prior_runs = self.ctx.find("MaintenanceRun")          # current versions only
        prior = None
        if prior_runs:
            last = max(prior_runs, key=lambda r: r.get("vfrom", 0))
            prior = {"id": last.get("id"), "focus": last.get("focus"),
                     "selected": last.get("selected") or "",
                     "next": last.get("next_candidate") or ""}
        # --- live-graph signals + a DERIVED candidate shortlist (rule 8) ---
        intents = self.ctx.find("Intent")
        reflections = [r for r in self.ctx.find("Reflection")
                       if r.get("scope") == "observation"]
        open_intents = [i for i in intents
                        if i.get("status") != "confirmed"] or intents

        def _reach(node: dict) -> int:
            nid = node.get("id", "")
            return len(self.ctx.nodes_serving(nid)) if nid else 0

        ranked = sorted(open_intents, key=_reach, reverse=True)
        signals = {
            "intents": len(intents),
            "open_intents": len(open_intents),
            "observation_backlog": len(reflections),
            "prior_runs": len(prior_runs),
        }
        candidates = (
            [{"kind": "reflection", "id": r.get("id"),
              "text": (r.get("text") or "")[:160]} for r in reflections[:5]]
            + [{"kind": "intent", "id": i.get("id"), "purpose": i.get("purpose"),
                "reach": _reach(i)} for i in ranked[:5]]
        )
        run_id = None
        if record:
            run_id = self.ctx.record_and_serve("MaintenanceRun", {
                "focus": focus or "auto", "status": "open",
                "selected": "", "next_candidate": ""})
            if prior and prior.get("id"):
                self.ctx.link(prior["id"], run_id, "PRECEDES")   # the autolearn chain
        next_step = ("read the last handover + run `!codegraph index`, then rank the "
                     "candidates and pick ONE high-impact spec (phase 1)")
        return {"run_id": run_id, "phases": phases, "prior": prior,
                "signals": signals, "candidates": candidates, "next_step": next_step}

    @verb(role="act")
    def draft_plan(self, title: str, steps: str = "") -> dict:
        """Author a bite-sized plan as graph provenance (Spec 287; rule 2).

        ``steps`` is a JSON array of step descriptions OR a newline-separated
        list. Mints a ``Plan{title}`` + one ``PlanStep{index, description,
        state:pending}`` per step, the Plan SERVING the intent and ``HAS_STEP``
        each PlanStep. The plan markdown is rendered on demand from these nodes —
        never a parsed file. The ``plan-execute`` discipline's draft-plan phase
        binds to this verb.

        Inputs: title, steps (JSON list or newlines).
        Returns: ``{plan_id, step_ids, count}``.
        chain_next: walk ``plan-execute``, or sign off then ``record_step_outcome``
                    per step + ``plan_status`` to roll up.
        """
        import json as _json
        parsed = None
        if steps:
            try:
                parsed = _json.loads(steps)
            except (ValueError, TypeError):
                parsed = list(steps.splitlines())
        if not isinstance(parsed, list):
            parsed = [parsed] if parsed not in (None, "") else []
        descriptions = [str(s).strip() for s in parsed if str(s).strip()]
        plan_id = self.ctx.record_and_serve("Plan", {"title": title, "status": "drafted"})
        step_ids = []
        for i, desc in enumerate(descriptions, start=1):
            sid = self.ctx.record("PlanStep", {
                "plan": plan_id, "index": i, "description": desc, "state": "pending"})
            self.ctx.link(plan_id, sid, "HAS_STEP")
            step_ids.append(sid)
        return {"plan_id": plan_id, "step_ids": step_ids, "count": len(step_ids)}

    @verb(role="act")
    def record_step_outcome(self, step_id: str, outcome: str,
                            evidence: str = "") -> dict:
        """Mark a PlanStep's execution outcome (Spec 287).

        ``outcome`` ∈ {done, blocked, skipped}. Bi-temporal update of the step's
        ``state`` + ``evidence`` (a new revision, not a destructive overwrite).

        Inputs: step_id (from ``draft_plan``), outcome, evidence.
        Returns: ``{step_id, state}`` — or ``{error}`` for a bad outcome / unknown step.
        chain_next: ``plan_status(plan_id)`` to roll up; ``delegate.dispatch_decision``
                    before the next step.
        """
        if outcome not in ("done", "blocked", "skipped"):
            return {"error": f"outcome must be done|blocked|skipped, got {outcome!r}"}
        node = self.ctx.recall(step_id)
        if node is None:
            return {"error": f"no node {step_id!r}"}
        self.ctx.update(step_id, {"state": outcome, "evidence": evidence[:200]})
        return {"step_id": step_id, "state": outcome}

    @verb(role="transform")
    def plan_status(self, plan_id: str) -> dict:
        """Roll up a Plan's steps + completion (Spec 287) — the render-on-demand
        read side (rule 2). Traverses the declared ``HAS_STEP`` edge (declare an
        edge ⇒ traverse it; no find()+filter on the foreign key).

        Inputs: plan_id.
        Returns: ``{title, status, steps:[{index, description, state}], complete}``
                 — ``complete`` is True iff every step is done|skipped. ``{error}``
                 for an unknown plan.
        chain_next: render the plan markdown from this, or continue the walk.
        """
        plan = self.ctx.recall(plan_id)
        if plan is None:
            return {"error": f"no Plan {plan_id!r}"}
        steps = self.ctx.neighbors(plan_id, "HAS_STEP", direction="out")
        steps_sorted = sorted(steps, key=lambda s: int(s.get("index", 0)))
        items = [{"index": int(s.get("index", 0)),
                  "description": s.get("description", ""),
                  "state": s.get("state", "pending")} for s in steps_sorted]
        complete = bool(items) and all(
            i["state"] in ("done", "skipped") for i in items)
        return {"title": plan.get("title", ""), "status": plan.get("status", ""),
                "steps": items, "complete": complete}

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

    @verb(role="act")
    def optimize_skilldoc(self, target_ref: str, kind: str = "skilldoc") -> dict:
        """Author an optimized functional doc — flags + candidate, NO rewrite (act).

        The metaprompt loop (Spec 306): agency uses its own framework substrate
        to enrich its own documentation. A capability docstring / SkillDoc /
        tool-description / template is a FUNCTIONAL prompt — its job is correct
        routing + invocation, not persuasion — so it is scored against the
        functional framework family (304), not CO-STAR. Resolves ``target_ref``
        → text, evaluates it (305 functional profile → goal-keyed flags incl.
        the load-bearing ``role_padding`` — a function needs no Role), renders
        the functional framework into an optimized CANDIDATE, and records a
        ``doc-optimization`` Artefact. **Advisory: returns the candidate, writes
        no source** (a human or a later ``branch.commit_smart`` applies it).

        The rules each flag enforces — what a good skilldoc paragraph looks like —
        live in ``agency/capabilities/prompt/references/skilldoc-authoring.md``;
        read them before applying a candidate.

        Inputs: target_ref (a capability name, a file path, or literal text),
                kind (``skilldoc`` | ``tool-desc`` | ``template``).
        Returns: ``{flags, candidate, rationale, artefact_id, scores, status,
                 source, kind}`` OR ``{error}``.
        chain_next: ``develop.validate_skill`` (the 080 gate) on the applied doc.
        """
        if kind not in ("skilldoc", "tool-desc", "template"):
            return {"error": f"kind must be skilldoc|tool-desc|template, got {kind!r}"}
        text, source = self._resolve_doc_text(target_ref)
        if not text.strip():
            return {"error": "EMPTY_TARGET", "source": source}
        evald = self.ctx.call("prompt", "evaluate", prompt_body=text, target=kind)
        evald = evald if isinstance(evald, dict) else {}
        flags = list(evald.get("flags", []))
        rendered = self.ctx.call("prompt", "render", framework_slug=kind,
                                 fields=_functional_fields(text, kind))
        candidate = rendered.get("result", "") if isinstance(rendered, dict) else ""
        artefact_id = self.ctx.record_and_serve("Artefact", {
            "kind": "doc-optimization", "path": source})
        rationale = (f"{kind}: " + (", ".join(flags) if flags else "no goal violations")
                     + " — candidate restructured to the functional grammar "
                     "(advisory; source unchanged)")
        return {"flags": flags, "candidate": candidate, "rationale": rationale[:300],
                "artefact_id": artefact_id, "scores": evald.get("scores", {}),
                "status": evald.get("status"), "source": source, "kind": kind}

    def _resolve_doc_text(self, target_ref: str) -> tuple[str, str]:
        """Resolve a ``target_ref`` to (text, source-label), tried IN ORDER:
        (1) a live capability name → its authored module docstring (the Spec 080
        grammar the SkillDoc derives from — folder-form ``<name>._main`` or
        single-file ``<name>``); (2) an existing file path → its contents;
        (3) otherwise the ref is literal text. A capability name therefore wins
        over a same-named file on disk. Read-only — never writes."""
        import importlib
        import inspect
        from pathlib import Path
        if target_ref in self.ctx.registry.names():
            for modpath in (f"agency.capabilities.{target_ref}._main",
                            f"agency.capabilities.{target_ref}"):
                try:
                    mod = importlib.import_module(modpath)
                except ImportError:
                    continue
                doc = inspect.getdoc(mod)
                if doc:
                    return doc, f"capability:{target_ref}"
            return "", f"capability:{target_ref}"
        try:
            p = Path(target_ref)
            if p.is_file():
                return p.read_text(), f"file:{target_ref}"
        except (OSError, ValueError):
            pass
        return target_ref, "literal"

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

    @verb(role="transform")
    def estimate(self, loc: int = 0, files: int = 0, tests: int = 0) -> dict:
        """Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate,
        DECIDABLE only: no LLM, a transparent formula over the inputs you can count).

        Inputs: loc (lines of change), files (files touched), tests (tests to write).
        Returns: ``{points, bucket, confidence, drivers}`` — bucket ∈ S/M/L/XL; confidence
                 falls as size grows (more unknowns).
        chain_next: walk ``plan`` (large) or ``tdd`` (small) accordingly.
        """
        loc, files, tests = max(0, int(loc)), max(0, int(files)), max(0, int(tests))
        # transparent, documented weights (a tunable config, not a magic snapshot — rule 8)
        points = round(loc / 50 + files * 1.5 + tests * 1.0, 1)
        bucket = ("S" if points < 5 else "M" if points < 15 else "L" if points < 40 else "XL")
        confidence = round(max(0.3, 1.0 - points / 60), 2)   # shrinks with size
        return {"result": {"points": points, "bucket": bucket, "confidence": confidence,
                           "drivers": {"loc": loc, "files": files, "tests": tests}}}

    @verb(role="effect")
    def index(self, path: str = ".", apply: bool = False,
              max_tokens: int = 3000) -> dict:
        """Index a repo as a token-cheap briefing — the development-workflow
        entry to the indexer (Spec 292).

        Understanding a repo before working on it is a `develop` concern, so the
        94%-reduction briefing is surfaced here. Delegates to
        ``document.index_repo`` (the rendering machinery + ``RepoIndex`` graph
        node stay in ``document``; this is the verb-level port, not a fork), so
        a single call records the index node AND, with ``apply``, writes
        ``PROJECT_INDEX.md``. Used by the SessionStart hook to keep the index
        fresh each session.

        Inputs: path (str), apply (bool — write PROJECT_INDEX.md),
                max_tokens (int — budget; default 3000).
        Returns: ``{index_id, content, tokens, files_scanned, writeup}``.
        chain_next: read the briefing instead of re-scanning the tree.
        """
        return self.ctx.call("document", "index_repo", path=path,
                             apply=apply, max_tokens=max_tokens)

    @verb(role="act")
    def scaffold_capability(self, name: str, kind: str = "light",
                            base_dir: str = "") -> dict:
        """Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton.

        Inputs: name (kebab-case), kind (light|medium|heavy), base_dir (optional).
        Returns: {result: <path>, artefact: {kind, name, path, scaffold_version}}.
        chain_next: plugin.lint_capability(name) to verify lint-clean, then
                    develop.reload to make the new capability live this session.
        """
        return scaffold_capability(name, kind=kind,
                                   base_dir=base_dir or None)

    @verb(role="effect")
    def reload(self) -> dict:
        """Reload edited capability code into the live session (effect).

        Purges + re-imports the ``agency.capabilities.*`` subtree so a verb you
        just edited or scaffolded is live WITHOUT a session restart — the
        authoring loop's last step (delegates to ``Engine.reload``, Spec 302).
        Picks up edits inside a folder-cap's ``_main`` / ``clusters`` submodules,
        not just brand-new caps. Code-mode ``execute`` reaches new verbs
        immediately; a non-code-mode client must re-list tools to see them.

        Inputs: (none).
        Returns: ``{reloaded, capability_count, added, removed, rewired_tools,
                 reimported}``.
        chain_next: develop.validate_skill(name) on the reloaded capability.
        """
        return self.ctx.engine.reload()

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
        Returns: a status-contract shape — one of:
          - ``{status: "completed", skill_id, outputs}``
          - ``{status: "input-required", phase, blocked_on, resume_with, skill_id, partial_outputs}``
          - ``{status: "failed", phase, error, skill_id, completed_phases}``
        chain_next: on input-required, re-call with resume_from + resume_with keys.
        """
        return _skill_walk(self.ctx, name, inputs, resume_from=resume_from)

    # ════════════════════════════════════════════════════════════════════════
    # Spec 114 — plugin-as-session-driver: 3 verbs for the session lifecycle
    # (init / check / mode-select). reflect.synthesize_session +
    # dogfood.record_decision + dogfood.boundary_use_audit live on their own
    # caps. See Plan/114-plugin-as-session-driver/spec.md.
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="act")
    def session_init(self, purpose: str = "", deliverable: str = "",
                      acceptance: str = "",
                      mode_hint: str = "") -> dict:
        """Mint a SessionLifecycle SERVING the intent, detect mode, and suggest the first verb.

        The plugin's primary session-driver entry point (Spec 114 Pillar 1).
        Records a SessionLifecycle node tied to the serving intent + an initial
        mode (auto-detected from cwd state, or honoring ``mode_hint``).

        Mode-detection heuristics (cheap, deterministic):
          - cwd contains ``Plan/*/spec.md`` modified → ``spec-authoring``
          - cwd contains ``agency/capabilities/*/*.py`` modified → ``coding``
          - default → ``brainstorming``

        Inputs: purpose, deliverable, acceptance (optional intent triple — if
                empty, uses the serving intent's existing fields), mode_hint
                (override the auto-detect).
        Returns: ``{session_lifecycle_id, intent_id, mode, suggested_first_verb}``.
        chain_next: ``develop.session_check`` to read state OR
                    ``develop.mode_select`` to switch.
        """
        mode = mode_hint if mode_hint in SESSION_MODE else self._detect_mode()
        sid = self.ctx.record_and_serve("SessionLifecycle", {
            "mode": mode, "status": "active",
            "purpose": purpose or "session", "deliverable": deliverable,
            "acceptance": acceptance,
        })
        suggested = {
            "brainstorming": "develop.brainstorm",
            "spec-authoring": "develop.checklist",   # → write_spec
            "coding": "develop.test",
            "review": "develop.skill_walk",
            "synthesize": "reflect.synthesize_session",
        }.get(mode, "develop.brainstorm")
        return {
            "session_lifecycle_id": sid,
            "intent_id": self.ctx.intent_id,
            "mode": mode,
            "suggested_first_verb": suggested,
        }

    @verb(role="transform")
    def session_check(self, session_lifecycle_id: str = "") -> dict:
        """Read the current SessionLifecycle state (transform).

        Inputs: session_lifecycle_id (defaults to the most recent
                SessionLifecycle SERVING the current intent).
        Returns: ``{session_lifecycle_id, mode, status, mode_history}``.
        chain_next: ``develop.mode_select`` to switch modes.
        """
        if session_lifecycle_id:
            node = self.ctx.recall(session_lifecycle_id)
        else:
            sessions = [s for s in self.ctx.find("SessionLifecycle")]
            node = sorted(sessions, key=lambda n: n.get("vfrom", 0),
                          reverse=True)[0] if sessions else None
        if not node:
            return {"session_lifecycle_id": "", "mode": "",
                    "status": "not_found", "mode_history": []}
        # Mode history = ModeShift nodes for this session
        shifts = [s for s in self.ctx.find("ModeShift")]
        history = sorted(
            [{"from": s["from_mode"], "to": s["to_mode"],
              "reason": s.get("reason", "")} for s in shifts],
            key=lambda h: h.get("vfrom", 0))
        return {
            "session_lifecycle_id": node.get("id", session_lifecycle_id),
            "mode": node.get("mode", ""),
            "status": node.get("status", ""),
            "purpose": node.get("purpose", ""),
            "mode_history": history,
        }

    @verb(role="transform")
    def session_resume(self, for_intent_id: str = "") -> dict:
        """Spec 114 Slice 2 — cross-session handoff.

        Find the most-recent ACTIVE SessionLifecycle SERVING the given
        intent (or the most-recent intent when `for_intent_id` is empty)
        so a fresh session can pick up where the prior one left off — no
        context re-derivation. Archived lifecycles are skipped; if no
        active lifecycle exists, returns `found=False`.

        Inputs: for_intent_id (optional; empty → most-recent Intent —
                renamed from `intent_id` to avoid the Registry.invoke
                built-in-parameter collision).
        Returns: ``{found, session_lifecycle_id, intent_id, mode, status,
                   purpose, mode_history, suggested_action, last_active}``.
        chain_next: when `found=True`, walk the suggested_action verb;
                    when `found=False`, `develop.session_init` for a
                    fresh start.
        """
        # Resolve target intent (most-recent active when not specified).
        target_iid = for_intent_id
        if not target_iid:
            intents = list(self.ctx.memory.find("Intent"))
            if intents:
                last = max(intents, key=lambda r: r.get("vfrom", 0))
                target_iid = last.get("id", "") or ""
        if not target_iid:
            return {
                "found": False, "session_lifecycle_id": "",
                "intent_id": "", "mode": "", "status": "",
                "purpose": "", "mode_history": [],
                "suggested_action": "develop.session_init",
                "last_active": 0,
            }
        # Find SessionLifecycles SERVING this intent via the graph edge.
        candidates = self.ctx.nodes_serving(
            target_iid, label="SessionLifecycle", where={"status": "active"})
        if not candidates:
            return {
                "found": False, "session_lifecycle_id": "",
                "intent_id": target_iid, "mode": "", "status": "",
                "purpose": "", "mode_history": [],
                "suggested_action": "develop.session_init",
                "last_active": 0,
            }
        # Pick the most-recent by vfrom (bi-temporal valid-from).
        winner = max(candidates, key=lambda n: n.get("vfrom", 0))
        sid = winner.get("id", "") or ""
        # Mode history: ModeShift nodes SERVES'd by this session.
        shifts = list(self.ctx.memory.find("ModeShift"))
        history = sorted(
            [{"from": s.get("from_mode", ""), "to": s.get("to_mode", ""),
              "reason": s.get("reason", "")} for s in shifts],
            key=lambda h: h.get("vfrom", 0))
        mode = winner.get("mode", "")
        # Mode-aware suggestion — point the agent at the right next verb
        # without re-deriving where it left off.
        suggestion_for = {
            "brainstorming": "develop.brainstorm (resume the brainstorm)",
            "spec-authoring": "develop.write_spec (continue spec authoring)",
            "coding": "develop.implement (continue coding)",
            "review": "develop.skill_walk (continue review pass)",
            "synthesize": "reflect.synthesize_session (close the session)",
        }
        suggested_action = suggestion_for.get(
            mode, "develop.session_check (inspect state)")
        return {
            "found": True,
            "session_lifecycle_id": sid,
            "intent_id": target_iid,
            "mode": mode,
            "status": winner.get("status", ""),
            "purpose": winner.get("purpose", ""),
            "mode_history": history,
            "suggested_action": suggested_action,
            "last_active": winner.get("vfrom", 0),
        }

    @verb(role="effect")
    def mode_select(self, session_lifecycle_id: str,
                     new_mode: str, reason: str = "") -> dict:
        """Switch session mode + record a ModeShift node (effect).

        Inputs: session_lifecycle_id, new_mode (one of ``SESSION_MODE``), reason.
        Returns: ``{from_mode, to_mode, mode_shift_id}``.
        chain_next: the walkable skill for the new mode.
        """
        if new_mode not in SESSION_MODE:
            raise ValueError(
                f"mode={new_mode!r} not in {sorted(SESSION_MODE)}")
        node = self.ctx.recall(session_lifecycle_id)
        if not node:
            raise KeyError(
                f"SessionLifecycle {session_lifecycle_id!r} not found")
        from_mode = node.get("mode", "brainstorming")
        shift_id = self.ctx.record("ModeShift", {
            "from_mode": from_mode, "to_mode": new_mode,
            "reason": reason,
        })
        self.ctx.link(shift_id, session_lifecycle_id, "SERVES")
        self.ctx.update(session_lifecycle_id, {"mode": new_mode})
        return {
            "from_mode": from_mode, "to_mode": new_mode,
            "mode_shift_id": shift_id,
        }

    def _detect_mode(self) -> str:
        """Cheap deterministic mode-detection from cwd state.

        Inspects the current working directory for modified spec / code files
        via `git status --short`. Returns a SESSION_MODE value.
        """
        import subprocess
        try:
            res = subprocess.run(
                ["git", "status", "--short"], capture_output=True,
                text=True, timeout=2, check=False)
            output = res.stdout or ""
        except (FileNotFoundError, subprocess.SubprocessError):
            return "brainstorming"
        has_spec = any("Plan/" in ln and ".md" in ln
                       for ln in output.splitlines())
        has_code = any("agency/capabilities/" in ln and ln.endswith(".py")
                       for ln in output.splitlines())
        if has_spec and not has_code:
            return "spec-authoring"
        if has_code:
            return "coding"
        return "brainstorming"

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
        rid = self.ctx.record_and_serve("Reflection", {
            "scope": "observation",
            "text": text,
        })
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"result": rid}
