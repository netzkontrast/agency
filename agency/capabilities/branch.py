"""branch — finish a development branch: detect state, then merge / open a PR /
keep / discard (superpowers-port Phase 2).

Ports the `finishing-a-development-branch` discipline. `assess` (transform) reads
the branch state and recommends an action (judgment-as-code); `finish` (effect)
executes the chosen action and records the outcome as provenance. The VCS boundary
(`VCSBackend`) is injected, so tests never touch a real repo.
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension
from ._vcs import GitClient

_ACTIONS = {"merge", "pr", "keep", "discard"}


def _recommend(state: dict) -> str:
    "The finishing-a-branch decision as code: keep if dirty, discard if nothing landed, else merge/PR."
    if state.get("dirty"):
        return "keep"                                       # uncommitted work — don't finish yet
    if int(state.get("ahead", 0) or 0) == 0:
        return "discard"                                    # nothing ahead to land
    return "merge" if int(state.get("behind", 0) or 0) == 0 else "pr"   # diverged -> open a PR


class BranchCapability(CapabilityBase):
    name = "branch"
    home = "lifecycle"
    ontology = OntologyExtension(nodes={"BranchOutcome": ["branch", "action", "ok"]})

    @verb(role="transform", inject=["vcs"])
    def assess(self, vcs, branch: str, base: str = "main") -> dict:
        "Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard."
        state = (vcs or GitClient()).state(branch=branch, base=base)
        return {"result": {**state, "recommended": _recommend(state)}}

    @verb(role="effect", inject=["vcs"])
    def finish(self, vcs, branch: str, action: str, base: str = "main") -> dict:
        "Finish the branch by the chosen action (merge/pr/keep/discard); record the outcome."
        if action not in _ACTIONS:
            return {"result": {"error": f"unknown action {action!r}", "actions": sorted(_ACTIONS)}}
        res = (vcs or GitClient()).finish(branch=branch, action=action, base=base)
        ok = bool(res.get("ok", True))
        o = self.ctx.record("BranchOutcome", {"branch": branch, "action": action, "ok": ok,
                                              "detail": (res.get("detail") or "")[:2000]})
        self.ctx.link(o, self.ctx.intent_id, "SERVES")
        return {"result": {"outcome": o, "branch": branch, "action": action, "ok": ok,
                           "detail": res.get("detail", "")}}
