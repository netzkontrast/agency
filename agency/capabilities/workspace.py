"""workspace — isolate work in a git worktree + record a green baseline
(superpowers-port Phase 2).

Ports the `using-git-worktrees` discipline as `effect` verbs: `isolate` creates a
worktree on a fresh branch (so work can't clobber the main tree) and `baseline`
runs the test command there and records whether the tree starts GREEN — the
baseline later work is measured against. Both record provenance; the VCS boundary
(`VCSBackend`) is injected, so tests never touch a real repo.
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension
from ._vcs import GitClient


class WorkspaceCapability(CapabilityBase):
    name = "workspace"
    home = "lifecycle"
    ontology = OntologyExtension(
        nodes={"Workspace": ["path", "branch", "base"],
               "Baseline": ["command", "passed"]},
        edges={"BASELINED"},
    )

    @verb(role="effect", inject=["vcs"])
    def isolate(self, vcs, branch: str, base: str = "main") -> dict:
        "Create an isolated git worktree on a fresh branch off `base`; record the Workspace."
        wt = (vcs or GitClient()).worktree(branch=branch, base=base)
        w = self.ctx.record("Workspace", {"path": wt["path"], "branch": wt["branch"], "base": base})
        self.ctx.link(w, self.ctx.intent_id, "SERVES")
        return {"result": {"workspace": w, "path": wt["path"], "branch": wt["branch"], "base": base}}

    @verb(role="effect", inject=["vcs"])
    def baseline(self, vcs, workspace: str, command: str) -> dict:
        "Run the baseline test command in the workspace and record the green/red result."
        ws = self.ctx.recall(workspace) or {}
        res = (vcs or GitClient()).run(command=command, cwd=ws.get("path", ""))
        passed = int(res.get("returncode", 1)) == 0
        b = self.ctx.record("Baseline", {"command": command, "passed": passed,
                                         "output": (res.get("output") or "")[:2000]})
        self.ctx.link(workspace, b, "BASELINED")
        self.ctx.link(b, self.ctx.intent_id, "SERVES")
        return {"result": {"workspace": workspace, "passed": passed, "output": res.get("output", "")}}
