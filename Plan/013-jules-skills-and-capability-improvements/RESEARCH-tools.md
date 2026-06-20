# RESEARCH-tools — Jules tool catalogue (A1)

Source: `_jules_reference.md` §3a–§3f; `capabilities/jules.py:127-336`; `_jules_api.py:140-396`.

## 1. Complete tool catalogue (Jules-internal; agent-side)

**Filesystem (§3a)** — Standard, Python-call syntax:
- `list_files(path="")` — directory listing; "Run `list_files('src/')`".
- `read_file(filepath)` — ingest plaintext; "Use `read_file('path')` before editing".
- `write_file(filepath, content)` — create/overwrite; "Call `write_file(...)` ONLY for new files".
- `delete_file(filepath)` / `rename_file(filepath, new_filepath)` — guarded mutations.
- `restore_file(filepath)` / `reset_all()` — localised / global rollback to clone state.

**Plan + state machine (§3b)**:
- `set_plan(plan)` — register numbered markdown plan; re-callable.
- `request_plan_review(plan)` — suspend autonomy for human plan approval BEFORE `set_plan`.
- `record_user_approval_for_plan()` — internal lock post-approval.
- `plan_step_complete(message)` — advance the state machine; "verify changes via `read_file`/`list_files` first, then `plan_step_complete(...)`".
- `done(summary)` — terminate sub-agent loop.

**CI / testing / submission (§3c)**:
- **`pre_commit_instructions()`** — mandatory pre-flight checklist; "Call `pre_commit_instructions()` and execute every step before `submit`".
- **`submit(branch_name, commit_message, title, description)`** — the ONLY publish-to-remote primitive; "When the work compiles and tests pass, call `submit(branch_name='...', commit_message='...', title='...', description='...')` — this is the only way work leaves the VM".
- `request_code_review()` — internal Critic agent pre-PR; "Run `request_code_review()` before `submit`".
- `frontend_verification_instructions()` / `frontend_verification_complete(...)` — Playwright + screenshot.
- `start_live_preview_instructions()` — dev-server port binding.

**Multimodal (§3d)**: `google_search`, `view_text_website`, `knowledgebase_lookup`, `view_image`, `read_image_file`, `read_media_file`.

**HIL / orchestration (§3e)**:
- `message_user(message, continue_working)` — STATUS only; "Use `message_user(...)` for progress reports — NEVER for questions" (§3e forbids).
- **`request_user_input(message)`** — dedicated blocking ask; "If you need clarification, call `request_user_input('...')` — not `message_user`".
- `read_pr_comments()` / `reply_to_pr_comments(replies)` — PR review loop.
- `initiate_memory_recording()` — long-term repo memory.

**DSL / Special (§3f)**:
- `run_in_bash_session` — persistent shell; raw bash on lines after the tool name.
- **`replace_with_git_merge_diff`** — precision edits with `<<<<<<< SEARCH` / `======= ` / `>>>>>>> REPLACE` markers; "For multi-line code changes use `replace_with_git_merge_diff` — never rewrite a whole file with `write_file`".

## 2. The "must-name" tools (silent-fail prevention)

`submit(branch_name, commit_message, title, description)` (§3c) — almost certainly the missing instruction in our Phase 4/6 silent-fail (`jules.py:6-9`). `pre_commit_instructions()` (§3c) — mandatory pre-flight. `request_user_input(message)` (§3e) — dedicated blocking ask; `message_user` forbidden for questions. `replace_with_git_merge_diff` (§3f) — precision edits, no JSON-escape failure. `request_code_review()` (§3c) — internal Critic before PR.

## 3. Mapping to spec-012 `INSTRUCTIONS` (per `WatchAction`)

- `review_and_approve_plan` — name `set_plan`, `request_plan_review` (§3b); agent-side `jules.plan` + `jules.approve_plan`.
- `answer_agent_question` — Jules MUST have used `request_user_input` (§3e); reply via `jules.message`.
- `verify_pr` — name `read_pr_comments` / `reply_to_pr_comments` (§3e); confirm via `git ls-remote` (NOT local HEAD).
- `recover_silent_fail` — name `pre_commit_instructions` + `submit` (§3c) in the probe prompt — the canonical missed pair.
- `recover_apply_plan` — agent-side GitHub MCP (`create_branch` / `push_files` / `delete_file` / `create_pull_request`); Jules tools no longer in scope.
- `dispatch_fresh` — fresh session; preamble must name `pre_commit_instructions` + `submit` + `replace_with_git_merge_diff` + `request_user_input`.
- `inspect_and_resume` — name `read_file` / `list_files` (§3a) + `plan_step_complete` (§3b) before `submit`.
- `terminal` — no tool nomination.

## 4. Anti-patterns (cite §)

- Using `message_user` for questions (§3e — explicitly forbidden; only `request_user_input` blocks).
- Rewriting whole files with `write_file` instead of `replace_with_git_merge_diff` (§3a vs §3f — JSON-escape failure mode).
- Skipping `pre_commit_instructions()` before `submit` (§3c — "mandatory pre-flight").
- Claiming local HEAD as remote head (`jules.py:5-6, 244-262`; §3c — `submit` is the only push primitive; verify via `git ls-remote`).
- Calling `grep(pattern)` (§3f — deprecated; use `rg` via `run_in_bash_session`).
