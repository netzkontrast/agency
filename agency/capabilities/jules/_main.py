# agency-scaffold: v1
"""jules — the agent capability. An agent IS a Lifecycle parameterization that

Jules drives remote agent sessions end-to-end: dispatch, plan approval, follow-ups, and verification that a session reporting completed actually pushed a branch.

Use when: fanning a coding task out to a remote Jules agent session and driving it to a verified PR — dispatching, sending follow-ups, approving plans, and recovering completed-but-unpushed work.
Triggers:
- A coding task suited to a remote agent session
- A Jules session reporting completed but no branch on origin
- A remote plan awaiting approval before it proceeds
Red flags:
- Trusting completed as done → confirm with capability_jules_verify (state and branch on origin)
- Dispatching without a prompt review → run capability_jules_lint_prompt first
"""
from __future__ import annotations

# agency-accept-warn: surface_size jules is legitimately broad agent-orchestration
# (Spec 070 audit: only ~3 cosmetic merges possible; the other ~16 verbs —
# dispatch/message/recover/verify/watch/plan/activities/… — are genuinely distinct).

from typing import Protocol

from ...capability import ArtefactSchemas, CapabilityBase, RenderTemplates, verb
from ...ontology import OntologyExtension
from .._vcs import GitClient


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
               automation_mode: str = "",
               protocol_preset: str = "") -> dict: ...
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
               automation_mode: str = "",
               protocol_preset: str = "") -> dict:
        from . import api as _jules_api
        return _jules_api.jules_create(
            prompt=prompt, source=source, starting_branch=starting_branch,
            title=title, require_plan_approval=require_plan_approval,
            automation_mode=automation_mode,
            protocol_preset=protocol_preset)

    def get(self, session: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_get(session)

    def list(self, page_size: int, page_token: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_list(page_size=page_size, page_token=page_token)

    def activities(self, session: str, page_size: int, only_kinds: str, page_token: str = "") -> dict:
        from . import api as _jules_api
        return _jules_api.jules_activities(session, page_size=page_size,
                                           only_kinds=only_kinds, page_token=page_token)

    def plan(self, session: str, max_pages: int) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_plan(session, max_pages=max_pages)

    def approve_plan(self, session: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_approve_plan(session)

    def message(self, session: str, prompt: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_message(session, prompt)

    # Spec 012 Phase 2/3 — orbital surface.
    def resolve_source(self, owner: str, repo: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_resolve_source_public(owner, repo)

    def get_full(self, session: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_get_full(session)

    def status_all(self, page_size: int, max_pages: int) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_status_all(page_size=page_size, max_pages=max_pages)

    def approve_awaiting(self, limit: int) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_approve_awaiting(limit=limit)

    def quota(self, daily_limit: int) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_quota(daily_limit=daily_limit)

    def patch(self, session: str) -> dict:
        from . import api as _jules_api
        return _jules_api.jules_patch_extract(session)




class JulesCapability(CapabilityBase):
    name = "jules"
    home = "lifecycle"
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    # Spec-012 ontology extension: typed nodes for the session registry, alias
    # table, watcher event stream, and patch artefact (the silent-fail recovery
    # input). Merged strictly onto the core per CORE.md:131-133 — never leaks
    # into the core ontology. Extras allowed (the ontology validates required
    # + enums only; richer fields like `title`, `branch`, `url` ride along).
    from .skills import JULES_SKILLS as _JULES_SKILLS

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
        skills=_JULES_SKILLS,
    )

    def _backend(self) -> JulesBackend:
        # Spec 002 — reach the Jules boundary by name through the DriverRegistry;
        # fall back to ctx.client (the legacy injector seam) then a fresh client,
        # so bare unit tests with no engine still work.
        drivers = getattr(self.ctx, "drivers", None)
        if drivers is not None and drivers.has("jules"):
            return drivers.get("jules")
        return self.ctx.client or JulesClient()    # the engine injects its jules backend as ctx.client

    @verb(role="effect")
    def dispatch(self, source: str, starting_branch: str, prompt: str,
                 title: str = "", require_plan_approval: bool = True,
                 alias: str = "",
                 automation_mode: str = "",
                 protocol_preset: str = "") -> dict:
        """Spawn a remote Jules session (external effect). Returns id/url/state.

        Inputs: source (owner/repo), starting_branch, prompt, title (optional),
                require_plan_approval (bool, default True), alias (optional),
                automation_mode ('' | AUTO_CREATE_PR), protocol_preset (e.g. 'agency-default').
        Returns: ``{status, session, url, alias, artefact: {kind, session, url}}``.
        chain_next: ``jules.status(session=)`` then ``jules.approve_plan(session=)``
                    when state hits AWAITING_PLAN_APPROVAL.

        Param completeness: the default `require_plan_approval=True` is the
        recommended doctrine shape the watcher's `review_and_approve_plan`
        WatchEvent is built for. Spec 013 Phase 4 adds:

        - `automation_mode` — canonical Jules-side field
          (``"" | "AUTO_CREATE_PR"``). The flag interaction matrix
          (`Plan/013-…/DESIGN.md`):
          - `require_plan_approval=True`, `automation_mode=""` — doctrine
            default. Plan-gated, agent confirms PR.
          - `require_plan_approval=True`, `automation_mode="AUTO_CREATE_PR"` —
            agency-driving-Jules pattern. Plan-gated, PR auto-opens.
          - `require_plan_approval=False`, `automation_mode="AUTO_CREATE_PR"` —
            zero-touch. Only safe with a tight `affects:` allow-list.
        - `protocol_preset` (e.g. ``"agency-default"``) — when non-empty,
          prepends the Mode-A/B preamble assembled by
          `_jules_preambles.assemble(...)`. Mode A (dogfood) when source
          == `DISPATCH_SELF_SOURCE`; Mode B (delegate) otherwise. The Mode
          B preamble carries the explicit READ-ONLY `git clone` instruction
          + `read_file` pointers to both root docs.

        When `alias` is supplied, the alias + the JulesSession node are
        recorded in the bi-temporal graph (the registry IS the graph, per
        CORE.md:38-45)."""
        s = self._backend().create(prompt=prompt, source=source,
                                   starting_branch=starting_branch, title=title,
                                   require_plan_approval=require_plan_approval,
                                   automation_mode=automation_mode,
                                   protocol_preset=protocol_preset)
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
            # Spec 022 — surface the dispatch immediately on the engine monitor
            # so the user sees it in Claude Code without waiting for the first
            # watcher transition (seconds-to-minutes later).
            self.ctx.emit_monitor(
                source="jules", kind="dispatched",
                message=f"sid={sid} state={s.get('state', 'QUEUED')} title={title}",
            )
        return {
            "status": s.get("state", "submitted"),
            "session": sid,
            "url": s.get("url"),
            "alias": alias,
            "artefact": {"kind": "jules-session", "session": sid or "", "url": s.get("url") or ""},
        }

    @verb(role="transform")
    def status(self, session: str) -> dict:
        """Read a session's full state from the backend.

        Inputs: session (sid).
        Returns: the backend's full state dict (state, url, plan, outputs, …).
        chain_next: ``jules.verify(state=, branch=)`` to confirm push.

        The trimmed `{state, url}` shape was dropping 5 fields the watcher +
        recovery flow need (R2 audit fix; spec 012 Phase 5).
        """
        return self._backend().get(session)

    @verb(role="transform")
    def list(self, page_size: int = 20, page_token: str = "") -> dict:
        """Enumerate sessions (trimmed to id/state/title/url; one page — walk via token).

        Inputs: page_size (int), page_token (str — empty = first page).
        Returns: ``{sessions: [{id, state, title, url}], next_page_token}``.
        chain_next: re-call with returned ``next_page_token`` to walk older pages.
        """
        return self._backend().list(page_size, page_token)

    @verb(role="transform")
    def activities(self, session: str, page_size: int = 10, only_kinds: str = "",
                   page_token: str = "") -> dict:
        """A session's activity stream, trimmed to summaries (the costliest Jules read).

        Inputs: session (sid), page_size (int), only_kinds (comma-separated kinds),
                page_token (str — empty for newest page).
        Returns: ``{activities: [{kind, summary, ts}], next_page_token}``.
        chain_next: walk pages via ``next_page_token``; ``jules.plan`` /
                    ``jules.patch`` for typed slices.

        Without ``page_token`` older `agentMessaged` / failure details become
        unreachable (Codex review ccb8f03 / jules.py:139).
        """
        return self._backend().activities(session, page_size, only_kinds, page_token)

    @verb(role="transform")
    def plan(self, session: str, max_pages: int = 5) -> dict:
        """The latest generated plan — show it before approve_plan (no PR exists yet).

        Inputs: session (sid), max_pages (int — walk back this many pages).
        Returns: ``{plan: <markdown>, generated_at}`` or ``{error}`` if not found.
        chain_next: review then ``jules.approve_plan(session=)``.
        """
        return self._backend().plan(session, max_pages)

    @verb(role="effect")
    def approve_plan(self, session: str) -> dict:
        """Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out.

        Inputs: session (sid).
        Returns: backend response (typically ``{state: WORKING}`` after).
        chain_next: poll ``jules.status(session=)`` until COMPLETED / FAILED.
        """
        return self._backend().approve_plan(session)

    @verb(role="effect")
    def message(self, session: str, prompt: str) -> dict:
        """Send a message into a session (feedback / plan-revision / nudge to push).

        Inputs: session (sid), prompt (str — the message body).
        Returns: backend response (typically ``{ok}`` on accept).
        chain_next: poll ``jules.status(session=)`` — resumption is racy.

        Input only, NOT a control plane. Never use to revive a FAILED session
        or to cancel one.
        """
        return self._backend().message(session, prompt)

    @verb(role="transform")
    def stop(self, session: str) -> dict:
        """UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop.

        Inputs: session (sid).
        Returns: ``{error: 'unsupported', session, message}``.
        chain_next: ``jules.message(session=, prompt='please stop')`` or wait
                    for terminal state (COMPLETED / FAILED).
        """
        return {
            "error": "unsupported",
            "session": session,
            "message": ("The Jules v1alpha API has no session cancellation. Use `message` "
                        "to ask the agent to stop and leave changes uncommitted, or wait "
                        "for COMPLETED/FAILED."),
        }

    @verb(role="transform", inject=["vcs"])
    def verify(self, vcs, state: str, branch: str, remote: str = "origin") -> dict:
        """COMPLETED != done — verifies the branch landed on origin.

        Inputs: state (caller-reported session state), branch (str),
                remote (str, default 'origin').
        Returns: ``{done, state, branch_on_remote, sha, error?}``.
        chain_next: when ``done=True``, open a PR; otherwise ``jules.recover``.

        Derives ``branch_on_remote`` INDEPENDENTLY via the injected ``vcs``
        boundary (``git ls-remote``). Fail-closed: any lookup error →
        ``done=False`` (Spec 006 F3 / Spec 012 Phase 5).
        """
        if not branch:
            return {"done": False, "state": state, "branch_on_remote": False,
                    "error": "branch is required"}
        chk = (vcs or GitClient()).remote_exists(branch=branch, remote=remote)
        if not chk.get("ok"):
            return {"done": False, "state": state, "branch_on_remote": False,
                    "error": f"remote check failed: {chk.get('detail','')}"}
        branch_on_remote = bool(chk.get("exists"))
        is_completed = str(state).lower() == "completed"
        done = is_completed and branch_on_remote
        # Spec 022 — make COMPLETED≠done silent-fail detection visible on the
        # monitor channel without the user reading the verify return value. Gate
        # on COMPLETED (same condition as `done`): an in-progress session whose
        # branch isn't pushed yet is NORMAL, not a silent fail (PR #20 review).
        if is_completed and not branch_on_remote:
            self.ctx.emit_monitor(
                source="jules", kind="silent_fail_detected",
                message=f"branch={branch!r} NOT on {remote} (state={state}) — likely silent fail",
            )
        return {"done": done, "state": state, "branch_on_remote": branch_on_remote,
                "sha": chk.get("sha", "")}

    # === Spec 012 Phase 3 — orbital read/admin verbs ==========================

    @verb(role="transform")
    def resolve_source(self, owner: str, repo: str) -> dict:
        """Resolve `owner/repo` to the opaque `sources/<id>` the API expects.

        Inputs: owner (str), repo (str).
        Returns: ``{source_id, owner, repo}`` or ``{error}`` on miss.
        chain_next: pass ``source_id`` (or ``owner/repo``) to ``jules.dispatch``.

        The composition is undocumented; must list-and-match. Read-only.
        """
        return self._backend().resolve_source(owner, repo)

    @verb(role="transform")
    def status_all(self, page_size: int = 100, max_pages: int = 20) -> dict:
        """Paginated, grouped-by-state listing of every session on the account.

        Inputs: page_size (int), max_pages (int).
        Returns: ``{by_state, totals, total, truncated}``.
        chain_next: ``jules.approve_awaiting`` for AWAITING_PLAN_APPROVAL group.

        Operational hygiene (lesson-15 §3); the watcher uses it to seed the
        registry.
        """
        return self._backend().status_all(page_size, max_pages)

    @verb(role="effect")
    def approve_awaiting(self, limit: int = 0) -> dict:
        """Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`).

        Inputs: limit (int — cap; 0 = all).
        Returns: ``{approved, skipped}``.
        chain_next: poll ``jules.status_all`` until all approved sessions
                    transition to WORKING / COMPLETED.

        The one state with a timeout/discard window; don't let it sit
        (lesson-15 §6).
        """
        return self._backend().approve_awaiting(limit)

    @verb(role="transform")
    def quota(self, daily_limit: int = 0) -> dict:
        """Count sessions created today (UTC).

        Inputs: daily_limit (int — caller-supplied budget; 0 = no headroom calc).
        Returns: ``{used, daily_limit, headroom}`` (headroom only when
                 ``daily_limit > 0``).
        chain_next: gate further ``jules.dispatch`` calls on ``headroom > 0``.

        The API has no quota surface; this is operational hygiene
        (lesson-15 §6).
        """
        return self._backend().quota(daily_limit)

    @verb(role="transform")
    def patch(self, session: str) -> dict:
        """Per-output stats (``files``, ``lines``, ``bytes``) from the session's outputs — NO body.

        Inputs: session (sid).
        Returns: ``{outputs: [{index, files, lines, bytes}]}``.
        chain_next: ``jules.patch_body(session=, output_index=)`` for the
                    actual unidiff bytes; ``jules.apply_patch`` for recovery.

        Used by the watcher to classify silent-fail variants (empty patch vs
        missing push). Body retrieval is the explicit ``patch_body`` verb.
        """
        return self._backend().patch(session)

    @verb(role="transform")
    def patch_body(self, session: str, output_index: int = 0, max_bytes: int = 4096) -> dict:
        """Explicit, capped unidiff retrieval for one of the session's outputs.

        Inputs: session (sid), output_index (int, default 0),
                max_bytes (int — default 4096; capped slice).
        Returns: ``{unidiff, truncated, original_bytes}`` or ``{error}`` on
                 out-of-range index.
        chain_next: ``jules.apply_patch(session=)`` for the recovery plan.

        Default cap 4 KB so a careless call can't blow the agent's context.
        """
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
        """Read or upsert a stable alias for a Jules sid.

        Inputs: name (alias slug), session (sid — empty = look up).
        Returns: ``{name, session}`` on hit; ``{error}`` on lookup miss.
        chain_next: ``jules.status(session=)`` once resolved.

        Stored as a ``JulesAlias`` node in the bi-temporal graph (no
        parallel sessions.json per the canon CORE.md:38-45).
        """
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

        Inputs: text (the dispatch prompt body), must_name (comma-separated
                override; empty falls back to the canonical list).
        Returns: ``{ok, missing, extras}``.
        chain_next: edit the prompt to add ``missing`` names; re-lint.

        Symmetric with ``plugin.lint_skill``: a pure predicate, no side
        effects. Consumed by the ``jules-protocol-preamble`` skill Phase 3
        (``name-canonical-tools``).
        """
        from .preambles import lint_must_name
        names = [s.strip() for s in must_name.split(",") if s.strip()] if must_name else None
        return lint_must_name(text, must_name=names)

    @verb(role="transform")
    def detect_mode(self, source: str) -> dict:
        """Mode A (dogfood) vs Mode B (delegate) — pure decision on dispatch source.

        Inputs: source (str — owner/repo of the dispatch target).
        Returns: ``{mode: dogfood|delegate, self_source, reason}``.
        chain_next: pass ``mode`` to ``_jules_preambles.assemble(...)``.

        Mode A when ``source == DISPATCH_SELF_SOURCE`` (the agency repo
        itself); Mode B for any other source. Bound by Phase 1 of the
        ``jules-protocol-preamble`` skill.
        """
        from .preambles import DISPATCH_SELF_SOURCE
        if source == DISPATCH_SELF_SOURCE:
            return {"mode": "dogfood", "self_source": DISPATCH_SELF_SOURCE,
                    "reason": "source matches DISPATCH_SELF_SOURCE; AGENTS.md inherited via lexical scoping"}
        return {"mode": "delegate", "self_source": DISPATCH_SELF_SOURCE,
                "reason": "source differs from DISPATCH_SELF_SOURCE; preamble carries the READ-ONLY clone block"}

    @verb(role="transform")
    def review_comment(self, body: str) -> dict:
        """Compose an @jules PR review-comment with the mandatory handshake tail.

        Inputs: body (str — your review comment).
        Returns: ``{text, tail_appended}``. ``text`` is what the caller passes
                 to GitHub MCP ``add_issue_comment``; ``tail_appended=False``
                 means the body already carried a compliant tail.
        chain_next: post ``text`` via the GitHub MCP comment tool.

        The tail instructs Jules to ``reply_to_pr_comments(...)`` after
        pushing (AGENCY_PROTOCOL.md §9). Idempotent.
        """
        from .preambles import REVIEW_COMMENT_TAIL, review_comment as _rc
        already = REVIEW_COMMENT_TAIL.strip() in body
        return {"text": _rc(body), "tail_appended": not already}

    @verb(role="transform")
    def watch(self, session: str = "", for_intent: str = "", timeout: int = 30) -> dict:
        """Await the next `WatchEvent` for a session or intent.

        Inputs: session (sid — looks up the watching intent), for_intent (intent_id —
                explicit override), timeout (int — seconds, capped at 25).
        Returns: ``{action, session, state, instruction, evidence, _for_intent}``
                 on a real event; ``{action: 'noop', instruction: 'Working.',
                 evidence: {}, _for_intent}`` on heartbeat.
        chain_next: dispatch action-specific verb (e.g. ``jules.approve_plan``,
                    ``jules.recover``, ``jules.verify``).

        Caller supplies EITHER ``session`` (sid; resolves the watching intent
        via the `JulesSession SERVES Intent` edge) OR ``for_intent`` directly.
        ``for_intent`` is named distinctly from the engine's auto-injected
        ``intent_id`` (which always points to the *calling* intent).

        Returns the next event from the per-intent queue, OR a heartbeat noop
        after ``min(timeout, 25)`` seconds — so client stdio stays alive even
        when no transition fires (Spec 012 Refinement Notes must-fix #5).

        Returns ``{action, session, state, instruction, evidence}`` for a real
        event, or ``{action: "noop", instruction: "Working.", evidence: {}}``
        for the heartbeat. The watcher's poll loop ALSO emits noop heartbeats
        every 20s; this verb's heartbeat is the client-facing fallback if the
        queue is otherwise empty.

        Sync wrapper around the async queue: drains any pending event via
        ``get_nowait``, else polls 10×/sec for up to ``min(timeout, 25)``s.

        **Intent semantics** — the *calling intent* (auto-injected as
        ``intent_id``) wraps THIS verb call in code-mode; the *watching
        intent* is the one that originated the dispatch (recorded on the
        ``JulesSession``'s ``SERVES`` edge). They are often the same (one
        orchestrator dispatches + watches), but on cross-session resume —
        a fresh intent later asking ``jules.watch(session=sid)`` — they
        differ. This verb resolves through ``JulesSession SERVES Intent``
        to pick the right queue; ``for_intent`` lets the caller override
        the resolution explicitly. Returns the resolved intent on the
        response under ``_for_intent`` so the caller knows whose queue
        was read.
        """
        import time as _time
        if not session and not for_intent:
            return {"action": "error", "instruction": "must supply session or for_intent"}

        # Resolve watching intent from JulesSession SERVES Intent if needed.
        # The labeled intent id (e.g. "intent:abc123") lives in node properties,
        # NOT the graph's internal numeric id at row["i"]["id"].
        iid = for_intent
        if not iid and session:
            mem = self.ctx.memory
            rows = mem.g.query(
                "MATCH (js:JulesSession)-[:SERVES]->(i:Intent) "
                "WHERE js.sid = $sid RETURN i",
                {"sid": session},
            )
            if rows:
                iid = rows[0]["i"]["properties"].get("id", "")
            if not iid:
                iid = self.ctx.intent_id   # fall back to the calling intent

        from .watch import INSTRUCTIONS
        engine = self.ctx.engine
        watcher = getattr(engine, "_jules_watcher", None) if engine else None
        if watcher is None:
            return {"action": "noop", "instruction": INSTRUCTIONS["noop"],
                    "evidence": {"reason": "watcher not started"}, "_for_intent": iid}

        def _emit(ev: dict) -> dict:
            # Return a NEW dict — never mutate the queued event in place
            # (callers may hold a reference; mutation is a leaky abstraction).
            return {**ev, "_for_intent": iid}

        q = watcher._get_queue(iid)
        # Drain pending event first (cheap path).
        try:
            return _emit(q.get_nowait())
        except Exception:
            pass

        # Sync poll with cap at 25s — leaves 5s of slack for stdio liveness.
        cap = min(max(timeout, 0), 25)
        deadline = _time.time() + cap
        while _time.time() < deadline:
            try:
                return _emit(q.get_nowait())
            except Exception:
                _time.sleep(0.1)
        return {"action": "noop", "instruction": INSTRUCTIONS["noop"],
                "evidence": {}, "_for_intent": iid}

    @verb(role="effect")
    def recover(self, session: str, owner: str = "", repo: str = "",
                branch: str = "", base: str = "main") -> dict:
        """Promote a session to the watcher's recovery-in-flight tracker.

        Inputs: session (sid), owner/repo/branch (optional plumb-throughs),
                base (str — default 'main').
        Returns: ``{status: 'probing', session, attempts_planned: 3}`` IMMEDIATELY;
                 outcome arrives later as a ``verify_pr`` / ``recover_apply_plan``
                 WatchEvent on the per-intent queue.
        chain_next: ``jules.watch(session=)`` to await the recovery outcome.

        The probe-wait-recheck cycle (~5 min × 3 attempts per
        AGENCY_PROTOCOL §5) lives in the watcher's poll loop. Missing
        owner/repo/branch are derived from ``sourceContext.source`` at
        probe-exhaustion time.
        """
        import time as _time
        engine = self.ctx.engine
        watcher = getattr(engine, "_jules_watcher", None) if engine else None
        if watcher is None:
            return {"status": "error",
                    "reason": "watcher not started; call jules.recover via the engine that owns the lifespan task"}
        watcher.recovery_in_flight[session] = {
            "attempt": 0,
            "next_probe_at": _time.time() + 5 * 60,
            "started_at": _time.time(),
            "intent_id": self.ctx.intent_id,
            "branch": branch,
            "recover_branch": f"recover-{session}",
            "base": base,
            "owner": owner,
            "repo": repo,
        }
        # Spec 022 — surface recovery entry on the engine monitor channel.
        self.ctx.emit_monitor(
            source="jules", kind="recovery_started",
            message=f"sid={session} entering recovery (probe budget: 3 × 5min)",
        )
        return {"status": "probing", "session": session, "attempts_planned": 3}

    @verb(role="transform")
    def apply_patch(self, session: str, branch: str = "", base: str = "main",
                    owner: str = "", repo: str = "") -> dict:
        """Compute a recovery plan for a session's patch (verb mirror of `recover_apply_plan`).

        Inputs: session (sid), branch (optional — defaults ``recover-<session>``),
                base (str — default 'main'), owner/repo (optional).
        Returns: ordered list of ``{tool, args}`` ops the agent executes via
                 GitHub MCP. NOT executed by this verb (planning vs. execution
                 boundary; Spec 012 REVIEW must-fix #1).
        chain_next: caller executes the ops via GitHub MCP in order.

        Falls back to ``sourceContext.source`` for owner/repo when omitted.
        """
        from .api import jules_get_full
        from . import patch as _jules_patch
        sess = jules_get_full(session)
        outputs = sess.get("outputs", [])
        if not owner or not repo:
            src = sess.get("sourceContext", {}).get("source", "")
            short = src.rsplit("/", 1)[-1]
            if "-" in short:
                owner = owner or short.partition("-")[0]
                repo = repo or short.partition("-")[2]
            elif "/" in src:
                owner = owner or src.partition("/")[0]
                repo = repo or src.partition("/")[2]
        recover_branch = branch or f"recover-{session}"
        plan = _jules_patch.build_recovery_plan(
            outputs, recover_branch, base,
            owner or "unknown", repo or "unknown", session,
        )
        return plan
