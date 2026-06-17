# agency-scaffold: v1
"""branch — finish a development branch: detect state, then merge / open a PR /

Branch inspects the working tree and remote state and finishes the branch the appropriate way — merge when clean, a PR when review is needed, or a clear report of what blocks completion.

Use when: a development branch is ready to wrap up and its state must be detected to merge, open a PR, or report what blocks completion.
Triggers:
- A feature branch whose work appears complete
- Uncertainty whether a branch should merge or open a PR
Red flags:
- Hand-writing a commit message → compose it with capability_branch_commit_smart
- Merging a branch without reading its state → run capability_branch_assess first
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension
from .._vcs import GitClient

_ACTIONS = {"merge", "pr", "keep", "discard"}


def _recommend(state: dict) -> str:
    "The finishing-a-branch decision as code: keep if dirty, discard if nothing landed, else merge/PR."
    if state.get("dirty"):
        return "keep"                                       # uncommitted work — don't finish yet
    if int(state.get("ahead", 0) or 0) == 0:
        return "discard"                                    # nothing ahead to land
    return "merge" if int(state.get("behind", 0) or 0) == 0 else "pr"   # diverged -> open a PR


# Spec 046 F-C — conventional-commit composition as DECIDABLE code (the sc-git pattern,
# agency-flavoured): infer the type + scope from the changed paths, no LLM.
_DOC_EXT = (".md", ".rst", ".txt")


def _infer_commit_type(paths: list[str], summary: str) -> str:
    low = summary.lower()
    if paths and all(p.startswith("tests/") or "/test" in p for p in paths):
        return "test"
    if paths and all(p.startswith("docs/") or p.endswith(_DOC_EXT) for p in paths):
        return "docs"
    if any(w in low for w in ("fix", "bug", "regression", "broken", "crash")):
        return "fix"
    if any(w in low for w in ("refactor", "rename", "cleanup", "tidy", "extract")):
        return "refactor"
    if any(w in low for w in ("ci", "build", "deps", "bump", "chore", "config")):
        return "chore"
    return "feat"


def _infer_scope(paths: list[str]) -> str:
    # a capability path → its name; else the common top-level component
    for p in paths:
        parts = p.split("/")
        if len(parts) >= 3 and parts[:2] == ["agency", "capabilities"]:
            return parts[2].replace(".py", "")
    tops = {p.split("/")[0] for p in paths if "/" in p}
    return next(iter(tops)) if len(tops) == 1 else ""


class BranchCapability(CapabilityBase):
    name = "branch"
    home = "lifecycle"
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(nodes={"BranchOutcome": ["branch", "action", "ok"]})

    @verb(role="transform")
    def commit_smart(self, summary: str, paths: str = "") -> dict:
        """Compose a conventional-commit message from a change summary + the changed paths
        (Spec 046 F-C — decidable, no LLM). Infers ``type(scope): subject``.

        Inputs: summary (one-line description of the change); paths (comma-separated
                changed files — drives the inferred type + scope).
        Returns: ``{message, type, scope}``.
        chain_next: use the message for the commit; then ``branch.assess`` / ``finish``.
        """
        files = [p.strip() for p in paths.split(",") if p.strip()]
        ctype = _infer_commit_type(files, summary)
        scope = _infer_scope(files)
        subject = " ".join(summary.strip().rstrip(".").split())[:60].lower()
        message = f"{ctype}({scope}): {subject}" if scope else f"{ctype}: {subject}"
        return {"result": {"message": message, "type": ctype, "scope": scope}}

    @verb(role="transform", inject=["vcs"])
    def assess(self, vcs, branch: str, base: str = "main") -> dict:
        """Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard.

        Inputs: branch (str), base (str — defaults to 'main').
        Returns: ``{ahead, behind, dirty, recommended}`` (wire shape).
        chain_next: ``branch.finish(branch=, action=recommended)``.
        """
        state = (vcs or GitClient()).state(branch=branch, base=base)
        return {"result": {**state, "recommended": _recommend(state)}}

    @verb(role="effect", inject=["vcs"])
    def finish(self, vcs, branch: str, action: str, base: str = "main") -> dict:
        """Finish the branch by the chosen action (merge/pr/keep/discard) and record the outcome.

        Inputs: branch (str), action (one of merge/pr/keep/discard), base (str).
        Returns: ``{outcome, branch, action, ok, detail}`` (wire shape);
                 ``{error, actions}`` on unknown action.
        chain_next: terminal — outcome node carries the audit trail.
        """
        if action not in _ACTIONS:
            return {"result": {"error": f"unknown action {action!r}", "actions": sorted(_ACTIONS)}}
        res = (vcs or GitClient()).finish(branch=branch, action=action, base=base)
        ok = bool(res.get("ok", True))
        o = self.ctx.record_and_serve("BranchOutcome", {"branch": branch, "action": action, "ok": ok,
                                                        "detail": (res.get("detail") or "")[:2000]})
        return {"result": {"outcome": o, "branch": branch, "action": action, "ok": ok,
                           "detail": res.get("detail", "")}}
