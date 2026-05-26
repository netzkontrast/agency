"""jules — the agent capability. An agent IS a Lifecycle parameterization that
dispatches a remote async session and inserts a `verify` step, because
`COMPLETED != done`: the Jules session state flips to COMPLETED even when it
paused before pushing a branch. `verify` checks the branch on REMOTE — the
silent-fail guard — always verify the branch on origin before trusting completion.

The capability's boundary is a `JulesBackend` (a Protocol). The default backend,
`JulesClient`, talks to the real Jules REST API via the vendored `_jules_api`
client. The backend is injected, so the engine really dispatches Jules in
production while deterministic tests inject a stand-in.
"""
from __future__ import annotations

from typing import Protocol

from ..capability import CapabilityBase, verb


class JulesBackend(Protocol):
    """The external boundary the `jules` capability talks to."""
    def create(self, prompt: str, source: str, starting_branch: str) -> dict: ...
    def get(self, session: str) -> dict: ...


class JulesClient:
    """The default `jules` backend — the real Jules REST API via the vendored
    `_jules_api` client. Needs `JULES_API_KEY` (checked at call time)."""

    def create(self, prompt: str, source: str, starting_branch: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_create(
            prompt=prompt, source=source, starting_branch=starting_branch,
            require_plan_approval=False)

    def get(self, session: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_get(session)


class JulesCapability(CapabilityBase):
    name = "jules"
    home = "lifecycle"

    def _backend(self) -> JulesBackend:
        return self.ctx.client or JulesClient()    # the engine injects its jules backend as ctx.client

    @verb(role="effect")
    def dispatch(self, source: str, starting_branch: str, prompt: str) -> dict:
        "Spawn a remote Jules session (external effect). Returns its id/url/state."
        s = self._backend().create(prompt=prompt, source=source, starting_branch=starting_branch)
        sid = s.get("id") or s.get("name")
        return {
            "status": s.get("state", "submitted"),
            "session": sid,
            "url": s.get("url"),
            "artefact": {"kind": "jules-session", "session": sid or "", "url": s.get("url") or ""},
        }

    @verb(role="transform")
    def status(self, session: str) -> dict:
        "Read a session's current state from the backend."
        s = self._backend().get(session)
        return {"state": s.get("state"), "url": s.get("url")}

    @verb(role="transform")
    def verify(self, state: str, branch_on_remote: bool) -> dict:
        "COMPLETED != done: done only if state is completed AND a branch is on origin."
        done = str(state).lower() == "completed" and bool(branch_on_remote)
        return {"done": done, "state": state, "branch_on_remote": bool(branch_on_remote)}
