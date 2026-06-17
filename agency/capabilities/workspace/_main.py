# agency-scaffold: v1
"""workspace — isolate work in a git worktree + record a green baseline.

Workspace isolates work in a git worktree and records a green baseline, so risky changes start from a clean, provably-green point that recovery can return to.

Use when: work should be isolated in a git worktree with a recorded green baseline — a clean, provably-green starting point before risky changes.
Triggers:
- Risky changes that should not touch the main working tree
- A starting point that must be provably green before edits
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension
from .._vcs import GitClient




class WorkspaceCapability(CapabilityBase):
    name = "workspace"
    home = "lifecycle"
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={"Workspace": ["path", "branch", "base"],
               "Baseline": ["command", "passed"]},
        edges={"BASELINED"},
    )

    @verb(role="effect", inject=["vcs"])
    def isolate(self, vcs, branch: str, base: str = "main") -> dict:
        """Create an isolated git worktree on a fresh branch off `base`, recording the Workspace.

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
        w = self.ctx.record_and_serve("Workspace", {"path": wt["path"], "branch": wt["branch"], "base": base})
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
