"""_vcs — the version-control boundary the `workspace` and `branch` capabilities
talk to.

`VCSBackend` is a Protocol; `GitClient` is the default backend — real `git` (and
`gh` for PRs) via subprocess. Like the Jules backend, it is INJECTED: the engine
wires the real client in production while deterministic tests inject a stand-in,
so no test ever touches a real repository. (Underscore-named so capability
discovery skips it — it is a boundary, not a capability.)
"""
from __future__ import annotations

import os
import shlex
import subprocess
from typing import Protocol


class VCSBackend(Protocol):
    """The git/gh boundary `workspace` and `branch` depend on."""
    def worktree(self, branch: str, base: str) -> dict: ...
    def run(self, command: str, cwd: str) -> dict: ...
    def state(self, branch: str, base: str) -> dict: ...
    def finish(self, branch: str, action: str, base: str) -> dict: ...
    def remote_exists(self, branch: str, remote: str = "origin") -> dict: ...


    def remote_exists(self, branch: str) -> bool: ...


class GitClient:
    """The default VCS backend: real `git`/`gh` subprocesses against the current
    repository. Never invoked by the test suite (tests inject a stand-in)."""

    def _git(self, *args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)

    def worktree(self, branch: str, base: str) -> dict:
        path = os.path.abspath(os.path.join("..", f"wt-{branch.replace('/', '-')}"))
        r = self._git("worktree", "add", "-b", branch, path, base)
        # signal failure (e.g. branch already exists) so callers don't record a
        # Workspace for a worktree that was never created.
        return {"path": path, "branch": branch, "base": base, "ok": r.returncode == 0,
                "detail": (r.stdout + r.stderr).strip()}

    def run(self, command: str, cwd: str) -> dict:
        # the operator-provided verification command; split (no shell) to avoid injection
        p = subprocess.run(shlex.split(command), cwd=cwd or None, capture_output=True, text=True)
        return {"returncode": p.returncode, "output": (p.stdout + p.stderr)}

    def state(self, branch: str, base: str) -> dict:
        a = self._git("rev-list", "--count", f"{base}..{branch}")
        b = self._git("rev-list", "--count", f"{branch}..{base}")
        if a.returncode or b.returncode:                       # invalid ref -> surface, don't fake 0/0
            return {"ahead": 0, "behind": 0, "dirty": False, "ok": False,
                    "detail": (a.stderr + b.stderr).strip()}
        dirty = bool(self._git("status", "--porcelain").stdout.strip())
        return {"ahead": int(a.stdout.strip() or 0), "behind": int(b.stdout.strip() or 0),
                "dirty": dirty, "ok": True}

    def remote_exists(self, branch: str, remote: str = "origin") -> dict:
        """Authoritative remote-branch check via `git ls-remote` — used by
        `jules.verify` to enforce `COMPLETED != done` (CORE.md:33-35) without
        trusting a caller-supplied bool (spec 006 F3 / spec 012 verify
        independence). `state()` checks only LOCAL ahead/behind; this one
        actually hits origin. Returns `{exists, sha, ok, detail}` — `ok=False`
        means the lookup itself failed (network/auth/unknown remote)."""
        r = self._git("ls-remote", "--heads", remote, branch)
        if r.returncode != 0:
            return {"exists": False, "sha": "", "ok": False,
                    "detail": (r.stdout + r.stderr).strip()}
        line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
        sha = line.split("\t", 1)[0] if line else ""
        return {"exists": bool(sha), "sha": sha, "ok": True, "detail": ""}

    def finish(self, branch: str, action: str, base: str) -> dict:
        if action == "merge":
            r = self._git("merge", "--no-ff", branch)
            return {"action": "merge", "ok": r.returncode == 0, "detail": (r.stdout + r.stderr).strip()}
        if action == "pr":
            p = subprocess.run(["gh", "pr", "create", "--base", base, "--head", branch, "--fill"],
                               capture_output=True, text=True)
            return {"action": "pr", "ok": p.returncode == 0, "detail": (p.stdout + p.stderr).strip()}
        if action == "discard":
            r = self._git("branch", "-D", branch)
            return {"action": "discard", "ok": r.returncode == 0, "detail": (r.stdout + r.stderr).strip()}
        return {"action": "keep", "ok": True, "detail": "branch kept as-is"}

    def remote_exists(self, branch: str) -> bool:
        """Verify if a branch exists on origin."""
        r = self._git("ls-remote", "--heads", "origin", branch)
        return r.returncode == 0 and bool(r.stdout.strip())
