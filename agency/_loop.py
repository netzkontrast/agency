"""agency/_loop.py — the lifecycle-spine loop module (Specs 362–369).

The looper port lives here: looper (https://github.com/ksimback/looper, by
Kevin Simback / @ksimback, MIT) reimplemented as the lifecycle SPINE, not a
capability. The ``loop`` state machine is data in
``_lifecycle_data/machines.json`` (Spec 345), walked via the pillar
``ctx.lifecycle.open(machine="loop")`` / ``.move()``. This module holds the
loop-specific logic that is NOT pure reuse:

- ``control_evaluate`` — the termination guards (Spec 366; ports run-loop.py's
  ``enforce_wall_clock`` / ``no_progress_reached`` / ``max_revisions`` /
  ``max_iterations``).
- *(later slices)* ``open`` / ``advance``, ``compile`` / ``emit``,
  ``detect_models`` / ``recommend_council``.

Reuse lives elsewhere: goal = Intent (363), verify = ``gate`` (364), council =
``persona``/``panel`` (365), emit = ``document.render`` (368), read/provenance =
``manage``.

MIT attribution — the loop-design discipline, the four coaching rubrics, the
``loop.yaml`` / ``run-loop.py`` shapes, and the termination model are ported from
looper (Kevin Simback, MIT).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

# Defaults mirror looper's loop_control (templates/loop.yaml) — tunable budgets
# with a rationale, not frozen snapshots (CLAUDE.md rule 8): the caps a loop is
# opened with override these.
DEFAULT_MAX_ITERATIONS = 12
DEFAULT_MAX_REVISIONS = 3
DEFAULT_NO_PROGRESS_STALL = 2

# stop_reason priority — a hard cap wins over a soft one.
STOP_REASONS = ("budget", "no_progress", "max_revisions", "max_iterations")


def control_evaluate(control: dict[str, Any], progress: dict[str, Any]) -> dict[str, Any]:
    """Decide whether the loop may advance, or must stop (and why).

    Pure port of looper's run-loop.py termination guards. ``control`` carries the
    caps a loop was opened with (``max_iterations`` / ``max_revisions`` /
    ``no_progress_stall`` / ``budget.wall_clock_min``); ``progress`` carries the
    live counters (``iterations`` / ``revisions`` / ``stalled`` / ``elapsed_min``).

    Returns ``{permit: bool, stop_reason: str}`` where ``stop_reason`` ∈
    ``"" | budget | no_progress | max_revisions | max_iterations``. Priority:
    budget → no_progress → max_revisions → max_iterations. A loop ALWAYS has a
    stop — looper's honest durability, enforced.
    """
    budget = control.get("budget") or {}
    wall = budget.get("wall_clock_min")
    if wall is not None and progress.get("elapsed_min", 0) > wall:
        return {"permit": False, "stop_reason": "budget"}

    stall_cap = control.get("no_progress_stall", DEFAULT_NO_PROGRESS_STALL)
    if progress.get("stalled", 0) >= stall_cap:
        return {"permit": False, "stop_reason": "no_progress"}

    if progress.get("revisions", 0) >= control.get("max_revisions", DEFAULT_MAX_REVISIONS):
        return {"permit": False, "stop_reason": "max_revisions"}

    if progress.get("iterations", 0) >= control.get("max_iterations", DEFAULT_MAX_ITERATIONS):
        return {"permit": False, "stop_reason": "max_iterations"}

    return {"permit": True, "stop_reason": ""}


def _has_termination_guard(max_iterations: int, budget: Any, no_progress_stall: int) -> bool:
    """A loop must declare at least one termination guard (looper: never emit a
    guard-free loop)."""
    return (max_iterations or 0) > 0 or bool(budget) or (no_progress_stall or 0) > 0


def open_loop(host: Any, intent_id: str, *, max_iterations: int = DEFAULT_MAX_ITERATIONS,
              max_revisions: int = DEFAULT_MAX_REVISIONS, budget: dict[str, Any] | None = None,
              no_progress_stall: int = DEFAULT_NO_PROGRESS_STALL) -> dict[str, Any]:
    """Open a loop — a Lifecycle on the "loop" machine SERVING ``intent_id`` — with
    the termination control recorded on the node. Refuses a guard-free loop.

    ``host`` supplies the lifecycle pillar + memory (an ``Engine`` or a
    ``CapabilityContext`` — both expose ``.lifecycle`` and ``.memory``). This is the
    spec's ``_loop.open`` (Spec 366); named ``open_loop`` to avoid shadowing the
    builtin ``open`` in this module (which later does file I/O for emit). Returns
    ``{loop_id, state, control}``.
    """
    if not _has_termination_guard(max_iterations, budget, no_progress_stall):
        raise ValueError(
            "a loop must declare a termination guard (max_iterations, budget, or "
            "no_progress) — looper: never emit a guard-free loop")
    loop_id = host.lifecycle.open(intent_id, machine="loop")
    control: dict[str, Any] = {
        "max_iterations": max_iterations,
        "max_revisions": max_revisions,
        "no_progress_stall": no_progress_stall,
    }
    if budget:
        control["budget"] = budget
    # Record control on the Lifecycle node as JSON (deterministic round-trip; the
    # lifecycle-state-writer drift guard only forbids writing `state` outside
    # agency/lifecycle.py — `loop_control` is additive). A later slice may promote
    # this to a typed LoopControl node.
    host.memory.update(loop_id, {"loop_control": json.dumps(control)})
    state = (host.memory.recall(loop_id) or {}).get("state")
    return {"loop_id": loop_id, "state": state, "control": control}


# --- Spec 363: goal coaching (the goal IS a root Intent) ---------------------

_RUBRIC_DIR = Path(__file__).parent / "_lifecycle_data" / "loop" / "rubrics"
GOAL_RUBRIC = "goal-rubric.md"

# Heuristics derived from goal-rubric.md (the vendored looper rubric is the
# authority; these are the decidable signals it describes — not a second source).
_ACTIVITY_LEADERS = (
    "work on", "improve", "improving", "do ", "deal with", "handle",
    "look at", "focus on", "help with", "try to", "make our", "make the",
)
_VAGUE_DONE_TERMS = ("good", "better", "nice", "great", "quality", "robust", "clean", "solid")
_CHECKABLE_MARKERS = (
    "every", "all ", "each", "no ", "none", "must", "contains", "passes", "exit", "<", ">", "=", "%",
)


def rubric_path(name: str) -> Path:
    """Resolve a vendored loop rubric (looper references → agency loop data)."""
    return _RUBRIC_DIR / name


def _validate_context_sources(sources: Any) -> list[dict[str, Any]]:
    """Normalize + argv-validate goal context sources. Each is ``{file: str}`` or
    ``{cmd: [argv]}`` — a ``cmd`` MUST be an argv array, never a shell string
    (looper File Rule + shell safety, Spec 192). A ``cmd`` is resolved by the
    machine/runner, not at framing time."""
    normalized: list[dict[str, Any]] = []
    for src in sources or []:
        if not isinstance(src, dict):
            raise ValueError("each context source must be a {file} or {cmd:[argv]} mapping")
        if "cmd" in src:
            cmd = src["cmd"]
            if not (isinstance(cmd, list) and cmd and all(isinstance(t, str) for t in cmd)):
                raise ValueError(
                    "context source cmd must be an argv array, not a shell string "
                    "(looper: argv arrays only — no shell interpolation)")
            normalized.append({"cmd": list(cmd)})
        elif "file" in src:
            if not isinstance(src["file"], str) or not src["file"].strip():
                raise ValueError("context source file must be a non-empty string")
            normalized.append({"file": src["file"]})
        else:
            raise ValueError("each context source needs a 'file' or 'cmd' key")
    return normalized


def frame_goal(host: Any, statement: str, definition_of_done: str, *,
               deliverable: str = "", context_sources: Any = None) -> dict[str, Any]:
    """Frame a loop goal as a root Intent (Spec 363). ``statement`` → Intent
    purpose, ``definition_of_done`` → acceptance; ``context_sources`` bind argv-safe
    onto the Intent (resolved at compile/run time, never shell-interpolated).
    ``host`` exposes ``.intent`` + ``.memory``. Returns ``{goal_id, context_sources}``.
    """
    sources = _validate_context_sources(context_sources)
    goal_id = host.intent.capture(
        purpose=statement,
        deliverable=deliverable or statement,
        acceptance=definition_of_done,
    )
    if sources:
        host.memory.update(goal_id, {"context_sources": json.dumps(sources)})
    return {"goal_id": goal_id, "context_sources": sources}


def critique_goal(host: Any, intent_id: str) -> dict[str, Any]:
    """Critique a framed goal against goal-rubric.md (Spec 363) — ADVISORY, never
    blocks (looper parity). Surfaces rubric findings (outcome-vs-activity,
    falsifiable done-state, gather-vs-assume) and reuses the clarity score
    (Spec 322) as a reported signal. The wizard (367) decides any hard gate.
    Returns ``{findings, clarity, ok, rubric_source}``.
    """
    intent = host.memory.recall(intent_id) or {}
    statement = str(intent.get("purpose", ""))
    done = str(intent.get("acceptance", ""))
    raw_sources = intent.get("context_sources")
    sources = json.loads(raw_sources) if raw_sources else []

    findings: list[dict[str, str]] = []
    if any(statement.strip().lower().startswith(lead) for lead in _ACTIVITY_LEADERS):
        findings.append({
            "dimension": "outcome_vs_activity",
            "message": "goal is activity-framed; name the concrete outcome/artifact, not only the activity",
            "rubric": GOAL_RUBRIC,
        })
    done_low = done.lower()
    has_vague = any(term in done_low for term in _VAGUE_DONE_TERMS)
    has_checkable = any(m in done_low for m in _CHECKABLE_MARKERS) or any(c.isdigit() for c in done_low)
    if not done.strip() or (has_vague and not has_checkable):
        findings.append({
            "dimension": "falsifiable_done",
            "message": "done-state is not falsifiable; define the artifact/state that proves the loop finished",
            "rubric": GOAL_RUBRIC,
        })
    if not sources:
        findings.append({
            "dimension": "gather_vs_assume",
            "message": "no context sources named; gather context the host must read instead of assuming it",
            "rubric": GOAL_RUBRIC,
        })

    from ._clarity import clarity_score
    clarity = clarity_score(host.memory, intent_id)
    return {
        "findings": findings,
        "clarity": clarity,
        "ok": not findings,
        "rubric_source": str(rubric_path(GOAL_RUBRIC)),
    }


# --- Spec 364: verification as typed gates -----------------------------------
# Criteria are stored on the loop as a JSON list (interim); they promote to typed
# VerificationCriterion nodes when the loop capability's ontology extension lands.
# Every kind produces ONE typed verdict shape the machine (366) consumes.

VERIFICATION_RUBRIC = "verification-rubric.md"
_CRITERION_KINDS = ("programmatic", "judge", "human")
_EXPECT_MODES = ("exit_zero", "exit_nonzero", "stdout_contains")
_PROGRAMMATIC_TIMEOUT_SEC = 300  # tunable budget (CLAUDE.md rule 8), not a snapshot


def _loop_criteria(host: Any, loop_id: str) -> list[dict[str, Any]]:
    raw = (host.memory.recall(loop_id) or {}).get("criteria")
    return json.loads(raw) if raw else []


def add_criterion(host: Any, loop_id: str, kind: str, *, check: Any = None,
                  expect: str = "exit_zero", contains: str = "", rubric: str = "",
                  prompt: str = "", cid: str = "") -> dict[str, Any]:
    """Add a typed verification criterion to a loop (Spec 364). programmatic
    ``check`` is argv-validated (shell safety, Spec 192 — never a shell string)."""
    if kind not in _CRITERION_KINDS:
        raise ValueError(f"criterion kind must be one of {_CRITERION_KINDS}, got {kind!r}")
    existing = _loop_criteria(host, loop_id)
    crit: dict[str, Any] = {"id": cid or f"c{len(existing) + 1}", "kind": kind}
    if kind == "programmatic":
        if not (isinstance(check, list) and check and all(isinstance(t, str) for t in check)):
            raise ValueError(
                "programmatic criterion check must be an argv array, not a shell string "
                "(looper: argv arrays only — no shell interpolation, Spec 192)")
        if expect not in _EXPECT_MODES:
            raise ValueError(f"expect must be one of {_EXPECT_MODES}, got {expect!r}")
        crit.update({"check": list(check), "expect": expect, "contains": contains})
    elif kind == "judge":
        if not rubric.strip():
            raise ValueError("judge criterion needs a rubric")
        crit["rubric"] = rubric
    else:  # human
        if not prompt.strip():
            raise ValueError("human criterion needs a prompt")
        crit["prompt"] = prompt
    existing.append(crit)
    host.memory.update(loop_id, {"criteria": json.dumps(existing)})
    return {"criterion_id": crit["id"], "kind": kind}


def _parse_judge_verdict(text: str) -> dict[str, Any]:
    """Parse a council member's verdict (looper ``parse_judge_output`` parity):
    fenced or bare JSON with verdict in pass|revise; unparseable degrades to
    revise + a warning, never a crash."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text or "", re.DOTALL)
    candidate = fenced.group(1) if fenced else (text or "").strip()
    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("judge output was not a JSON object")
    except (json.JSONDecodeError, ValueError):
        return {"verdict": "revise", "kind": "judge",
                "warning": "unparseable_judge_output", "notes": (text or "").strip()}
    if parsed.get("verdict") not in ("pass", "revise"):
        parsed["verdict"] = "revise"
        parsed.setdefault("warning", "unparseable_judge_output")
    parsed["kind"] = "judge"
    return parsed


def check_criterion(criterion: dict[str, Any], *, cwd: str | None = None,
                    judge_output: str | None = None) -> dict[str, Any]:
    """Evaluate ONE criterion to the typed verdict the machine (366) consumes:
    ``{verdict in pass|revise|input-required, kind, ...}`` (Spec 364).

    - programmatic: run the argv safely (argv-only, timeout — shell safety,
      Spec 192) and match ``expect``.
    - judge: parse the council member's ``judge_output`` (degrade on unparseable);
      the council DISPATCH is Spec 365 — here we own the verdict shape.
    - human: a typed ``input-required`` pause naming the prompt (elicit, Spec 285).
    """
    kind = criterion.get("kind")
    if kind == "programmatic":
        argv = criterion.get("check") or []
        if not (isinstance(argv, list) and argv):
            raise ValueError("programmatic criterion has no argv check")
        try:
            proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                                  timeout=_PROGRAMMATIC_TIMEOUT_SEC)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"verdict": "revise", "kind": "programmatic", "evidence": f"check failed to run: {exc}"}
        expect = criterion.get("expect", "exit_zero")
        if expect == "exit_zero":
            ok = proc.returncode == 0
        elif expect == "exit_nonzero":
            ok = proc.returncode != 0
        else:  # stdout_contains
            ok = criterion.get("contains", "") in proc.stdout
        # Full stdout is the evidence — never truncated (CLAUDE.md rule 9).
        return {"verdict": "pass" if ok else "revise", "kind": "programmatic",
                "returncode": proc.returncode, "evidence": proc.stdout.strip()}
    if kind == "judge":
        return _parse_judge_verdict(judge_output or "")
    if kind == "human":
        return {"verdict": "input-required", "kind": "human", "prompt": criterion.get("prompt", "")}
    raise ValueError(f"unknown criterion kind: {kind!r}")


def verify_report(host: Any, loop_id: str) -> dict[str, Any]:
    """Audit a loop's verification SET against verification-rubric.md (Spec 364).
    Flags the rubric's anti-patterns (all-vibe: no deterministic floor).
    ``programmatic_ratio`` is computed live (rule 8). Returns ``{criteria,
    programmatic_ratio, warnings, rubric_source}``."""
    criteria = _loop_criteria(host, loop_id)
    total = len(criteria)
    n_programmatic = sum(1 for c in criteria if c.get("kind") == "programmatic")
    ratio = (n_programmatic / total) if total else 0.0
    warnings: list[dict[str, str]] = []
    if total and n_programmatic == 0:
        warnings.append({
            "rubric_ref": VERIFICATION_RUBRIC,
            "message": "all criteria are judge/human — add a deterministic (programmatic) "
                       "floor where a check, schema, or test exists",
        })
    return {"criteria": criteria, "programmatic_ratio": ratio, "warnings": warnings,
            "rubric_source": str(rubric_path(VERIFICATION_RUBRIC))}


# --- Spec 365: the cross-model council (reuse persona + panel) ----------------
# A council member is a reviewer (notes) or a judge (a gating verdict), scoped to
# plan/delivery/both and bound to a model family/driver. Reuse target: a member
# promotes to a `persona` (297) bound to a `driver` (002); convene reuses `panel`
# (294); cross-vendor dispatch routes through `delegate`/`jules` (040/271) + the
# egress gate (369). Stored here as JSON on the loop node — the spine interim,
# parity with 364's criteria. The verdict SHAPE is owned by `_parse_judge_verdict`
# (above): judge JSON degrades to revise + warn, never a crash.

COUNCIL_RUBRIC = "council-rubric.md"
_MEMBER_ROLES = ("reviewer", "judge")
_MEMBER_SCOPES = ("plan", "delivery", "both")
# The loop's two gating states (366) and the council scope each one needs covered.
_LOOP_GATES = {"plan_gate": "plan", "delivery_gate": "delivery"}


def _loop_members(host: Any, loop_id: str) -> list[dict[str, Any]]:
    raw = (host.memory.recall(loop_id) or {}).get("council")
    return json.loads(raw) if raw else []


def add_member(host: Any, loop_id: str, role: str, *, scope: str = "both",
               family: str = "", local: bool = False, driver: str = "",
               mid: str = "") -> dict[str, Any]:
    """Add a council member to a loop (Spec 365). ``role`` ∈ reviewer|judge;
    ``scope`` ∈ plan|delivery|both; ``family``/``driver`` name the model it speaks
    for; ``local`` flags a privacy-preserving on-device model. A reviewer emits
    notes; a judge emits the gating verdict. Returns ``{member_id, role, family}``.
    """
    if role not in _MEMBER_ROLES:
        raise ValueError(f"member role must be one of {_MEMBER_ROLES}, got {role!r}")
    if scope not in _MEMBER_SCOPES:
        raise ValueError(f"member scope must be one of {_MEMBER_SCOPES}, got {scope!r}")
    members = _loop_members(host, loop_id)
    member = {"id": mid or f"m{len(members) + 1}", "role": role, "scope": scope,
              "family": family, "local": bool(local), "driver": driver or family}
    members.append(member)
    host.memory.update(loop_id, {"council": json.dumps(members)})
    return {"member_id": member["id"], "role": role, "family": family}


def recommend_council(host: Any, loop_id: str, *, host_family: str = "") -> dict[str, Any]:
    """Report the council's verdict-source coverage + a cross-family recommendation
    (Spec 365). **The reviewer-only rule:** a ``revise_until_clean`` gate REQUIRES a
    verdict source — a judge member covering its scope, or a human criterion —
    because nothing else can declare a delivery "clean." Cross-model review (a
    member from a DIFFERENT family than the host) is the coaching default, not a
    hard rule. Returns ``{members, verdict_sources_ok, missing, recommended,
    host_family, rubric_source}``.
    """
    members = _loop_members(host, loop_id)
    has_human = any(c.get("kind") == "human" for c in _loop_criteria(host, loop_id))
    judges = [m for m in members if m.get("role") == "judge"]

    def _covered(gate_scope: str) -> bool:
        if has_human:
            return True
        return any(m.get("scope") in ("both", gate_scope) for m in judges)

    missing = [gate for gate, gscope in _LOOP_GATES.items() if not _covered(gscope)]
    member_view = [
        {**m, "cross_family": bool(host_family) and m.get("family") != host_family}
        for m in members
    ]
    recommended = [
        {"role": "judge", "scope": _LOOP_GATES[gate],
         "family": f"a family other than {host_family or 'the host'}"}
        for gate in missing
    ]
    return {"members": member_view, "verdict_sources_ok": not missing,
            "missing": missing, "recommended": recommended,
            "host_family": host_family, "rubric_source": str(rubric_path(COUNCIL_RUBRIC))}


# --- Spec 366: the walk reducer (advance) ------------------------------------
# `advance` is the SOLE in-session walk step. It reads the current machine state,
# runs the gate (criteria 364 + council verdict 365), asks control_evaluate
# whether a move is still permitted, then ctx.lifecycle.move(...) — the pillar is
# the only state writer (Spec 339). Status/stop_reason DERIVE from the graph
# (loop node progress + the 344 transition trail via manage.lifecycle*, 341) —
# no state.json/run-log.md is written in-session (looper's files are an EXPORT
# concern, Spec 368). control-rubric.md is vendored under the loop rubrics.

CONTROL_RUBRIC = "control-rubric.md"

# plan_gate → {pass: delivering, revise: planning, counter: revisions};
# delivery_gate → {pass: completed, revise: delivering, counter: iterations}.
_GATE_FLOW = {
    "plan_gate": {"scope": "plan", "on_pass": "delivering", "on_revise": "planning", "counter": "revisions"},
    "delivery_gate": {"scope": "delivery", "on_pass": "completed", "on_revise": "delivering", "counter": "iterations"},
}
_FORWARD = {"planning": "plan_gate", "delivering": "delivery_gate"}
_TERMINAL = ("completed", "failed", "canceled")


def _loop_progress(host: Any, loop_id: str) -> dict[str, Any]:
    raw = (host.memory.recall(loop_id) or {}).get("progress")
    return json.loads(raw) if raw else {"iterations": 0, "revisions": 0, "stalled": 0, "signature": ""}


def _save_progress(host: Any, loop_id: str, progress: dict[str, Any]) -> None:
    host.memory.update(loop_id, {"progress": json.dumps(progress)})


def _gate_decision(host: Any, loop_id: str, *, judge_output: str = "",
                   criteria_cwd: str | None = None) -> dict[str, Any]:
    """Run the loop's criteria to ONE gate decision + a no-progress signature.
    Any human criterion → ``input-required``; any revise → ``revise`` (signature =
    the joined revise evidence, looper's failure-signature); else ``pass``."""
    verdicts = [check_criterion(c, cwd=criteria_cwd, judge_output=judge_output)
                for c in _loop_criteria(host, loop_id)]
    if any(v["verdict"] == "input-required" for v in verdicts):
        return {"decision": "input-required", "signature": "", "verdicts": verdicts}
    revises = [v for v in verdicts if v["verdict"] == "revise"]
    if revises:
        sig = "|".join(sorted(
            str(v.get("evidence") or v.get("notes") or v.get("warning") or "revise")
            for v in revises))
        return {"decision": "revise", "signature": sig, "verdicts": verdicts}
    return {"decision": "pass", "signature": "", "verdicts": verdicts}


def advance(host: Any, loop_id: str, *, artefact: str = "", judge_output: str = "",
            criteria_cwd: str | None = None) -> dict[str, Any]:
    """Advance the loop ONE transition (Spec 366) — the in-session walk step.

    - planning/delivering: the host drafts the artefact; transition forward.
    - plan_gate/delivery_gate: run the gate (criteria + council verdict), ask
      ``control_evaluate``, then ``lifecycle.move``. pass → forward; revise →
      back (counter++); a denied guard → ``failed`` carrying the stop_reason.
    Returns ``{state, decision, stop_reason?, review?, revisions?, iterations?}``.
    """
    props = host.memory.recall(loop_id) or {}
    state = props.get("state")
    control = json.loads(props.get("loop_control") or "{}")
    progress = _loop_progress(host, loop_id)

    if state in _TERMINAL:
        return {"state": state, "decision": "terminal", "stop_reason": progress.get("stop_reason", "")}

    if state in _FORWARD:  # host drafts the plan / delivery artefact, then move on
        nxt = _FORWARD[state]
        host.lifecycle.move(loop_id, nxt, evidence=artefact or f"{state} drafted")
        return {"state": nxt, "decision": "drafted"}

    flow = _GATE_FLOW.get(state)
    if flow is None:
        raise ValueError(f"cannot advance from state {state!r}")

    result = _gate_decision(host, loop_id, judge_output=judge_output, criteria_cwd=criteria_cwd)
    decision = result["decision"]

    if decision == "input-required":  # a human criterion pauses the walk (Spec 285)
        return {"state": state, "decision": "input-required", "review": result["verdicts"]}

    def _fail(stop_reason: str) -> dict[str, Any]:
        progress["stop_reason"] = stop_reason
        _save_progress(host, loop_id, progress)
        host.lifecycle.move(loop_id, "failed", evidence=f"stop:{stop_reason}")
        return {"state": "failed", "decision": decision, "stop_reason": stop_reason,
                "review": result["verdicts"]}

    if decision == "pass":
        guard = control_evaluate(control, progress)
        if not guard["permit"]:
            return _fail(guard["stop_reason"])
        host.lifecycle.move(loop_id, flow["on_pass"], evidence=artefact or "gate passed")
        return {"state": flow["on_pass"], "decision": "pass", "review": result["verdicts"]}

    # revise: count the cycle + track the no-progress signature BEFORE the guard.
    progress[flow["counter"]] = progress.get(flow["counter"], 0) + 1
    sig = result["signature"]
    if sig and sig == progress.get("signature"):
        progress["stalled"] = progress.get("stalled", 0) + 1
    else:
        progress["stalled"] = 1
        progress["signature"] = sig
    guard = control_evaluate(control, progress)
    _save_progress(host, loop_id, progress)
    if not guard["permit"]:
        return _fail(guard["stop_reason"])
    host.lifecycle.move(loop_id, flow["on_revise"], evidence=f"revise:{sig}")
    return {"state": flow["on_revise"], "decision": "revise", "review": result["verdicts"],
            "revisions": progress.get("revisions", 0), "iterations": progress.get("iterations", 0)}


# --- Spec 367: the loop-design wizard (a walkable skill) ----------------------
# Looper's 7-stage interview as a walkable skill (Spec 081/152): one phase per
# turn, each composing the REUSE verbs (intent/gate/persona/panel + the lifecycle
# pillar + _loop). Registered into the develop ontology (no new capability), so it
# walks via `develop.skill_walk` and is discoverable. The council + control phases
# are HARD gates — the two invariants looper itself refuses to emit without: a
# verdict source for every revise_until_clean gate (365) and a termination guard
# (366). The ASCII preview (phase 6) is DERIVED from the graph, never authored.

from .skill import phase  # canonical phase-dict builder (Spec 286)

LOOP_DESIGN_SKILL: dict[str, Any] = {
    "name": "loop-design",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"design.*loop|loop.?design|agent.*loop|looper",
                     "confidence": 0.8},
    "phases": [
        # Spec 378 — inline phase content (A1/A6) for the looper design wizard.
        phase(1, "goal", produces=["goal_id"], verbs=["intent.capture", "intent.confirm"],
              goal="Capture and confirm the loop's objective.",
              instructions="State what the loop must ACHIEVE (not how it iterates) and "
                           "confirm it as an intent — every later phase serves this goal.",
              freedom="high"),
        phase(2, "verification", produces=["criteria"], verbs=["gate.check"],
              goal="Define the criteria that decide pass vs revise.",
              instructions="Name the checkable criteria each iteration is judged against "
                           "(the gate predicates). A loop with no verification can't know "
                           "when it's done — or when to revise.",
              freedom="medium"),
        phase(3, "host", produces=["host"], verbs=["persona.create"],
              goal="Choose the host that runs each iteration.",
              instructions="Select/declare the host persona that executes the loop body "
                           "and the family it belongs to (local agent, subagent, Jules).",
              freedom="medium"),
        phase(4, "council", produces=["council"], gate="hard",
              verbs=["persona.create", "panel.convene"],
              goal="Seat a verdict source for every revise-until-clean gate.",
              instructions="Every revise gate needs a verdict source — a judge member or "
                           "a human criterion (Spec 365). Confirm this gate only when each "
                           "gate has one; a gate with no judge loops forever.",
              freedom="medium"),
        phase(5, "control", produces=["loop_id"], gate="hard", verbs=["lifecycle.open"],
              goal="Declare the termination guards and open the loop.",
              instructions="Declare at least one termination guard (max_iterations, budget, "
                           "or no-progress stall) — a guard-free loop is REFUSED (Spec 366). "
                           "Open the loop lifecycle. Confirm only when a guard is present.",
              freedom="low"),
        phase(6, "confirm", produces=["preview_ok"], requires_input=["preview_ok"],
              verbs=["_loop.preview"],
              goal="Preview the resolved loop before emission.",
              instructions="Render the preview (states + criteria + council + stops, "
                           "DERIVED from the machine so it can't drift) and review it. The "
                           "phase pauses for your preview_ok — don't rubber-stamp.",
              freedom="low"),
        phase(7, "emit", produces=["emitted"], verbs=["_loop.emit"],
              goal="Emit the portable loop artefacts.",
              instructions="Compile the resolved loop and emit its portable files. The "
                           "emitted loop is what actually runs — verify it matches the "
                           "preview.",
              freedom="low"),
    ],
}


def termination_guard_present(control: dict[str, Any]) -> bool:
    """Phase-5 gate predicate (366 invariant): the loop declares ≥1 termination guard."""
    return _has_termination_guard(control.get("max_iterations", 0),
                                  control.get("budget"),
                                  control.get("no_progress_stall", 0))


def verdict_source_present(host: Any, loop_id: str, *, host_family: str = "") -> bool:
    """Phase-4 gate predicate (365 reviewer-only rule): every revise_until_clean
    gate has a verdict source (a judge member or a human criterion)."""
    return recommend_council(host, loop_id, host_family=host_family)["verdict_sources_ok"]


def preview(host: Any, loop_id: str) -> dict[str, Any]:
    """Render the terminal-friendly ASCII flow looper shows before emission (Spec
    367 phase 6) — DERIVED from the loop machine (366) + criteria (364) + council
    (365), so it can never drift from what will actually run. Returns
    ``{ascii, states, criteria, council, control}``.
    """
    from ._lifecycle_machines import resolve_machine
    machine = resolve_machine("loop")
    criteria = _loop_criteria(host, loop_id)
    members = _loop_members(host, loop_id)
    control = json.loads((host.memory.recall(loop_id) or {}).get("loop_control") or "{}")

    crit_txt = ", ".join(f"{c['kind']}:{c['id']}" for c in criteria) or "none"
    council_txt = ", ".join(f"{m['role']}/{m.get('family') or '?'}" for m in members) or "none"
    caps = [f"{k}={control[k]}" for k in ("max_iterations", "max_revisions", "no_progress_stall")
            if control.get(k)]
    if control.get("budget"):
        caps.append(f"budget={control['budget']}")
    stops = ", ".join(caps) or "NONE — a guard-free loop is refused"

    lines = [
        "loop-design preview",
        "===================",
        "  planning → plan_gate ──pass──▶ delivering → delivery_gate ──pass──▶ completed",
        "                │ revise                          │ revise",
        "                ▼                                  ▼",
        "             planning                          delivering",
        "",
        f"criteria ({len(criteria)}): {crit_txt}",
        f"council ({len(members)}): {council_txt}",
        f"stops: {stops}",
    ]
    return {"ascii": "\n".join(lines), "states": machine["states"],
            "criteria": criteria, "council": members, "control": control}


# --- Spec 368: compile (graph → resolved) + emit (render portable files) ------
# The graph is the source of truth; files are a peer projection (CLAUDE.md rule 2).
# `compile` resolves the spine nodes into looper's loop.resolved.json shape (the
# SAME contract the ported run-loop.py reads, 369); `emit` projects the portable
# workspace. Schemas are vendored under loop/schemas/; validation reuses jsonschema
# against the self-contained loop.v1 schema + the reviewer-only rule (365).

_SCHEMA_DIR = Path(__file__).parent / "_lifecycle_data" / "loop" / "schemas"
_TEMPLATE_DIR = Path(__file__).parent / "_lifecycle_data" / "loop" / "templates"


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _member_argv(member: dict[str, Any]) -> list[str]:
    """Resolve a council member to an argv invocation (369 registry shape) — NEVER
    a shell string. The CLI is the member's family/driver; argv is `[cli, "-p"]`."""
    cli = member.get("driver") or member.get("family") or "host"
    return [cli, "-p"]


def _validate_resolved(resolved: dict[str, Any]) -> list[dict[str, str]]:
    """Validate the resolved spec against loop.v1 (self-contained, jsonschema) +
    the resolved-extra keys + the reviewer-only rule. Returns typed findings."""
    findings: list[dict[str, str]] = []
    try:
        import jsonschema
        base = json.loads((_SCHEMA_DIR / "loop.v1.schema.json").read_text(encoding="utf-8"))
        for e in jsonschema.Draft202012Validator(base).iter_errors(resolved):
            findings.append({"path": "/".join(str(p) for p in e.path), "message": e.message})
    except ImportError:  # jsonschema is a dev/analyze extra — degrade to structural
        for key in ("version", "goal", "host", "gates", "loop_control", "workspace"):
            if key not in resolved:
                findings.append({"path": key, "message": f"missing required key {key!r}"})
    for key in ("compiled_at", "source", "criteria_by_id", "council_by_id"):
        if key not in resolved:
            findings.append({"path": key, "message": f"missing resolved field {key!r}"})
    # The reviewer-only rule (365) — schema can't express it; enforce semantically.
    for gname, g in resolved.get("gates", {}).items():
        if g.get("verdict_policy") == "revise_until_clean" and not g.get("verdict_source"):
            findings.append({"path": f"gates/{gname}",
                             "message": "revise_until_clean gate has no verdict_source (reviewer-only rule, 365)"})
    return findings


def compile(host: Any, loop_id: str) -> dict[str, Any]:
    """Resolve a graph-native loop into looper's loop.resolved.json shape (Spec
    368): expand refs, build ``criteria_by_id`` + ``council_by_id``, inline judge
    rubrics, resolve every member to an argv invocation, carry loop_control +
    workspace. Validates against loop.resolved.v1. Pure — no side effects. Returns
    ``{resolved, valid, findings}``.
    """
    props = host.memory.recall(loop_id) or {}
    control = json.loads(props.get("loop_control") or "{}")
    criteria_raw = _loop_criteria(host, loop_id)
    members_raw = _loop_members(host, loop_id)
    rows = host.memory.g.query(
        "MATCH (l)-[:SERVES]->(i:Intent) WHERE l.id=$lid "
        "RETURN i.purpose AS purpose, i.acceptance AS acceptance, "
        "i.context_sources AS context_sources",
        {"lid": loop_id})
    intent = rows[0] if rows else {}

    criteria: list[dict[str, Any]] = []
    criteria_by_id: dict[str, Any] = {}
    for c in criteria_raw:
        cr: dict[str, Any] = {"id": c["id"], "type": c["kind"]}   # spine `kind` → looper `type`
        if c["kind"] == "programmatic":
            cr["check"] = list(c.get("check", []))
            cr["expect"] = c.get("expect", "exit_zero")
            if c.get("contains"):
                cr["contains"] = c["contains"]
        elif c["kind"] == "judge":
            cr["rubric"] = c.get("rubric", "")                     # inline the rubric
        else:
            cr["prompt"] = c.get("prompt", "")
        criteria.append(cr)
        criteria_by_id[cr["id"]] = cr

    council: list[dict[str, Any]] = []
    council_by_id: dict[str, Any] = {}
    for m in members_raw:
        entry = {"id": m["id"], "role": m["role"],
                 "cli": m.get("family") or m.get("driver") or "host",
                 "invoke": _member_argv(m), "scope": [m.get("scope", "both")],
                 "local": bool(m.get("local"))}
        council.append(entry)
        council_by_id[m["id"]] = entry

    def _gate(scope: str) -> dict[str, Any]:
        member_ids = [m["id"] for m in members_raw if m.get("scope") in ("both", scope)]
        judges = [m["id"] for m in members_raw
                  if m["role"] == "judge" and m.get("scope") in ("both", scope)]
        g: dict[str, Any] = {"when": f"after_{scope}", "members": member_ids,
                             "verdict_policy": "revise_until_clean",
                             "criteria": [c["id"] for c in criteria],
                             "max_revisions": control.get("max_revisions", DEFAULT_MAX_REVISIONS)}
        if judges:
            g["verdict_source"] = judges[0]
        return g

    lc: dict[str, Any] = {"max_iterations": control.get("max_iterations", DEFAULT_MAX_ITERATIONS)}
    if control.get("budget"):
        lc["budget"] = control["budget"]
    if control.get("no_progress_stall"):
        lc["no_progress"] = {"max_stalled_iterations": control["no_progress_stall"], "action": "stop"}
    # stop_conditions are DERIVED from the control fields (derivability), not authored.
    lc["stop_conditions"] = [f"max_iterations:{lc['max_iterations']}",
                             f"max_revisions:{control.get('max_revisions', DEFAULT_MAX_REVISIONS)}"]
    if control.get("no_progress_stall"):
        lc["stop_conditions"].append(f"no_progress:{control['no_progress_stall']}")
    if control.get("budget"):
        lc["stop_conditions"].append("budget")

    context_sources = []
    if intent.get("context_sources"):
        try:
            context_sources = json.loads(intent["context_sources"])
        except (json.JSONDecodeError, TypeError):
            context_sources = []

    resolved = {
        "version": 1,
        "goal": {
            "statement": intent.get("purpose", ""),
            "definition_of_done": intent.get("acceptance", ""),
            "verification": criteria,
            "context_sources": context_sources,
        },
        "host": {"cli": "host", "invoke": ["host", "-p"], "timeout_sec": 600},
        "council": council,
        "gates": {"plan_gate": _gate("plan"), "delivery_gate": _gate("delivery")},
        "loop_control": lc,
        "execution": {"mode": "in_session"},
        "workspace": {"dir": "loop-workspace", "layout": ["plan", "delivery", "review"]},
        "compiled_at": _now_iso(),
        "source": f"graph:{loop_id}",
        "criteria_by_id": criteria_by_id,
        "council_by_id": council_by_id,
    }
    findings = _validate_resolved(resolved)
    return {"resolved": resolved, "valid": not findings, "findings": findings}


def _anchored(loop_id: str, body: str) -> str:
    """Prefix the Spec 292 document-binding anchor so an on-disk edit round-trips
    via document.sync."""
    return f"<!-- agency-node: {loop_id} -->\n{body}"


def emit(host: Any, loop_id: str, target: str) -> dict[str, Any]:
    """Project the loop to its portable workspace (Spec 368): loop.yaml,
    loop.resolved.json, LOOP.md, RUN_IN_SESSION.md, README.md, loop-workspace/.
    Each rendered markdown carries the agency-node anchor (Spec 292 round-trip).
    Returns ``{files, valid, findings}``.
    """
    out = Path(target)
    out.mkdir(parents=True, exist_ok=True)
    compiled = compile(host, loop_id)
    resolved = compiled["resolved"]

    # loop.yaml — the human-authored (loop.v1) form: resolved minus resolved-only keys.
    authoring = {k: v for k, v in resolved.items()
                 if k not in ("compiled_at", "source", "criteria_by_id", "council_by_id")}
    try:
        import yaml
        loop_yaml = yaml.safe_dump(authoring, sort_keys=False)
    except ImportError:
        loop_yaml = json.dumps(authoring, indent=2)

    pv = preview(host, loop_id)
    files: list[str] = []

    def _write(name: str, text: str) -> None:
        (out / name).write_text(text, encoding="utf-8")
        files.append(str(out / name))

    _write("loop.yaml", loop_yaml)
    _write("loop.resolved.json", json.dumps(resolved, indent=2, sort_keys=True))
    _write("LOOP.md", _anchored(loop_id,
        f"# Loop — {resolved['goal']['statement'] or '(goal)'}\n\n"
        f"**Definition of done:** {resolved['goal']['definition_of_done']}\n\n"
        f"```\n{pv['ascii']}\n```\n"))
    _write("RUN_IN_SESSION.md", _anchored(loop_id,
        "# Run this loop in-session (the spine walk)\n\n"
        "Walk the `loop` lifecycle machine (Spec 366):\n\n"
        "1. Read `loop.resolved.json` + the context sources.\n"
        "2. Draft the plan artefact; `advance` planning → plan_gate.\n"
        "3. At plan_gate run the criteria + council verdict; pass → delivering, "
        "revise → planning (counts a revision).\n"
        "4. Draft delivery-N; `advance` delivering → delivery_gate; pass → completed.\n"
        "5. Stop on pass / cap / no-progress — the control guards are enforced.\n"))
    _write("README.md", _anchored(loop_id,
        "# Loop workspace\n\n"
        "Run in-session (see `RUN_IN_SESSION.md`) or externally: "
        "`python run-loop.py loop.resolved.json` (emitted by 369).\n\n"
        "Ported from [looper](https://github.com/ksimback/looper) "
        "(Kevin Simback, MIT) — the loop-design discipline, rubrics, the "
        "loop.yaml/run-loop.py shapes, and the termination model.\n"))
    for sub in ("plan", "delivery", "review"):
        (out / "loop-workspace" / sub).mkdir(parents=True, exist_ok=True)
    files.append(str(out / "loop-workspace"))

    return {"files": files, "valid": compiled["valid"], "findings": compiled["findings"]}


# --- Spec 369: external runner, model detection & egress (out-of-session twin) -
# The loop runs in two surfaces over ONE resolved contract (368): the in-session
# spine walk (366) and looper's external stdlib run-loop.py. 369 ports model
# detection (§6), the egress-consent gate (§9), and the runner template — reusing
# shell/driver/config/gate. Metadata-only, secret-free, argv + consent enforced.

MODEL_DETECTION_RUBRIC = "model-detection.md"

# Looper's model allowlist (§6) — family + local flag per CLI. `local` marks an
# on-device model (no egress). Probed by PATH; auth stays in each CLI's keychain.
_MODEL_ALLOWLIST = {
    "claude":  {"family": "anthropic", "local": False},
    "codex":   {"family": "openai",    "local": False},
    "gemini":  {"family": "google",    "local": False},
    "llm":     {"family": "llm",       "local": False},
    "ollama":  {"family": "ollama",    "local": True},
}
# Secret-shaped material that must NEVER enter the registry / an emitted artefact
# (looper File Rule — auth lives in the CLI keychain, not in invoke argv).
_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|--?key\b|--?token\b|secret|password|bearer\s)", re.I)
# Default redaction globs applied before any cross-vendor send (looper §9).
_DEFAULT_REDACT = ("**/.env", "**/.env.*", "secrets/**", "**/*.key")


def _model_store(store_path: str | None) -> list[dict[str, Any]]:
    if not store_path:
        return []
    p = Path(store_path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def detect_models(*, which: Any = None, store_path: str | None = None) -> dict[str, Any]:
    """Probe the looper model allowlist by PATH (Spec 369 §6). Records invocation
    metadata ONLY — argv + family + local flag — NEVER API keys/tokens (auth stays
    in each CLI's keychain). Returns ``{models, available}``; persists the available
    set to ``store_path`` (config, 334) when given.
    """
    import shutil
    which = which or shutil.which
    models = []
    for cli, meta in _MODEL_ALLOWLIST.items():
        models.append({"cli": cli, "family": meta["family"], "local": meta["local"],
                       "invoke": [cli, "-p"], "available": bool(which(cli))})
    available = [m for m in models if m["available"]]
    if store_path:
        Path(store_path).write_text(json.dumps(available, indent=2), encoding="utf-8")
    return {"models": models, "available": available}


def register_model(cli: str, family: str, invoke: Any, *, local: bool = False,
                   store_path: str | None = None) -> dict[str, Any]:
    """Register a model invocation (Spec 369 §6). ``invoke`` MUST be an argv array
    (never a shell string) and MUST NOT carry secret-shaped material. Returns
    ``{registered, ...}`` or ``{error}``.
    """
    if not (isinstance(invoke, list) and invoke and all(isinstance(t, str) for t in invoke)):
        return {"error": "invoke must be an argv array, not a shell string (argv-only, Spec 192)"}
    if _SECRET_RE.search(" ".join(invoke)):
        return {"error": "invocation carries secret-shaped material; auth stays in the CLI keychain"}
    entry = {"cli": cli, "family": family, "invoke": list(invoke), "local": bool(local)}
    if store_path:
        reg = _model_store(store_path)
        reg.append(entry)
        Path(store_path).write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return {"registered": True, **entry}


def emit_runner(host: Any, loop_id: str, target: str) -> dict[str, Any]:
    """Write the ported stdlib-only ``run-loop.py`` (Spec 369) — reads ONLY
    ``loop.resolved.json`` and runs the SAME contract the spine walk runs. Copied
    from the vendored template (looper File Rule: copy verbatim). Returns ``{file}``.
    """
    out = Path(target)
    out.mkdir(parents=True, exist_ok=True)
    runner = (_TEMPLATE_DIR / "run-loop.py.tmpl").read_text(encoding="utf-8")
    (out / "run-loop.py").write_text(runner, encoding="utf-8")
    return {"file": str(out / "run-loop.py")}


def egress_consent(member: dict[str, Any], *, consent_given: bool = False,
                   policy: str = "required", redact_globs: Any = None,
                   context_paths: Any = None) -> dict[str, Any]:
    """The cross-vendor egress gate (Spec 369 §9), consulted before any cross-vendor
    send IN-SESSION and in the external runner. local member → permit (no egress);
    no ``required`` policy → permit; first cross-vendor send → require consent;
    redaction globs are applied (redacted paths stubbed, not transmitted). Pure —
    the consent is recorded as provenance by the caller. Returns ``{permit,
    requires_consent, redacted, reason}``.
    """
    import fnmatch
    globs = list(redact_globs) if redact_globs is not None else list(_DEFAULT_REDACT)
    redacted = [p for p in (context_paths or [])
                if any(fnmatch.fnmatch(p, g) for g in globs)]
    if member.get("local"):
        return {"permit": True, "requires_consent": False, "redacted": redacted,
                "reason": "local member — no egress"}
    if policy != "required":
        return {"permit": True, "requires_consent": False, "redacted": redacted,
                "reason": "no consent policy"}
    if not consent_given:
        return {"permit": False, "requires_consent": True, "redacted": redacted,
                "reason": "cross-vendor send requires first-send consent"}
    return {"permit": True, "requires_consent": False, "redacted": redacted,
            "reason": "consent recorded"}
