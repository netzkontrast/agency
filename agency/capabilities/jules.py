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
from ._vcs import GitClient


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
    def create(self, prompt: str, source: str, starting_branch: str,
               title: str = "", require_plan_approval: bool = True,
               auto_create_pr: bool = False) -> dict: ...
    def get(self, session: str) -> dict: ...
    def list(self, page_size: int, page_token: str) -> dict: ...
    def activities(self, session: str, page_size: int, only_kinds: str, page_token: str = "") -> dict: ...
    def plan(self, session: str, max_pages: int) -> dict: ...
    def approve_plan(self, session: str) -> dict: ...
    def message(self, session: str, prompt: str) -> dict: ...
    # Spec 012 Phase 2/3 — orbital surface (resolve / ops hygiene / patches).
    def resolve_source(self, owner: str, repo: str) -> dict: ...
    def get_full(self, session: str) -> dict: ...
    def status_all(self, page_size: int, max_pages: int) -> dict: ...
    def approve_awaiting(self, limit: int) -> dict: ...
    def quota(self, daily_limit: int) -> dict: ...
    def patch(self, session: str) -> dict: ...


class JulesClient:
    """The default `jules` backend — the real Jules REST API via the vendored
    `_jules_api` client. Needs `JULES_API_KEY` (checked at call time)."""

    def create(self, prompt: str, source: str, starting_branch: str,
               title: str = "", require_plan_approval: bool = True,
               auto_create_pr: bool = False) -> dict:
        from . import _jules_api
        return _jules_api.jules_create(
            prompt=prompt, source=source, starting_branch=starting_branch,
            title=title, require_plan_approval=require_plan_approval,
            auto_create_pr=auto_create_pr)

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

    # Spec 012 Phase 2/3 — orbital surface.
    def resolve_source(self, owner: str, repo: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_resolve_source_public(owner, repo)

    def get_full(self, session: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_get_full(session)

    def status_all(self, page_size: int, max_pages: int) -> dict:
        from . import _jules_api
        return _jules_api.jules_status_all(page_size=page_size, max_pages=max_pages)

    def approve_awaiting(self, limit: int) -> dict:
        from . import _jules_api
        return _jules_api.jules_approve_awaiting(limit=limit)

    def quota(self, daily_limit: int) -> dict:
        from . import _jules_api
        return _jules_api.jules_quota(daily_limit=daily_limit)

    def patch(self, session: str) -> dict:
        from . import _jules_api
        return _jules_api.jules_patch_extract(session)


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
    def dispatch(self, source: str, starting_branch: str, prompt: str,
                 title: str = "", require_plan_approval: bool = True,
                 auto_create_pr: bool = False, alias: str = "") -> dict:
        """Spawn a remote Jules session (external effect). Returns id/url/state.

        Param completeness (R2 audit gap closure): the default flips to
        `require_plan_approval=True` — the recommended-by-the-reference shape
        the watcher's `review_and_approve_plan` WatchEvent is built for; the
        old `False` default is a opt-out, not the doctrine. `title`,
        `auto_create_pr`, `alias` ride through to the API. When `alias` is
        supplied, the alias + the JulesSession node are recorded in the bi-
        temporal graph (the registry is the graph, per CORE.md:38-45)."""
        s = self._backend().create(prompt=prompt, source=source,
                                   starting_branch=starting_branch, title=title,
                                   require_plan_approval=require_plan_approval,
                                   auto_create_pr=auto_create_pr)
        sid = s.get("id") or s.get("name")
        # Register in the bi-temporal graph (spec 012 — no parallel sessions.json).
        if sid:
            sess_id = f"jules-session:{sid}"
            if self.ctx.memory.recall(sess_id) is None:
                node_props = {"sid": sid, "url": s.get("url") or "",
                              "title": title, "branch": starting_branch, "source": source}
                state = s.get("state")
                if state in JULES_STATES:                       # only set if valid (avoid ontology violation)
                    node_props["state"] = state
                self.ctx.memory.record("JulesSession", node_props, node_id=sess_id)
            if alias:
                alias_id = f"jules-alias:{alias}"
                self.ctx.memory.record("JulesAlias", {"name": alias, "sid": sid}, node_id=alias_id)
                self.ctx.memory.link(alias_id, sess_id, "ALIAS_OF")
        return {
            "status": s.get("state", "submitted"),
            "session": sid,
            "url": s.get("url"),
            "alias": alias,
            "artefact": {"kind": "jules-session", "session": sid or "", "url": s.get("url") or ""},
        }

    @verb(role="transform")
    def status(self, session: str) -> dict:
        """Read a session's full state from the backend — the trimmed `{state,
        url}` shape was dropping 5 fields the watcher + recovery flow need
        (R2 audit fix; spec 012 Phase 5)."""
        return self._backend().get(session)

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

    @verb(role="transform", inject=["vcs"])
    def verify(self, vcs, state: str, branch: str, remote: str = "origin") -> dict:
        """COMPLETED != done. Derives `branch_on_remote` INDEPENDENTLY from
        origin via the injected `vcs` boundary (`git ls-remote`), dropping the
        caller-supplied bool the original draft trusted (spec 006 F3 / spec
        012 Phase 5). Fail-closed: if the lookup itself errors (network/auth/
        unknown remote), `done=False`; the silent-fail guard must never assume
        truth it cannot prove."""
        if not branch:
            return {"done": False, "state": state, "branch_on_remote": False,
                    "error": "branch is required"}
        chk = (vcs or GitClient()).remote_exists(branch=branch, remote=remote)
        if not chk.get("ok"):
            return {"done": False, "state": state, "branch_on_remote": False,
                    "error": f"remote check failed: {chk.get('detail','')}"}
        branch_on_remote = bool(chk.get("exists"))
        done = str(state).lower() == "completed" and branch_on_remote
        return {"done": done, "state": state, "branch_on_remote": branch_on_remote,
                "sha": chk.get("sha", "")}

    # === Spec 012 Phase 3 — orbital read/admin verbs ==========================

    @verb(role="transform")
    def resolve_source(self, owner: str, repo: str) -> dict:
        """Resolve `owner/repo` to the opaque `sources/<id>` the API expects
        (the composition is undocumented; must list-and-match). Read-only."""
        return self._backend().resolve_source(owner, repo)

    @verb(role="transform")
    def status_all(self, page_size: int = 100, max_pages: int = 20) -> dict:
        """Paginated, grouped-by-state listing of every session on the
        account. Returns `{by_state, totals, total, truncated}`. Operational
        hygiene (lesson-15 §3); the watcher uses it to seed the registry."""
        return self._backend().status_all(page_size, max_pages)

    @verb(role="effect")
    def approve_awaiting(self, limit: int = 0) -> dict:
        """Bulk-approve every session in `AWAITING_PLAN_APPROVAL` (up to
        `limit`, 0 = all). Returns `{approved, skipped}`. The one state with a
        timeout/discard window; don't let it sit (lesson-15 §6)."""
        return self._backend().approve_awaiting(limit)

    @verb(role="transform")
    def quota(self, daily_limit: int = 0) -> dict:
        """Count sessions created today (UTC). `daily_limit` is a caller-
        supplied budget (the API has no quota surface); returns `headroom`
        when supplied. Operational hygiene (lesson-15 §6)."""
        return self._backend().quota(daily_limit)

    @verb(role="transform")
    def patch(self, session: str) -> dict:
        """Per-output stats (`files`, `lines`, `bytes`) from the session's
        `outputs[*].changeSet.gitPatch.unidiffPatch` — NO body. Used by the
        watcher to classify silent-fail variants (empty patch vs missing
        push). Body retrieval is the explicit `patch_body` verb."""
        return self._backend().patch(session)

    @verb(role="transform")
    def patch_body(self, session: str, output_index: int = 0, max_bytes: int = 4096) -> dict:
        """Explicit, capped unidiff retrieval for one of the session's outputs
        — default cap 4 KB so a careless call can't blow the agent's context.
        Returns `{unidiff, truncated, original_bytes}`. The recovery flow's
        `apply_patch` is the only common caller (spec 012)."""
        outs = (self._backend().get_full(session).get("outputs") or [])
        if output_index < 0 or output_index >= len(outs):
            return {"error": f"output_index {output_index} out of range (0..{len(outs)-1})"}
        diff = (((outs[output_index] or {}).get("changeSet") or {})
                .get("gitPatch") or {}).get("unidiffPatch") or ""
        orig = len(diff.encode("utf-8"))
        cap = max(0, int(max_bytes))
        return {"unidiff": diff[:cap], "truncated": orig > cap, "original_bytes": orig}

    @verb(role="act")
    def alias(self, name: str, session: str = "") -> dict:
        """Read or upsert a stable alias for a Jules sid. Stored as a
        `JulesAlias` node in the bi-temporal graph (no parallel sessions.json
        per the canon CORE.md:38-45). With `session=""` looks up; with a
        non-empty `session`, upserts both the alias and a stub `JulesSession`
        node (the watcher fills in fields later) and links `ALIAS_OF`."""
        mem = self.ctx.memory
        alias_id = f"jules-alias:{name}"
        if not session:
            node = mem.recall(alias_id)
            if not node:
                return {"error": f"no such alias: {name}"}
            return {"name": name, "session": node.get("sid")}
        sess_id = f"jules-session:{session}"
        if mem.recall(sess_id) is None:
            mem.record("JulesSession", {"sid": session}, node_id=sess_id)
        mem.record("JulesAlias", {"name": name, "sid": session}, node_id=alias_id)
        mem.link(alias_id, sess_id, "ALIAS_OF")
        return {"name": name, "session": session}

    @verb(role="transform")
    def lint_prompt(self, text: str, must_name: str = "") -> dict:
        """Lint a dispatch prompt against the canonical must-name tool list.

        Returns ``{ok: bool, missing: [str], extras: [str]}``. Symmetric with
        ``plugin.lint_skill``: a pure predicate, no side effects, no memory
        writes. Consumed by the ``jules-protocol-preamble`` skill (Phase 3
        ``name-canonical-tools``) and reusable by ``jules-pr-review-cycle``
        for outbound replies.

        ``must_name`` is a comma-separated override; empty string falls back
        to the full canon from ``_jules_preambles._MUST_NAME_TOOLS``
        (``pre_commit_instructions``, ``submit``, ``request_user_input``,
        ``replace_with_git_merge_diff``, ``request_code_review``). String
        instead of ``list[str]`` so the verb auto-wires cleanly through MCP
        / bash CLI without nested-type schema gymnastics.
        """
        from ._jules_preambles import lint_must_name
        names = [s.strip() for s in must_name.split(",") if s.strip()] if must_name else None
        return lint_must_name(text, must_name=names)
