"""workspace — isolate work in a git worktree + record a green baseline.

`effect` verbs for isolated development: `isolate` creates a
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
        """Create an isolated git worktree on a fresh branch off `base`; record the Workspace.

        Inputs: branch (str — new branch name), base (str — default 'main').
        Returns: ``{workspace, path, branch, base}`` on success;
                 ``{error, branch, detail}`` on failure (wire shape).
        chain_next: ``workspace.baseline(workspace=, command=)`` to record
                    the starting GREEN state.
        """
        wt = (vcs or GitClient()).worktree(branch=branch, base=base)
        if not wt.get("ok", True):                             # don't record a phantom worktree
            return {"result": {"error": "worktree creation failed", "branch": branch,
                               "detail": wt.get("detail", "")}}
        w = self.ctx.record("Workspace", {"path": wt["path"], "branch": wt["branch"], "base": base})
        self.ctx.link(w, self.ctx.intent_id, "SERVES")
        return {"result": {"workspace": w, "path": wt["path"], "branch": wt["branch"], "base": base}}

    @verb(role="effect", inject=["vcs"])
    def baseline(self, vcs, workspace: str, command: str) -> dict:
        """Run the baseline test command in the workspace and record the green/red result.

        Inputs: workspace (Workspace node id), command (str — shell test cmd).
        Returns: ``{workspace, passed, output}`` (wire shape);
                 ``{error, workspace}`` on unknown workspace.
        chain_next: caller proceeds with the work; later runs compare against
                    this Baseline via ``BASELINED`` provenance.
        """
        ws = self.ctx.recall(workspace)
        if not ws or not ws.get("path"):                       # don't silently run in the process cwd
            return {"result": {"error": "unknown workspace (run workspace.isolate first)",
                               "workspace": workspace}}
        res = (vcs or GitClient()).run(command=command, cwd=ws["path"])
        passed = int(res.get("returncode", 1)) == 0
        b = self.ctx.record("Baseline", {"command": command, "passed": passed,
                                         "output": (res.get("output") or "")[:2000]})
        self.ctx.link(workspace, b, "BASELINED")
        self.ctx.link(b, self.ctx.intent_id, "SERVES")
        return {"result": {"workspace": workspace, "passed": passed, "output": res.get("output", "")}}
