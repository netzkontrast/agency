---
name: jules
description: "Use when fanning a coding task out to a remote Jules agent session and driving it to a verified PR — dispatching, sending follow-ups, approving plans, and recovering completed-but-unpushed work."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# jules capability

Jules drives remote agent sessions end-to-end: dispatch, plan approval, follow-ups, and verification that a session reporting completed actually pushed a branch.

## When to use

- A coding task suited to a remote agent session
- A Jules session reporting completed but no branch on origin
- A remote plan awaiting approval before it proceeds

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `activities` | transform | A session's activity stream. | [details](references/activities.md) |
| `alias` | act | Read or upsert a stable alias for a Jules sid. | [details](references/alias.md) |
| `apply_patch` | transform | Compute a recovery plan for a session's patch (verb mirror of `recover_apply_plan`). | [details](references/apply_patch.md) |
| `approve_awaiting` | effect | Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`). | [details](references/approve_awaiting.md) |
| `approve_plan` | effect | Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out. | [details](references/approve_plan.md) |
| `detect_mode` | transform | Mode A (dogfood) vs Mode B (delegate) — pure decision on dispatch source. | [details](references/detect_mode.md) |
| `dispatch` | effect | Spawn a remote Jules session (external effect). | [details](references/dispatch.md) |
| `lint_prompt` | transform | Lint a dispatch prompt against the canonical must-name tool list. | [details](references/lint_prompt.md) |
| `list` | transform | Enumerate sessions (trimmed to id/state/title/url; one page — walk via token). | [details](references/list.md) |
| `message` | effect | Send a message into a session (feedback / plan-revision / nudge to push). | [details](references/message.md) |
| `patch` | transform | Per-output stats (``files``, ``lines``, ``bytes``) from the session's outputs — NO body. | [details](references/patch.md) |
| `patch_body` | transform | Explicit, capped unidiff retrieval for one of the session's outputs. | [details](references/patch_body.md) |
| `plan` | transform | The latest generated plan — show it before approve_plan (no PR exists yet). | [details](references/plan.md) |
| `quota` | transform | Count sessions created today (UTC). | [details](references/quota.md) |
| `recover` | effect | Promote a session to the watcher's recovery-in-flight tracker. | [details](references/recover.md) |
| `resolve_source` | transform | Resolve `owner/repo` to the opaque `sources/<id>` the API expects. | [details](references/resolve_source.md) |
| `review_comment` | transform | Compose an @jules PR review-comment with the mandatory handshake tail. | [details](references/review_comment.md) |
| `status` | transform | Read a session's full state from the backend. | [details](references/status.md) |
| `status_all` | transform | Paginated, grouped-by-state listing of every session on the account. | [details](references/status_all.md) |
| `stop` | transform | UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop. | [details](references/stop.md) |
| `verify` | transform | COMPLETED != done — verifies the branch landed on origin. | [details](references/verify.md) |
| `watch` | transform | Await the next `WatchEvent` for a session or intent. | [details](references/watch.md) |

## Example

```bash
await call_tool('capability_jules_activities', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Trusting completed as done → confirm with capability_jules_verify (state and branch on origin)
- Dispatching without a prompt review → run capability_jules_lint_prompt first

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`jules-fanout`** (discipline): plan-batch → fan-out → join
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-fanout', 'inputs': {}, 'intent_id': '…'})`
- **`jules-pr-review-cycle`** (discipline): read-comments → draft-replies → reply-on-github
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-pr-review-cycle', 'inputs': {}, 'intent_id': '…'})`
- **`jules-protocol-preamble`** (discipline): detect-mode → verify-remote-state → name-canonical-tools → set-scope → dispatched
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-protocol-preamble', 'inputs': {}, 'intent_id': '…'})`
- **`jules-recovery-when-stuck`** (discipline): classify-state → probe-once → patch-or-empty → recovered
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-recovery-when-stuck', 'inputs': {}, 'intent_id': '…'})`
- **`jules-self-improvement`** (discipline): collect-dogfood → fold-into-graph
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-self-improvement', 'inputs': {}, 'intent_id': '…'})`
- **`jules-tool-discipline`** (discipline): apply-tool-discipline
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-tool-discipline', 'inputs': {}, 'intent_id': '…'})`
