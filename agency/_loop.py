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
