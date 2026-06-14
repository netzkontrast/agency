---
capability: jules
pillar: lifecycle
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# jules — Jules drives remote agent sessions end-to-end: dispatch, plan approval, follow-ups, and verification that a session reporting completed actually pushed a branch (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 22)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `jules.activities` | transform | **session** · page_size · only_kinds · page_token | A session's activity stream, trimmed to summaries (the costliest Jules read). |
| `jules.alias` | act | **name** · session | Read or upsert a stable alias for a Jules sid. |
| `jules.apply_patch` | transform | **session** · branch · base · owner · repo | Compute a recovery plan for a session's patch (verb mirror of `recover_apply_plan`). |
| `jules.approve_awaiting` | effect | limit | Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`). |
| `jules.approve_plan` | effect | **session** | Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out. |
| `jules.detect_mode` | transform | **source** | Mode A (dogfood) vs Mode B (delegate) — pure decision on dispatch source. |
| `jules.dispatch` | effect | **source** · **starting_branch** · **prompt** · title · require_plan_approval · alias · automation_mode · protocol_preset | Spawn a remote Jules session (external effect). Returns id/url/state. |
| `jules.lint_prompt` | transform | **text** · must_name | Lint a dispatch prompt against the canonical must-name tool list. |
| `jules.list` | transform | page_size · page_token | Enumerate sessions (trimmed to id/state/title/url; one page — walk via token). |
| `jules.message` | effect | **session** · **prompt** | Send a message into a session (feedback / plan-revision / nudge to push). |
| `jules.patch` | transform | **session** | Per-output stats (``files``, ``lines``, ``bytes``) from the session's outputs — NO body. |
| `jules.patch_body` | transform | **session** · output_index · max_bytes | Explicit, capped unidiff retrieval for one of the session's outputs. |
| `jules.plan` | transform | **session** · max_pages | The latest generated plan — show it before approve_plan (no PR exists yet). |
| `jules.quota` | transform | daily_limit | Count sessions created today (UTC). |
| `jules.recover` | effect | **session** · owner · repo · branch · base | Promote a session to the watcher's recovery-in-flight tracker. |
| `jules.resolve_source` | transform | **owner** · **repo** | Resolve `owner/repo` to the opaque `sources/<id>` the API expects. |
| `jules.review_comment` | transform | **body** | Compose an @jules PR review-comment with the mandatory handshake tail. |
| `jules.status` | transform | **session** | Read a session's full state from the backend. |
| `jules.status_all` | transform | page_size · max_pages | Paginated, grouped-by-state listing of every session on the account. |
| `jules.stop` | transform | **session** | UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop. |
| `jules.verify` | transform | **vcs** · **state** · **branch** · remote | COMPLETED != done — verifies the branch landed on origin. |
| `jules.watch` | transform | session · for_intent · timeout | Await the next `WatchEvent` for a session or intent. |

## Ontology (generated)

**Nodes:** `JulesSession`(sid) · `JulesAlias`(name, sid) · `JulesWatchEvent`(sid, action) · `JulesPatch`(sid, files, lines, bytes)
**Edges:** `ALIAS_OF` · `OBSERVED_OF` · `RECOVERED_BY`
**Enums:** `('JulesSession', 'state')` ∈ {AWAITING_PLAN_APPROVAL, AWAITING_USER_FEEDBACK, CANCELLED, COMPLETED, FAILED, IN_PROGRESS, PAUSED, PLANNING, QUEUED, STATE_UNSPECIFIED} · `('JulesWatchEvent', 'action')` ∈ {answer_agent_question, dispatch_fresh, inspect_and_resume, noop, recover_apply_plan, recover_silent_fail, review_and_approve_plan, terminal, verify_pr}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/jules -->
