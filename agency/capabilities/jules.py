"""jules — the agent capability. An agent IS a Lifecycle parameterization that
dispatches a remote async session and inserts a `verify` step, because
`COMPLETED != done`: the Jules session state flips to COMPLETED even when it
paused before pushing a branch. `verify` checks the branch on REMOTE — the
silent-fail guard — always verify the branch on origin before trusting completion.

The verbs cover the whole session lifecycle the v1alpha API exposes:
`dispatch` (create) · `status`/`list`/`activities`/`plan` (read) ·
`approve_plan`/`message` (drive) · `verify` (done-check) · `stop` (documents that
the API has no cancel). `message` is input-only — resumption is racy — and there is
no cancel: those hard-won semantics live in the verb docstrings.

The capability's boundary is a `JulesBackend` (a Protocol). The default backend,
`JulesClient`, talks to the real Jules REST API via the vendored `_jules_api`
client. The backend is injected, so the engine really dispatches Jules in
production while deterministic tests inject a stand-in.
"""
from __future__ import annotations

from typing import Protocol

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension


# Closed enums — single source of truth for the watcher (spec 012). The state
# set is the Jules v1alpha state machine; the action set is the WatchEvent
# verb the agent reacts to (see Plan/012-…/spec.md "WatchEvent shape").
JULES_STATES = {
    "STATE_UNSPECIFIED", "QUEUED", "PLANNING", "AWAITING_PLAN_APPROVAL",
    "IN_PROGRESS", "AWAITING_USER_FEEDBACK", "COMPLETED", "FAILED",
    "PAUSED", "CANCELLED",
}
WATCH_ACTIONS = {
    "noop", "review_and_approve_plan", "answer_agent_question",
    "verify_pr", "recover_silent_fail", "recover_apply_plan",
    "dispatch_fresh", "inspect_and_resume", "terminal",
}


class JulesBackend(Protocol):
    """The external boundary the `jules` capability talks to — the full Jules
    session lifecycle the v1alpha API actually exposes."""
    def create(self, prompt: str, source: str, starting_branch: str) -> dict: ...
    def get(self, session: str) -> dict: ...
    def list(self, page_size: int, page_token: str) -> dict: ...
    def activities(self, session: str, page_size: int, only_kinds: str, page_token: str = "") -> dict: ...
    def plan(self, session: str, max_pages: int) -> dict: ...
    def approve_plan(self, session: str) -> dict: ...
    def message(self, session: str, prompt: str) -> dict: ...


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

    def list(self, page_size: int, page_token: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_list(page_size=page_size, page_token=page_token)

    def activities(self, session: str, page_size: int, only_kinds: str, page_token: str = "") -> dict:
        from . import _jules_api
        return _jules_api.jules_activities(session, page_size=page_size,
                                           only_kinds=only_kinds, page_token=page_token)

    def plan(self, session: str, max_pages: int) -> dict:
        from . import _jules_api
        return _jules_api.jules_plan(session, max_pages=max_pages)

    def approve_plan(self, session: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_approve_plan(session)

    def message(self, session: str, prompt: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_message(session, prompt)


class JulesCapability(CapabilityBase):
    name = "jules"
    home = "lifecycle"
    # Spec-012 ontology extension: typed nodes for the session registry, alias
    # table, watcher event stream, and patch artefact (the silent-fail recovery
    # input). Merged strictly onto the core per CORE.md:131-133 — never leaks
    # into the core ontology. Extras allowed (the ontology validates required
    # + enums only; richer fields like `title`, `branch`, `url` ride along).
    ontology = OntologyExtension(
        nodes={
            "JulesSession":    ["sid"],
            "JulesAlias":      ["name", "sid"],
            "JulesWatchEvent": ["sid", "action"],
            "JulesPatch":      ["sid", "files", "lines", "bytes"],
        },
        edges={"OBSERVED_OF", "RECOVERED_BY", "ALIAS_OF"},
        enums={
            ("JulesSession",    "state"):  JULES_STATES,
            ("JulesWatchEvent", "action"): WATCH_ACTIONS,
        },
    )

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
    def list(self, page_size: int = 20, page_token: str = "") -> dict:
        "Enumerate sessions (trimmed to id/state/title/url; one page — walk via token)."
        return self._backend().list(page_size, page_token)

    @verb(role="transform")
    def activities(self, session: str, page_size: int = 10, only_kinds: str = "",
                   page_token: str = "") -> dict:
        """A session's activity stream, trimmed to summaries (the costliest Jules read).
        `page_token` walks older pages — without it, older `agentMessaged` /
        failure details become unreachable through `jules.activities` (Codex
        review ccb8f03 / jules.py:139)."""
        return self._backend().activities(session, page_size, only_kinds, page_token)

    @verb(role="transform")
    def plan(self, session: str, max_pages: int = 5) -> dict:
        "The latest generated plan — show it before approve_plan (no PR exists yet)."
        return self._backend().plan(session, max_pages)

    @verb(role="effect")
    def approve_plan(self, session: str) -> dict:
        "Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out; do it promptly."
        return self._backend().approve_plan(session)

    @verb(role="effect")
    def message(self, session: str, prompt: str) -> dict:
        """Send a message into a session (feedback / plan-revision / nudge a COMPLETED
        session to push). Input only, NOT a control plane: resumption is racy — poll
        status after; never use it to revive a FAILED session or to cancel one."""
        return self._backend().message(session, prompt)

    @verb(role="transform")
    def stop(self, session: str) -> dict:
        """UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop —
        only create/get/list/activities/approvePlan/sendMessage. Returns an explanatory
        notice instead of faking it; to intervene, `message` the agent to stand down, or
        wait for a terminal state (COMPLETED/FAILED)."""
        return {
            "error": "unsupported",
            "session": session,
            "message": ("The Jules v1alpha API has no session cancellation. Use `message` "
                        "to ask the agent to stop and leave changes uncommitted, or wait "
                        "for COMPLETED/FAILED."),
        }

    @verb(role="transform")
    def verify(self, state: str, branch_on_remote: bool) -> dict:
        "COMPLETED != done: done only if state is completed AND a branch is on origin."
        done = str(state).lower() == "completed" and bool(branch_on_remote)
        return {"done": done, "state": state, "branch_on_remote": bool(branch_on_remote)}
