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
  1. **plan-batch** — Plan the batch of independent items.
     Enumerate the independent items to fan out across Jules sessions — each must be self-contained (no shared state, no ordering dependency).
  2. **fan-out** — Fan out a Jules session per item.
     delegate.fan_out(driver='jules') spawns N child Lifecycles, each driving a Jules session, bounded by the quota arg.
  3. **join** — Confirm every child resolved.
     This skill does NOT auto-join — it pauses until you confirm every child session resolved to an outcome. Confirm only when the fan-out genuinely completed.
- **`jules-pr-review-cycle`** (discipline): read-comments → draft-replies → reply-on-github
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-pr-review-cycle', 'inputs': {}, 'intent_id': '…'})`
  1. **read-comments** — Read the PR review comments.
     Fetch the review comments via GitHub MCP and read them for what they actually ask — understand before replying.
  2. **draft-replies** — Draft replies carrying the protocol handshake.
     jules.review_comment drafts each reply WITH the mandatory protocol handshake tail. Address the comment with technical substance, not performative agreement.
  3. **reply-on-github** — Post the replies on GitHub.
     Post the drafted replies via GitHub MCP. Be frugal — only reply where a reply genuinely advances the review.
- **`jules-protocol-preamble`** (discipline): detect-mode → verify-remote-state → name-canonical-tools → set-scope → dispatched
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-protocol-preamble', 'inputs': {}, 'intent_id': '…'})`
  1. **detect-mode** — Detect dogfood vs delegate mode.
     jules.detect_mode resolves whether this dispatch is dogfood (self-source, Mode A) or delegate (another repo, Mode B). The mode drives the preamble and the read-only clone assertion.
  2. **verify-remote-state** — Guard against a silent fail before dispatch.
     jules.verify checks the remote branch state — the silent-fail guard (COMPLETED != pushed). Don't dispatch onto a dirty or unexpected remote.
  3. **name-canonical-tools** — Lint that the prompt names every canonical tool.
     jules.lint_prompt refuses to advance unless the assembled prompt NAMES every canonical tool symbol (read_file, …). A prompt that doesn't name its tools leaves the remote agent guessing.
  4. **set-scope** — Declare the scope allow-list + read-only assertion.
     Declare the affects-paths allow-list, the no-create-outside boundary, and (Mode B) the read-only agency-clone assertion. Scope is the safety rail on a remote agent.
  5. **dispatched** — Confirm the dispatch landed with a session id.
     The walker pauses until a session_id is supplied + confirmed. Confirm this gate only once the Jules session actually exists.
- **`jules-recovery-when-stuck`** (discipline): classify-state → probe-once → patch-or-empty → recovered
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-recovery-when-stuck', 'inputs': {}, 'intent_id': '…'})`
  1. **classify-state** — Classify the stuck session's state.
     jules.status returns the session resource so you can branch on state + has_outputs — is it silently failed, awaiting approval, or genuinely still working?
  2. **probe-once** — Probe the agent ONCE to push or reply empty.
     jules.message nudges the agent to push its work or reply EMPTY — the canonical recovery probe. Probe once; don't spam a stuck session.
  3. **patch-or-empty** — Extract the session's patch outputs.
     jules.patch extracts the patch outputs (files/lines/bytes) for the recovery plan — the fallback when the agent won't push.
  4. **recovered** — Confirm recovery — a PR url or EMPTY.
     Supply the pr_url (or the sentinel EMPTY when no recovery was needed) + confirm. Confirm only when the session is genuinely recovered or definitively empty.
- **`jules-self-improvement`** (discipline): collect-dogfood → fold-into-graph
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-self-improvement', 'inputs': {}, 'intent_id': '…'})`
  1. **collect-dogfood** — Collect the dogfood observations.
     dogfood.collect walks Plan/**/DOGFOOD-NOTES.md and returns the observations + a flat texts list ready for bulk ingestion.
  2. **fold-into-graph** — Fold the observations into the graph as Reflections.
     reflect.batch_note writes one Reflection node per text in a single invocation — the durable-memory half of the dogfood loop.
- **`jules-tool-discipline`** (discipline): apply-tool-discipline
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'jules-tool-discipline', 'inputs': {}, 'intent_id': '…'})`
  1. **apply-tool-discipline** — Lint that a draft prompt names its tools.
     jules.lint_prompt over a draft prompt — the reusable predicate the preamble's phase 3 also invokes. Refuses unless every canonical tool symbol is named; walk it standalone to lint a draft before committing to a dispatch.

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_jules_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_jules_activities", {"intent_id": iid})
await call_tool("capability_jules_alias", {"intent_id": iid})
await call_tool("capability_jules_apply_patch", {"intent_id": iid})
await call_tool("capability_jules_approve_awaiting", {"intent_id": iid})
await call_tool("capability_jules_approve_plan", {"intent_id": iid})
await call_tool("capability_jules_detect_mode", {"intent_id": iid})
```

More verbs: `capability_jules_dispatch`, `capability_jules_lint_prompt`, `capability_jules_list`, `capability_jules_message`, `capability_jules_patch`, `capability_jules_patch_body`, `capability_jules_plan`, `capability_jules_quota` …
