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
