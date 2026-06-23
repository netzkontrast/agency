"""Jules-specific Lifecycle skill templates (Spec 013 Phase 5+).

A skill IS a capability (CORE.md:47-62) — Lifecycle templates of atomic
gated step-graphs. These skills are registered on
``JulesCapability.ontology.skills`` and walked via ``agency.skill.SkillRun``.

This module is consumed by ``jules.py`` at module load (the
``OntologyExtension(skills=…)`` argument) and is otherwise pure data.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Phase 5 — jules-protocol-preamble
# ---------------------------------------------------------------------------
# Walked ONCE per dispatch. The doctrine docs at the repo root
# (AGENTS.md + AGENCY_PROTOCOL.md) carry the invariants once per snapshot;
# this skill compresses the per-dispatch boilerplate from ~700 tokens to
# ~120 tokens by binding 3 of its 5 phases to real verbs.
#
# Phase 1 (`detect-mode`) is invoke-bound to `jules.detect_mode`: produces
# `{mode, self_source, reason}` where `mode ∈ {"dogfood", "delegate"}`.
# Phase 2 (`verify-remote-state`) is invoke-bound to `jules.verify`: the
# silent-fail guard before dispatch.
# Phase 3 (`name-canonical-tools`) is invoke-bound to `jules.lint_prompt`:
# refuses to advance unless the assembled prompt names every canonical
# tool symbol (see _jules_preambles._MUST_NAME_TOOLS).
# Phase 4 (`set-scope`) is a document phase: caller declares the scope
# allow-list + the Mode-B read-only assertion (`agency_clone_ro_in_delegate`).
# Phase 5 (`dispatched`) is a HARD GATE elicit (CORE.md:56-60): walker
# pauses at `input-required` until a `session_id` is supplied + confirmed.
JULES_PROTOCOL_PREAMBLE_SKILL: dict = {
    "name": "jules-protocol-preamble",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "detect-mode",
         "produces": ["mode_decision"],
         "invoke": {"capability": "jules", "verb": "detect_mode"},
         "inputs": ["source"],
         "goal": "Detect dogfood vs delegate mode.",
         "instructions": "jules.detect_mode resolves whether this dispatch is dogfood "
                         "(self-source, Mode A) or delegate (another repo, Mode B). The "
                         "mode drives the preamble and the read-only clone assertion.",
         "freedom": "low"},
        {"index": 2, "name": "verify-remote-state",
         "produces": ["verify_result"],
         "invoke": {"capability": "jules", "verb": "verify"},
         "inputs": ["state", "branch", "remote"],
         "goal": "Guard against a silent fail before dispatch.",
         "instructions": "jules.verify checks the remote branch state — the silent-fail "
                         "guard (COMPLETED != pushed). Don't dispatch onto a dirty or "
                         "unexpected remote.",
         "freedom": "low"},
        {"index": 3, "name": "name-canonical-tools",
         "produces": ["lint_result"],
         "invoke": {"capability": "jules", "verb": "lint_prompt"},
         "inputs": ["text", "must_name"],
         "goal": "Lint that the prompt names every canonical tool.",
         "instructions": "jules.lint_prompt refuses to advance unless the assembled prompt "
                         "NAMES every canonical tool symbol (read_file, …). A prompt that "
                         "doesn't name its tools leaves the remote agent guessing.",
         "freedom": "low"},
        {"index": 4, "name": "set-scope",
         "produces": ["affects_paths", "no_create_outside",
                      "agency_clone_ro_in_delegate"],
         "goal": "Declare the scope allow-list + read-only assertion.",
         "instructions": "Declare the affects-paths allow-list, the no-create-outside "
                         "boundary, and (Mode B) the read-only agency-clone assertion. "
                         "Scope is the safety rail on a remote agent.",
         "freedom": "medium"},
        {"index": 5, "name": "dispatched",
         "produces": ["session_id"], "gate": "hard",
         "goal": "Confirm the dispatch landed with a session id.",
         "instructions": "The walker pauses until a session_id is supplied + confirmed. "
                         "Confirm this gate only once the Jules session actually exists.",
         "freedom": "low"},
    ],
}


# ---------------------------------------------------------------------------
# Phase 6 — jules-tool-discipline (collapsed)
# ---------------------------------------------------------------------------
# Phase C REVIEW must-fix #5: the original 5-phase shape was tautological
# ("was this string in the prompt?" × 5 isn't a skill). The cleaner answer:
# one advisory phase that invokes the real predicate. Reusable from inside
# `jules-protocol-preamble` Phase 3 (same `invoke` binding); also walked
# standalone when a caller wants to lint a draft prompt without committing
# to a dispatch.
JULES_TOOL_DISCIPLINE_SKILL: dict = {
    "name": "jules-tool-discipline",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "apply-tool-discipline",
         "produces": ["lint_result"],
         "invoke": {"capability": "jules", "verb": "lint_prompt"},
         "inputs": ["text", "must_name"],
         "goal": "Lint that a draft prompt names its tools.",
         "instructions": "jules.lint_prompt over a draft prompt — the reusable predicate "
                         "the preamble's phase 3 also invokes. Refuses unless every "
                         "canonical tool symbol is named; walk it standalone to lint a "
                         "draft before committing to a dispatch.",
         "freedom": "low"},
    ],
}


# ---------------------------------------------------------------------------
# Phase 7 — jules-recovery-when-stuck
# ---------------------------------------------------------------------------
# Walked by the watcher's recover flow (Spec 012 §5; AGENCY_PROTOCOL.md §5).
# 4 phases, 1 hard gate at the end. The phases mirror the three silent-fail
# routing options: probe → check for reply → fall back to patch-extract.
#
# Phase 1 (`classify-state`) binds to `jules.status`: returns the session
# resource so downstream phases can branch on state + has_outputs.
# Phase 2 (`probe-once`) binds to `jules.message`: nudges the agent to push
# or reply EMPTY (the canonical recovery probe; AGENCY_PROTOCOL.md §5).
# Phase 3 (`patch-or-empty`) binds to `jules.patch`: extracts the session's
# patch outputs for the recovery plan (returns files/lines/bytes counts).
# Phase 4 (`recovered`) is the HARD GATE: caller supplies pr_url (or a
# sentinel "EMPTY" when no recovery was needed) + confirms.
JULES_RECOVERY_WHEN_STUCK_SKILL: dict = {
    "name": "jules-recovery-when-stuck",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "classify-state",
         "produces": ["status"],
         "invoke": {"capability": "jules", "verb": "status"},
         "inputs": ["session"],
         "goal": "Classify the stuck session's state.",
         "instructions": "jules.status returns the session resource so you can branch on "
                         "state + has_outputs — is it silently failed, awaiting approval, "
                         "or genuinely still working?",
         "freedom": "low"},
        {"index": 2, "name": "probe-once",
         "produces": ["probe"],
         "invoke": {"capability": "jules", "verb": "message"},
         "inputs": ["session", "prompt"],
         "goal": "Probe the agent ONCE to push or reply empty.",
         "instructions": "jules.message nudges the agent to push its work or reply EMPTY — "
                         "the canonical recovery probe. Probe once; don't spam a stuck "
                         "session.",
         "freedom": "low"},
        {"index": 3, "name": "patch-or-empty",
         "produces": ["patch"],
         "invoke": {"capability": "jules", "verb": "patch"},
         "inputs": ["session"],
         "goal": "Extract the session's patch outputs.",
         "instructions": "jules.patch extracts the patch outputs (files/lines/bytes) for "
                         "the recovery plan — the fallback when the agent won't push.",
         "freedom": "low"},
        {"index": 4, "name": "recovered",
         "produces": ["pr_url"], "gate": "hard",
         "goal": "Confirm recovery — a PR url or EMPTY.",
         "instructions": "Supply the pr_url (or the sentinel EMPTY when no recovery was "
                         "needed) + confirm. Confirm only when the session is genuinely "
                         "recovered or definitively empty.",
         "freedom": "low"},
    ],
}


# ---------------------------------------------------------------------------
# Phase 8 — jules-pr-review-cycle
# ---------------------------------------------------------------------------
# 3 advisory phases composing the @jules review-comment flow. The
# `draft-replies` phase binds to `jules.review_comment` so every drafted
# reply ships with the mandatory AGENCY_PROTOCOL.md §9 handshake tail
# (`reply_to_pr_comments(...)`). The `read-comments` and `reply-on-github`
# phases are document phases — the caller fetches via GitHub MCP, drafts,
# then posts the replies, since GitHub MCP is the orchestrator's tool,
# not a capability the engine wires directly.
JULES_PR_REVIEW_CYCLE_SKILL: dict = {
    "name": "jules-pr-review-cycle",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "read-comments",
         "produces": ["comments"],
         "goal": "Read the PR review comments.",
         "instructions": "Fetch the review comments via GitHub MCP and read them for what "
                         "they actually ask — understand before replying.",
         "freedom": "medium"},
        {"index": 2, "name": "draft-replies",
         "produces": ["draft_reply"],
         "invoke": {"capability": "jules", "verb": "review_comment"},
         "inputs": ["body"],
         "goal": "Draft replies carrying the protocol handshake.",
         "instructions": "jules.review_comment drafts each reply WITH the mandatory "
                         "protocol handshake tail. Address the comment with technical "
                         "substance, not performative agreement.",
         "freedom": "medium"},
        {"index": 3, "name": "reply-on-github",
         "produces": ["posted"],
         "goal": "Post the replies on GitHub.",
         "instructions": "Post the drafted replies via GitHub MCP. Be frugal — only reply "
                         "where a reply genuinely advances the review.",
         "freedom": "low"},
    ],
}


# ---------------------------------------------------------------------------
# Phase 9 — jules-fanout
# ---------------------------------------------------------------------------
# Composes the canonical pattern from develop.review: a `dispatch` phase
# invokes `delegate.fan_out(driver="jules")` to spawn N child Lifecycles,
# each driving a Jules session. The HARD GATE at `join` pauses until the
# caller confirms every child resolved to an outcome (this skill does not
# auto-join; it expects the orchestrator's confirmation that the fan-out
# completed). Quota is the existing `delegate` arg.
JULES_FANOUT_SKILL: dict = {
    "name": "jules-fanout",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "plan-batch",
         "produces": ["items"],
         "goal": "Plan the batch of independent items.",
         "instructions": "Enumerate the independent items to fan out across Jules "
                         "sessions — each must be self-contained (no shared state, no "
                         "ordering dependency).",
         "freedom": "medium"},
        {"index": 2, "name": "fan-out",
         "produces": ["fanout_result"],
         "invoke": {"capability": "delegate", "verb": "fan_out"},
         "inputs": ["driver", "driver_verb", "items", "quota"],
         "goal": "Fan out a Jules session per item.",
         "instructions": "delegate.fan_out(driver='jules') spawns N child Lifecycles, each "
                         "driving a Jules session, bounded by the quota arg.",
         "freedom": "medium"},
        {"index": 3, "name": "join",
         "produces": ["child_outcomes"], "gate": "hard",
         "goal": "Confirm every child resolved.",
         "instructions": "This skill does NOT auto-join — it pauses until you confirm "
                         "every child session resolved to an outcome. Confirm only when "
                         "the fan-out genuinely completed.",
         "freedom": "low"},
    ],
}


# ---------------------------------------------------------------------------
# Phase 10 — jules-self-improvement
# ---------------------------------------------------------------------------
# The dogfood loop made first-class. Both phases bind to real verbs so
# the walk EXECUTES:
# - Phase 1 (`collect-dogfood`) binds to `dogfood.collect(plan_dir)`:
#   walks Plan/**/DOGFOOD-NOTES.md, returns observations + a flat texts
#   list ready for bulk ingestion.
# - Phase 2 (`fold-into-graph`) binds to `reflect.batch_note(scope, texts)`:
#   one Reflection node per text in a single invocation, no longer
#   capped at one-observation-per-walk.
#
# The observation -> spec-amendment step (taking a Reflection and
# proposing a delta to a DESIGN.md / spec.md) is genuinely harder
# (LLM-shaped) and deferred to a future spec. v1 closes the durable-
# memory half of the loop; the surface-to-orchestrator half is a
# follow-on.
JULES_SELF_IMPROVEMENT_SKILL: dict = {
    "name": "jules-self-improvement",
    "kind": "discipline",
    "phases": [
        {"index": 1, "name": "collect-dogfood",
         "produces": ["collection"],
         "invoke": {"capability": "dogfood", "verb": "collect"},
         "inputs": ["plan_dir"],
         "goal": "Collect the dogfood observations.",
         "instructions": "dogfood.collect walks Plan/**/DOGFOOD-NOTES.md and returns the "
                         "observations + a flat texts list ready for bulk ingestion.",
         "freedom": "low"},
        {"index": 2, "name": "fold-into-graph",
         "produces": ["reflections"],
         "invoke": {"capability": "reflect", "verb": "batch_note"},
         "inputs": ["scope", "texts"],
         "goal": "Fold the observations into the graph as Reflections.",
         "instructions": "reflect.batch_note writes one Reflection node per text in a "
                         "single invocation — the durable-memory half of the dogfood loop.",
         "freedom": "low"},
    ],
}


JULES_SKILLS: dict[str, dict] = {
    "jules-protocol-preamble":   JULES_PROTOCOL_PREAMBLE_SKILL,
    "jules-tool-discipline":     JULES_TOOL_DISCIPLINE_SKILL,
    "jules-recovery-when-stuck": JULES_RECOVERY_WHEN_STUCK_SKILL,
    "jules-pr-review-cycle":     JULES_PR_REVIEW_CYCLE_SKILL,
    "jules-fanout":              JULES_FANOUT_SKILL,
    "jules-self-improvement":    JULES_SELF_IMPROVEMENT_SKILL,
}
