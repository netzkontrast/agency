# Jules — architectural and operational reference

Authoritative reference for the Google Jules execution environment, tool
schemas, and orchestration surface. Stored beside the `jules` capability
source as a knowledge base; the agency does NOT auto-load this file (the
`_` prefix is consistent with the boundary-vs-capability convention).

The agency's design work for the `jules` capability + the planned Jules
skills (`Plan/013-…`) draws on this document.

> Source: user-supplied research synthesis,
> "Architectural and Operational Analysis of Google Jules: Execution
> Environments, Tool Schemas, and Autonomous Agentic Capabilities."

---

## 1. The agentic-workflow paradigm

Jules is an **asynchronous autonomous coding agent**, decoupling prompt
execution from immediate user supervision. Powered by Gemini 3.1 Pro / 3 Flash.
Three architectural pillars:

- An ephemeral, highly tailored **virtual-machine environment**.
- A **dual-paradigm tool-calling schema** (Standard tools = Python syntax;
  Special tools = a custom DSL).
- A **REST API + MCP server + scriptable CLI** orchestration layer.

The asymmetry between human-driven IDEs and agent-driven workflows requires
*programmatic guarantees, strict guardrails, and deterministic feedback
loops* to prevent hallucination spirals.

## 2. The VM sandbox

Each session gets a secure short-lived Ubuntu VM. Modernised baseline image
with pinned toolchains:

| Stack | Pinned | Also available |
|---|---|---|
| Python | 3.12.11 | 3.10.18 (pyenv) |
| Python utils | pip 25.1.1, pipx 1.4.3, poetry 2.1.3, uv 0.7.13, black 25.1.0, mypy 1.16.1, pytest 8.4.0, ruff 0.12.0 | — |
| Node | v22.16.0 | v18.20.8, v20.19.2 (nvm) |
| Node utils | npm 11.4.2, yarn 1.22.22, pnpm 10.12.1, eslint 9.29.0, prettier 3.5.3, chromedriver 137.0.7151.70 | — |
| Java | OpenJDK 21.0.7 | — |
| Other | Go, Rust, Bun | — |

Plus standard Unix utilities: `git 2.49.0`, `grep 3.11`, `gzip 1.12`, `jq 1.7`,
`make 4.3`, `rg 14.1.0`, `sed 4.9`, `tar 1.35`, `tmux 3.4`, `yq`.

**Environment snapshots:** on first successful repo setup (e.g. `setup.sh`),
Jules captures a persistent memory + filesystem snapshot; subsequent tasks
hydrate from the snapshot, bypassing cold-start. **Env vars** are repo-scoped,
defined in the dashboard, cryptographically locked for the task duration.

**Filesystem topology:** repos clone into `/app`; bash runs from repo root by
default. `AGENTS.md` is a localised, **overriding system prompt** scoped to
its directory subtree — nested `AGENTS.md` files **override** higher ones.

## 3. The dual-paradigm tool schema

Standard tools — Python syntax: `tool_name(arg1="value")`. Deterministic API
calls, file I/O, state updates, UI messages.

Special tools — custom DSL: tool name on line 1, raw unescaped args on
subsequent lines. Used for raw code and shell commands to avoid JSON-escape
failures.

### 3a. Standard tools — filesystem

| Tool | Description |
|---|---|
| `list_files(path="")` | `ls -a -1F --group-directories-first <path>`; dirs get trailing `/` |
| `read_file(filepath)` | Ingest plaintext into context; hard error on missing path |
| `write_file(filepath, content)` | Create-or-overwrite; superseded `create_file_with_block`/`overwrite_file_with_block` |
| `delete_file(filepath)` | Removes file; errors on invalid path |
| `rename_file(filepath, new_filepath)` | Move/rename with strong guards (missing src, existing dst, missing parent) |
| `restore_file(filepath)` | Localised rollback to original cloned state |
| `reset_all()` | Global rollback — entire repo + sandbox to pristine clone state |

### 3b. Standard tools — plan + state machine

| Tool | Description |
|---|---|
| `set_plan(plan)` | Register the operational plan (numbered markdown list); re-callable |
| `request_plan_review(plan)` | Suspend autonomy; ask human to approve the architectural approach BEFORE `set_plan` |
| `record_user_approval_for_plan()` | Internal lock once the user approves via UI; minor revisions don't need re-approval |
| `plan_step_complete(message)` | Advance state machine; **must verify changes via `read_file`/`list_files` first** |
| `done(summary)` | Terminate a sub-agent loop with a summary payload |

### 3c. Standard tools — CI / testing / submission

| Tool | Description |
|---|---|
| `pre_commit_instructions()` | **Mandatory pre-flight**: dynamic, contextual checklist (tests, formatting, linting) required before `submit` |
| **`submit(branch_name, commit_message, title, description)`** | **Packages VM filesystem state into a Git commit AND pushes it to remote; triggers user approval workflow for the PR.** This is the only tool that publishes work — naming it explicitly in dispatch prompts prevents silent-fail-without-PR. |
| `request_code_review()` | Triggers the internal Jules Critic agent for edge-case/bug review BEFORE the PR is human-visible |
| `frontend_verification_instructions()` | Returns sandbox-specific Playwright boilerplate |
| `frontend_verification_complete(screenshot_path, additional_media_paths=[])` | Attach UI screenshots to session context |
| `start_live_preview_instructions()` | Bind a local dev server to sandbox-exposed ports |

### 3d. Standard tools — multimodal + external info

| Tool | Description |
|---|---|
| `google_search(query)` | Live web search; bypasses training cutoff |
| `view_text_website(url)` | Headless scrape, DOM stripped to plaintext (needs sandbox internet) |
| `knowledgebase_lookup(query)` | Google's internal proprietary developer KB (frameworks, error signatures) |
| `view_image(url)`, `read_image_file(filepath)`, `read_media_file(filepath)` | Gemini multimodal; reads PNG/WebP/JPEG and webm video |

### 3e. Standard tools — human-in-the-loop + orchestration

| Tool | Description |
|---|---|
| `message_user(message, continue_working)` | Status update; `continue_working=False` suspends until user state change. **Forbidden for questions.** |
| `request_user_input(message)` | The **dedicated blocking tool** for clarification / scope escalation |
| `read_pr_comments()` | Ingest pending PR review feedback |
| `reply_to_pr_comments(replies)` | JSON list of `{comment_id, reply}` — conversational review on GitHub |
| `call_hello_world_agent(message)` | Diagnostic inter-agent comms test |
| `initiate_memory_recording()` | Long-term memory module — record architectural decisions for future sessions on the same repo |

### 3f. Special tools — DSL

**`run_in_bash_session`** — persistent shell across invocations (env vars, venvs, sourced scripts survive). The model is taught explicit pipelines:
- Background processes: `npm start > npm_output.log 2>&1 &`
- Port collision: `kill $(lsof -t -i :<port>) 2>/dev/null || true`
- Process hunting: `pgrep -af <pattern>` + `kill <PID>`
- (The earlier `grep(pattern)` tool is **deprecated** — use native `grep`/`rg` via bash.)

**`replace_with_git_merge_diff`** — precision text manipulation with Git merge-conflict markers. DSL shape:

```
replace_with_git_merge_diff
path/to/file.py
<<<<<<< SEARCH
[exact original block, indentation matters]
=======
[replacement block]
>>>>>>> REPLACE
```

Avoids the JSON-escape failure mode of LLMs writing multi-line diffs.

## 4. REST API resource model

Base `https://jules.googleapis.com/v1alpha`, header `x-goog-api-key`. Three hierarchical entities:

- **Sources** (`/sources/{id}`) — connected ingestible environments (GitHub repos). Schema: owner, repo, privacy, default-branch, branches.
- **Sessions** (`/sessions/{id}`) — overarching project / continuous unit of agentic work. Schema: prompt, title, sourceContext (incl. `startingBranch`), `requirePlanApproval`, **`automationMode`** (e.g. `AUTO_CREATE_PR` enables true zero-touch by bypassing confirmation).
- **Activities** (`/sessions/{id}/activities/{actId}`) — atomic events. Each carries an `originator` (`user|agent|system`), `createTime`, and any artefacts. Types: `PlanGenerated`, `PlanApproved`, `UserMessaged`, `AgentMessaged`, `ProgressUpdated`, `SessionCompleted`, `SessionFailed`, `CodeChanges` (a discrete trackable ChangeSet), `BashOutput` (raw stdout/stderr), `Media`.

### Session state machine

`STATE_UNSPECIFIED → QUEUED → PLANNING → AWAITING_PLAN_APPROVAL → AWAITING_USER_FEEDBACK ↔ IN_PROGRESS → COMPLETED | FAILED | PAUSED | CANCELLED`

**Critical: `COMPLETED` is NOT a single terminal state.** The same value
overloads four distinct situations distinguishable only via the activity
stream — see `AGENCY_PROTOCOL.md §1` for the routing rules. The watcher's
`_classify` (`agency/capabilities/_jules_watch.py`) discriminates them via
`plan_unapproved` + `branch_on_remote` + `patch_summary`. From a one-shot
orchestrator (no long-lived watcher), call `jules.activities(sid)` after
any COMPLETED read to determine which case actually applies.

`FAILED`, `PAUSED`, and `CANCELLED` are genuinely terminal — see the
classifier's terminal-stickiness invariant.

## 5. CLI

`@google/jules` — Node.js. Surface includes `jules remote new`, `jules remote list`, **`--parallel`** (up to 60 concurrent agents on the Ultra tier). Unix-pipe friendly: `gh issue list | jq | jules remote new`.

## 6. MCP — the thick-server architecture

JSON-RPC 2.0 over stdio. Three layers:
- **MCP protocol interface** — async request handling for resources/tools/prompts.
- **API client abstraction** — type-safe HTTP, key injection (`X-Goog-Api-Key`), exponential backoff.
- **State management** — local JSON (`~/.jules-mcp/schedules.json`) for stateful persistence across ephemeral execution.

**Security:** strict allow-list — Linear, Stitch, Neon, Tinybird, Context7, Supabase. Other MCP servers cannot be added without Google audit. Bidirectional data flows are validated; permission scope of every requested tool is audited.

## 7. Operational implications for the agency `jules` capability

Distilled cues this document gives our spec / capability work:

- **Always name `submit` and `pre_commit_instructions` in dispatch prompts.** Prose alone leaves work in the VM only — the canonical silent-fail mode. Most likely root cause of "COMPLETED with outputs, no branch on origin."
- **Activity types are richer than our current taxonomy** — `CodeChanges`, `BashOutput`, `Media` should be first-class kinds in the watcher's classifier.
- **`automationMode: AUTO_CREATE_PR`** is the right default for the agency-driving-Jules pattern; lift to the `dispatch` verb.
- **`request_user_input` vs `message_user`** matters — the system explicitly forbids questions through `message_user`. Our recovery prompts that include questions must demand `request_user_input` if we want a blocking reply.
- **Session-level env vars** survive across the VM lifecycle; the agency could ship a small `agency-protocol` env-var set (timeouts, branch naming) to reduce per-prompt boilerplate.
- **Snapshot architecture** means dispatching against the same repo+branch reuses the warm image — multi-phase Jules dispatches against the agency repo should be fast.
- **AGENTS.md lexical scoping** — we could place an `AGENTS.md` at the agency repo root telling Jules: always run `pytest -q`, follow conventional-commits, **never** report a local HEAD as the remote head, verify via `git ls-remote` before claiming done, use `submit` to publish.
- **`replace_with_git_merge_diff` is the most reliable edit primitive** for Jules — our dispatch prompts could nudge toward it for any multi-line code change to reduce hallucinated edits.
- **MCP allow-list is closed** — we cannot host an agency MCP for Jules to call directly; the integration direction is Jules → external MCP, not Jules → our MCP.
- **The Jules Critic (`request_code_review`)** is a built-in parallel reviewer. We can ask Jules to invoke it before `submit` to raise per-session quality.

---

*End reference.*
