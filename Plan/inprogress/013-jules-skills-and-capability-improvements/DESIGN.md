# Spec 013 — DESIGN.md (Phase B draft)

Synthesised from `RESEARCH-tools.md` (A1) · `RESEARCH-operational.md` (A2) ·
`RESEARCH-skills.md` (A3) and grounded in `agency/capabilities/_jules_reference.md`
+ `docs/vision/CORE.md` + the spec 012 design + spec 012 DOGFOOD-NOTES.

## Why

The agency's `jules` capability covers the v1alpha REST surface (post-spec-012)
but **the agent inside Jules doesn't know our operational doctrine**. The
in-flight Phase 4/6 silent-fail is the proof:
**`COMPLETED + has_outputs=True + no branch on origin`** for both sessions
(`DOGFOOD-NOTES.md:77-85`) — almost certainly because the dispatch prompt **never
named `submit(...)`**, the *one* Jules tool that publishes work to remote
(`RESEARCH-tools.md §2`, `_jules_reference.md §3c`).

The canon answers this without new concepts: **a skill IS a capability**
(`CORE.md:47-62`, Lifecycle template of atomic gated step-graphs). We add a
small intersecting set of Jules-specific skills that carry the doctrine, plus
narrow deltas on the `jules` capability surface, plus a one-time `AGENTS.md`
at the repo root that Jules sessions inherit through the lexical-scoping
mechanism (`_jules_reference.md §2` last paragraph; A2 §2).

## Done When

- [ ] **Six new skills** land on `JulesCapability.ontology.skills`, each
  composing existing Capability verbs via the `Phase.invoke` binding pattern
  (`develop.py:65-71` precedent). Names + phase counts in `## Design — the
  skill set` below. No new top-level concept; no new role-tag.
- [ ] **Two capability deltas on `jules.dispatch`** (panel cut `agents_md_path`
  — Phase C REVIEW must-fix #2: write-semantics into Jules's VM filesystem are
  fuzzy and `protocol_preset` + the committed root `AGENTS.md` cover every
  A2 case): `automation_mode=""` and `protocol_preset=""`. Plus a defined
  interaction matrix with the existing `require_plan_approval`/`auto_create_pr`
  flags (see `## Design — capability deltas`, "Flag interaction matrix").
- [ ] **A single `agency-default` preamble** (panel cut the multi-preset
  registry — REVIEW must-fix #1: speculative presets undermine the token-win
  claim) in `agency/capabilities/_jules_preambles.py`. It carries ONLY the
  must-name tool list (A1 §2) + a pointer line to `AGENTS.md`; the 5
  invariants live at the repo root, paid for once per snapshot (see the
  "AGENTS.md vs preset" split below).
- [ ] **Spec 012's `INSTRUCTIONS` table is updated** to name the right Jules
  tools per A1 §3 — `recover_silent_fail` explicitly tells the agent to call
  `pre_commit_instructions()` then `submit(...)`; `dispatch_fresh` names the
  full must-name set; `answer_agent_question` instructs the agent to use
  `request_user_input` (NOT `message_user`).
- [ ] **`AGENTS.md` at the repo root** carries the 5 invariants from A2 §5.
  Per `_jules_reference.md §2`, every Jules dispatch into this repo
  inherits it automatically — no per-prompt boilerplate.
- [ ] **`AGENCY_PROTOCOL.md` at the repo root** — the renamed +
  generalised `JULES_PROTOCOL.md` (the doctrine applies to any remote
  async agent the agency drives, not just Jules — Jules today, others
  tomorrow). Carries: `COMPLETED ≠ done`, silent-fail-recovery flow,
  scope discipline, the must-name publish tool (whatever it's called for
  the agent in question), `request_user_input`-style blocking-ask rule.
  `AGENTS.md` cites it; the `agency-default` preamble points at it.
- [ ] **Dispatch-mode dispatcher** in `_jules_preambles.py`
  `assemble(source, starting_branch, prompt, preset_name) → text`. Detects:
  - **Mode A — dogfood** (source == `"netzkontrast/agency"`, configurable
    via `agency.dispatch_self_source`): Jules works directly in the
    agency repo. R+W there. AGENTS.md + AGENCY_PROTOCOL.md are inherited
    via Jules's lexical scoping (`_jules_reference.md §2`) — preamble
    carries only the per-dispatch must-name tool list.
  - **Mode B — delegate** (any other source): Jules is helping on a
    target project (the plugin is installed in someone else's repo via
    Claude Code). The preamble explicitly instructs Jules to
    `git clone --depth=1 https://github.com/netzkontrast/agency.git ~/work/vendor/agency`
    READ-ONLY, then `read_file('~/work/vendor/agency/AGENTS.md')` +
    `read_file('~/work/vendor/agency/AGENCY_PROTOCOL.md')` BEFORE
    drafting any plan. R+W happens in the target project (the dispatch
    `source`), never in the agency clone. The preamble must say so
    explicitly — the agency repo is *reference only* in Mode B.
- [ ] **`jules.verify` already uses `vcs.remote_exists`** (Spec 012 Phase 5,
  shipped at commit `6059c74`). This spec re-affirms: never trust local HEAD.

## Design — the skill set

Six intersecting skills. **Chaining via shared hard gates is the canon-aligned
intersection model** (A3 §3, recommended (a); proven by `develop.review.dispatch`
invoking `delegate.fan_out`). One skill's hard gate is the next's precondition;
no new walker support is required.

### 1. `jules-protocol-preamble` (5 phases, 1 hard gate)

```
detect-mode          advisory  → produces: mode  (∈ {"dogfood", "delegate"})
verify-remote-state  advisory  → produces: branch_on_remote   # invoke: jules.verify
name-canonical-tools advisory  → produces: must_name          # list of tool names
set-scope            advisory  → produces: affects_paths, no_create_outside, agency_clone_ro_in_delegate
dispatched           HARD GATE → produces: session_id
```

Walked **once per dispatch**. Per the Phase C panel review:

- **Phase 1 (`detect-mode`)** compares the `source` arg against
  `agency.dispatch_self_source` (default `"netzkontrast/agency"`).
  `mode="dogfood"` → Jules reads AGENTS.md + AGENCY_PROTOCOL.md via the
  lexical scoping mechanism (`_jules_reference.md §2`); `mode="delegate"`
  → the preamble carries the explicit
  `git clone --depth=1 https://github.com/netzkontrast/agency.git ~/work/vendor/agency`
  instruction + `read_file('~/work/vendor/agency/{AGENTS,AGENCY_PROTOCOL}.md')`.
- **Phase 2 (`verify-remote-state`)** binds to `jules.verify` via `invoke`
  and produces `branch_on_remote` — the real field returned at
  `jules.py:261` (the panel's source-faithfulness fix: the original
  draft invented `remote_head`/`vcs_clean`).
- **Phase 3 (`name-canonical-tools`)** produces the per-dispatch
  `must_name` list — the panel collapsed the prior 5-phase
  `jules-tool-discipline` skill (see #2 below) into a real predicate; this
  phase invokes the new `jules.lint_prompt(text, must_name=[…])` verb to
  *validate* the assembled prompt contains those names — a one-shot
  predicate, not five tautological booleans.
- **Phase 4 (`set-scope`)** produces the `affects:` allow-list +, in
  delegate mode only, the `agency_clone_ro_in_delegate` flag asserting
  Jules will never write to the agency clone.
- **Phase 5 (`dispatched`)** is the hard `elicit` gate (`CORE.md:56-60`):
  walker stays at `input-required` until a real `session_id` is supplied
  by the dispatch flow.

### 2. `jules-tool-discipline` — collapsed to 1 advisory phase + a new predicate verb

Phase C REVIEW must-fix #5: the original 5-phase shape was tautological
("was this string in the prompt?" × 5 isn't a skill). Two cleaner options;
this design takes **(a)** — add a real predicate verb:

- **New verb `jules.lint_prompt(text, must_name=[…])` *(transform)*** on
  `JulesCapability` — returns `{ok, missing: [str, …], extras: [str, …]}`.
  Symmetric with `plugin.lint_skill` (the CSO linter). Used by Phase 3 of
  `jules-protocol-preamble` (above) AND by `jules-pr-review-cycle` to lint
  the response prompts Jules will assemble in reply to PR comments.
- **The skill collapses to one advisory document phase**:
  ```
  apply-tool-discipline   advisory → produces: lint_result   # invoke: jules.lint_prompt
  ```
  Walked from inside `jules-protocol-preamble` Phase 3, not as a separate
  top-level skill. The doctrine still lives in `AGENCY_PROTOCOL.md` (root)
  and the `agency-default` preamble's must-name section; the *predicate*
  enforces it.

### 3. `jules-recovery-when-stuck` (4 phases, 1 hard gate)

```
classify-state          → produces: state, branch_on_remote
probe-once              → produces: probe_at, probe_count
patch-or-empty          → produces: files, lines, bytes  (invoke: jules.patch)
recovered               HARD GATE → produces: pr_url
```

Walked by the watcher's `recover` flow (spec 012). Phase 1 binds to
`jules.status` + `jules.verify`. Phase 2 binds to `jules.message`. Phase 3
binds to `jules.patch`. Phase 4 hard-gates until either a branch appears
(`recover_silent_fail → verify_pr` WatchEvent transition) or the local-apply
plan executes (`recover_apply_plan` WatchEvent).

### 4. `jules-pr-review-cycle` (3 phases, advisory)

```
read-comments      → produces: comments  (invoke: github.list_review_comments  via GitHub MCP)
draft-replies      → produces: replies
reply-on-github    → produces: posted    (invoke: github.add_reply_to_pull_request_comment)
```

Composes the GitHub MCP read/reply path. Mirrors what we did by hand on
PR #1 (`bf6a26e8` round). Jules itself uses `read_pr_comments` /
`reply_to_pr_comments` (A1 §1 HIL/orchestration); the agency side composes
the GitHub MCP equivalents.

### 5. `jules-fanout` (3 phases, hard gate)

```
plan-batch        → produces: items
fan-out           → produces: child_sessions  (invoke: delegate.fan_out, driver="jules")
join              HARD GATE → produces: child_outcomes
```

The `develop.review` precedent for chaining via `invoke: delegate.fan_out`
(`develop.py:65-71`). Quota is the existing `delegate` arg; this skill is
just the canonical composition.

### 6. `jules-self-improvement` (2 phases, advisory)

```
collect-dogfood   → produces: observations
fold-into-spec    → produces: design_deltas, open_questions  (invoke: reflect.note)
```

After a fan-out completes, this walks the dogfood ledger (mirrors what we
already do in `Plan/012/DOGFOOD-NOTES.md`) and records improvements as
`Reflection` nodes (`reflect.note`). The capability is the dogfood loop
itself, made first-class.

### Intersection / chaining

Hard gates are the join points. Concretely:

- `jules-protocol-preamble.dispatched.session_id` → input to *every*
  subsequent Jules skill.
- `jules-tool-discipline.publish-named` *must* be true before the prompt
  is sent — gated by `jules.dispatch` itself, not the walker (social
  enforcement, A3 §3).
- `jules-recovery-when-stuck.recovered.pr_url` → input to
  `jules-pr-review-cycle` (the loop closes).

No name-keyed gate registry needed; chaining is by data flow.

## Design — capability deltas

### `jules.dispatch` — 2 new pass-through args (panel cut `agents_md_path`)

```python
@verb(role="effect")
def dispatch(self, source, starting_branch, prompt,
             title="", require_plan_approval=True, auto_create_pr=False,
             alias="",
             # NEW (spec 013):
             automation_mode="",   # "" | "AUTO_CREATE_PR"; canonical Jules name
             protocol_preset="") -> dict:
```

`agents_md_path` was cut per Phase C REVIEW must-fix #2 — write semantics
into Jules's VM filesystem are fuzzy (we don't own it; AUTHORING an
`AGENTS.md` from the dispatch side may collide with what's already there)
and the committed root-level `AGENTS.md` + the Mode-B clone instruction
in the preamble cover every case.

### Flag interaction matrix (panel must-fix #3)

`automation_mode` × `auto_create_pr` × `require_plan_approval` was a
6-way space with no doctrine. The matrix:

| `require_plan_approval` | `automation_mode` | Meaning | Recommended? |
|---|---|---|---|
| `True` | `""` | Plan-gated; agent confirms PR open. Doctrine default. | ✅ default |
| `True` | `"AUTO_CREATE_PR"` | Plan-gated; PR auto-opens after work. Agency-driving-Jules pattern. | ✅ opt-in |
| `False` | `""` | No plan gate; agent confirms PR. **Legacy** (spec-012 dispatch shape before Phase 5 flipped the default). | ⚠️ legacy |
| `False` | `"AUTO_CREATE_PR"` | Zero-touch (no plan gate, auto-PR). | ❌ unsafe — requires `affects:`-locked spec |

**`auto_create_pr` is deprecated** in favor of `automation_mode`: `dispatch`
treats `auto_create_pr=True` as a back-compat alias mapping to
`automation_mode="AUTO_CREATE_PR"`. A deprecation warning fires once per
process. Removed in a future spec.

### `protocol_preset` — single preset, the panel cut

```python
PREAMBLE: str = _AGENCY_DEFAULT_PREAMBLE   # NOT a dict; one preset, per panel must-fix #1
```

`protocol_preset="agency-default"` looks up this single constant. Future
presets can be added when the second one has a real, distinct caller —
shipping speculative `research-pass` / `code-edit` presets undermines the
token-win claim (panel REVIEW). Underscore-prefixed file
(`agency/capabilities/_jules_preambles.py`): skipped by capability
discovery; consumed lazily by `_jules_api.jules_create` when
`protocol_preset` is non-empty.

The preamble's responsibility is **narrow** (per the AGENTS.md-vs-preset
split below): the must-name tool list (A1 §2) + one literal pointer line
that tells Jules to obey `AGENTS.md` / `AGENCY_PROTOCOL.md` at the agency
repo root. The 5 doctrine invariants (A2 §5) live in those docs, paid
for once per snapshot — not per dispatch.

### `agency/capabilities/_jules_preambles.py` — single constant + mode dispatcher

```python
PREAMBLE: str = _AGENCY_DEFAULT_PREAMBLE  # one preset (panel must-fix #1)

def assemble(source: str, starting_branch: str, prompt: str,
             preset_name: str = "agency-default") -> str:
    """Compose the dispatch text.

    Mode A (dogfood, source == agency.dispatch_self_source):
      prepend PREAMBLE + the per-dispatch must-name tool list. AGENTS.md
      and AGENCY_PROTOCOL.md are inherited via Jules's lexical scoping
      (`_jules_reference.md §2`); we don't re-paste them.

    Mode B (delegate, any other source):
      prepend PREAMBLE + must-name list + an explicit clone instruction:
      `git clone --depth=1 https://github.com/netzkontrast/agency.git
       ~/work/vendor/agency` (READ-ONLY) +
      `read_file('~/work/vendor/agency/AGENTS.md')` +
      `read_file('~/work/vendor/agency/AGENCY_PROTOCOL.md')`
      BEFORE drafting any plan. R+W happens in `source`, never in the
      agency clone.
    """
```

Underscore-prefixed file: skipped by capability discovery; consumed
lazily by `_jules_api.jules_create` when `protocol_preset` is non-empty.

### Spec 012 `INSTRUCTIONS` update (the cross-cutting hook)

The `INSTRUCTIONS: dict[WatchAction, str]` constant in `_jules_watch.py`
(spec 012, when shipped) is replaced by the templates from A1 §3. Concretely:

| WatchAction | Names which Jules tools |
|---|---|
| `review_and_approve_plan` | `set_plan`, `request_plan_review` |
| `answer_agent_question`   | `request_user_input` (NOT `message_user`) |
| `verify_pr`               | `read_pr_comments`, `reply_to_pr_comments`; **verify via `git ls-remote` not local HEAD** |
| `recover_silent_fail`     | **`pre_commit_instructions()` → `submit(branch, commit_message, title, description)`** — the canonical missed pair |
| `recover_apply_plan`      | (agency-side; GitHub MCP) — Jules tools no longer in scope |
| `dispatch_fresh`          | full must-name set: `submit`, `pre_commit_instructions`, `request_user_input`, `replace_with_git_merge_diff`, `request_code_review` |
| `inspect_and_resume`      | `read_file`, `list_files`, `plan_step_complete` before any `submit` |
| `terminal`                | no tool nomination |

The 280-char cap from spec 012 likely relaxes to ~480 chars to fit the
tool-naming; still token-efficient (≤ 120 tokens per event).

## Design — `AGENTS.md` + `AGENCY_PROTOCOL.md` (split ownership)

Phase C REVIEW's biggest watch-out: **the overlap between `AGENTS.md` and the
`agency-default` preset must be designed deliberately**, or we re-pay tokens
on every dispatch for content already paid once at snapshot time. The split:

| Artefact | Owns | Lives | When paid |
|---|---|---|---|
| `AGENTS.md` (repo root) | Repo-wide conventions for **any** agent in this tree: ruff/black/mypy/pytest, conventional-commits, branch policy, `git ls-remote` verification, "**Do not narrate; record in `_lessons-learned/`**". Cites `AGENCY_PROTOCOL.md`. | `netzkontrast/agency` root | Once per snapshot (Mode A); once per clone (Mode B). |
| `AGENCY_PROTOCOL.md` (repo root) | The **doctrine** for any remote async agent the agency drives — formerly `JULES_PROTOCOL.md`, generalised. `COMPLETED ≠ done`. Silent-fail recovery. Scope discipline. The "publish tool must be named" rule. The blocking-ask rule (`request_user_input`-shape). | `netzkontrast/agency` root | Once per snapshot/clone. |
| `agency-default` preamble (`_jules_preambles.py`) | ONLY: (i) the per-dispatch must-name tool list (A1 §2) — `submit`, `pre_commit_instructions`, `request_user_input`, `replace_with_git_merge_diff`, `request_code_review`; (ii) one literal pointer line: `"Follow ~/AGENTS.md and ~/AGENCY_PROTOCOL.md."` | `agency/capabilities/_jules_preambles.py` | Once per dispatch (~120 tokens, not 700). |

**Mode A — dogfood** (`source == "netzkontrast/agency"`): Jules's lexical
scoping (`_jules_reference.md §2`) auto-inherits both root docs from the
cloned filesystem. The preamble carries only the must-name list + pointer.

**Mode B — delegate** (any other source): Jules is in another repo. The
preamble's pointer line becomes the explicit clone instruction (see
`_jules_preambles.assemble` above): clone agency READ-ONLY into
`~/work/vendor/agency`, `read_file` both root docs, THEN draft the plan.

### `AGENTS.md` content sketch (≤ 60 lines)

```markdown
# AGENTS.md — agency repo conventions

Applies to every coding agent in this tree (Claude Code, Jules, others).

## Verification (the silent-fail guard)
- `COMPLETED ≠ done`. A session reading COMPLETED with no branch on origin
  is the canonical silent-fail (see AGENCY_PROTOCOL.md).
- Verify via `git ls-remote origin <branch>` — never trust local HEAD.
- Tests: `pytest -q` from repo root must pass before any submit.

## Commits / branches
- Conventional commits (`feat:`, `fix:`, `chore:`).
- Develop on feature branches; PRs target `main`. Additive history; never
  rewrite or force-push.

## Style
- Python: ruff + black + mypy clean. No new lint regressions.
- Capabilities self-register (drop a file in `agency/capabilities/`).
- Skills are Lifecycle templates (CORE.md:47-62); no new top-level concepts.

## Discipline
- Read `AGENCY_PROTOCOL.md` for the remote-agent doctrine.
- Record reusable learnings in `_lessons-learned/` (timestamped, terse).
- Don't narrate; ship the artefact.
```

### `AGENCY_PROTOCOL.md` content sketch (≤ 80 lines)

```markdown
# AGENCY_PROTOCOL.md — remote async agent doctrine

Applies to any remote async agent the agency drives (Jules today; others
tomorrow). Formerly `JULES_PROTOCOL.md`; generalised.

## §1 — `COMPLETED ≠ done`
A session-state COMPLETED with `has_outputs=True` does NOT imply the work
is published. **Always verify the branch on origin via `git ls-remote`**
before declaring done. The silent-fail variants:
- COMPLETED + no branch on origin → publish step never ran.
- COMPLETED + branch on origin + no PR open → PR step skipped.
- COMPLETED + branch on origin + fabricated SHAs in agent messages →
  agent confabulated; trust `git ls-remote`, not chat.

## §2 — Name the publish tool
Every dispatch prompt MUST explicitly name the agent's publish tool. For
Jules: `pre_commit_instructions()` then `submit(branch, commit_message,
title, description)`. Prose alone leaves work in the VM.

## §3 — Scope discipline
- `affects:` is a hard allow-list. Touching a path outside `affects:`
  → emit a `BLOCKED:` PR and stop.
- No source copying (don't paste research-doc content into PR bodies).
- TDD: RED before GREEN before REFACTOR.

## §4 — Blocking ask vs status
- Questions go through the blocking-ask tool (`request_user_input` for
  Jules) — NEVER through `message_user` (status-only).
- One open question at a time.

## §5 — Recovery flow on silent-fail
1. Probe the agent ("your branch isn't on origin — push and reply with
   the PR URL, or reply `EMPTY` if nothing to publish").
2. If `EMPTY` → done; if PR URL → verify; if no reply within budget →
   extract the patch from the activity stream and apply via GitHub MCP.
3. Record the outcome on the `JulesSession` node.

## §6 — Network errors are orthogonal to session errors
TLS/clock-skew flakiness on the Jules API path is a `network_error`
WatchEvent — retry with back-off; never classify as session failure.
GitHub MCP runs on a different network path; use it as the fallback
verification channel.
```

This is the *single highest-leverage* artefact pair in the whole design:
written once, inherited (Mode A) or cloned-read-once (Mode B) by every
future dispatch.

## Files

- **Create**:
  - `AGENTS.md` (repo root) — agency-wide conventions for any agent in
    this tree (see content sketch above).
  - `AGENCY_PROTOCOL.md` (repo root) — the renamed + generalised
    remote-async-agent doctrine (was `JULES_PROTOCOL.md`); see content
    sketch above.
  - `agency/capabilities/_jules_preambles.py` — **single** `PREAMBLE`
    constant + `assemble(source, starting_branch, prompt, preset_name)`
    Mode-A/B dispatcher (NOT a multi-preset registry — panel must-fix #1).
  - `agency/capabilities/_jules_skills.py` (or extend `ontology.skills` in
    `jules.py`) — the six skill definitions.
  - `tests/test_jules_skills.py` — every skill walks end to end on a
    `StubJulesClient` + `StubVCS`; gates pause/resume correctly; preamble
    text shows up in the assembled prompt; Mode A vs Mode B branch.
  - `tests/test_jules_lint_prompt.py` — predicate verb: rejects prompts
    missing canonical tool names; passes when all `must_name` are present.
  - `Plan/013-…/REVIEW.md` (Phase C output, already landed).
- **Modify**:
  - `agency/capabilities/jules.py` — extend `dispatch` with the two new
    pass-through args (`automation_mode`, `protocol_preset`); add the new
    **`jules.lint_prompt(text, must_name=[…])` transform verb** (panel
    must-fix #5; symmetric with `plugin.lint_skill`); extend
    `JulesCapability.ontology.skills` to register the six skills.
  - `agency/capabilities/_jules_api.py` — `jules_create` accepts
    `automation_mode` and prepends the resolved preset to the prompt
    when `protocol_preset` is set.
  - `Plan/012-…/spec.md` — fold the `INSTRUCTIONS` table update into the
    spec's WatchEvent design (Phase 7 of spec 012's IMPLEMENTATION-PLAN
    will pick it up).
  - `Plan/JULES_PROTOCOL.md` → **renamed** to repo-root
    `AGENCY_PROTOCOL.md`; cross-references in
    `_lessons-learned/` updated.

## Open Questions

Phase D triage. Resolved questions moved into the body above; only true
blockers remain here for Phase E + later.

### Resolved by Phase D refinement

- ~~**OQ1 — `automation_mode` default.**~~ **Resolved** via the Flag
  Interaction Matrix (`## Design — capability deltas`): default `""`
  (plan-gated, agent-confirmed PR), opt-in `"AUTO_CREATE_PR"` for the
  agency-driving-Jules pattern. `auto_create_pr=True` becomes a back-compat
  alias with a deprecation warning.
- ~~**OQ2 — Preset registry vs per-dispatch arg.**~~ **Resolved** per
  panel must-fix #1: single `PREAMBLE` constant. New presets only when a
  second one has a real, distinct caller. Override via the explicit text
  prepend in `_jules_api.jules_create` is sufficient.
- ~~**OQ — `agents_md_path` on dispatch.**~~ **Resolved** per panel
  must-fix #2: cut. Mode-A inheritance + Mode-B clone-and-read covers
  every case the original arg was designed for.

### Still open (Phase E will decide)

1. **Mode A/B detection edge cases.** Two flavors:
   - **(a) Fork.** What if `source` is a fork of `netzkontrast/agency`
     (e.g. `someone-else/agency`) — Mode A or Mode B? Recommend: **Mode A
     if `agency.dispatch_self_source` matches OR the source's
     default-branch tip is an ancestor of agency's `main`**; else Mode B.
     Phase E should pick the cheap check (config flag) for v1.
   - **(b) Private agency mirror.** Some users may install the plugin
     from a private fork (e.g. enterprise mirror). Mode B's clone URL is
     currently hardcoded to the public GitHub URL. Should the assembler
     read it from `agency.dispatch_protocol_source_url` (configurable)?
     Recommend yes; default to the public URL.
2. **AGENTS.md scope nesting.** Root `AGENTS.md` covers the whole tree.
   Should there also be a nested `agency/AGENTS.md` (Python-specific:
   ruff/black/mypy/pytest discipline) that the lexical scoping
   (`_jules_reference.md §2`) would let override the root for source
   edits? Recommend: **no for v1**, single root keeps the model simple;
   revisit if linter conventions diverge between subtrees.
3. **The intersection model (validation, not selection).** Phase C
   confirmed (a) `develop`-style chaining via shared hard gates. Phase E
   test design must prove the chain: `jules-protocol-preamble.dispatched`
   produces a `session_id` consumed by `jules-recovery-when-stuck`'s
   `classify-state` phase; no name-keyed registry needed.
4. **Jules `inspect_and_resume` semantics.** Spec 012's `INSTRUCTIONS`
   table says PAUSED → `inspect_and_resume`. Reference §4 says PAUSED is
   "manually suspended." Is the right action there `inspect_and_resume`,
   or should the watcher emit `answer_agent_question` with the last
   activity-stream content? Phase E of spec 012 (not 013) will pick this
   up when it touches the WatchEvent design.
5. **Token budget for `INSTRUCTIONS` post-rename.** Spec 012 capped
   templates at 280 chars. Per the WatchAction table above, several
   entries grow to ~480 chars to fit tool-naming. Phase E: relax to 480
   (still ≤ 120 tokens per event) — vs. keep 280 + add a `tools_needed:[…]`
   field rendered by reference at the call site? Recommend **relax to
   480**: a literal-tool-name instruction is reliable; an indirected
   one re-introduces the silent-fail failure mode the design is closing.
6. **`AGENCY_PROTOCOL.md` cross-references.** The `_lessons-learned/`
   subtree references the old `JULES_PROTOCOL.md` path in multiple
   timestamped notes. Phase E task: a single rename + grep-and-update
   commit, recorded as the rename + a one-line note in
   `_lessons-learned/`.

## Evidence

- `RESEARCH-tools.md` (A1), `RESEARCH-operational.md` (A2),
  `RESEARCH-skills.md` (A3) — this draft is a faithful synthesis.
- `agency/capabilities/_jules_reference.md` §2-§7 — the architectural
  ground truth.
- `agency/capabilities/jules.py:127-336` — the current verb surface
  this design extends.
- `agency/capabilities/develop.py:28-80, 127` — the precedent for skill
  composition via `invoke`-bound phases + `OntologyExtension.skills`.
- `agency/examples/music.py:22-43` — the gated-skill exemplar.
- `agency/skill.py:24-86` — the canonical `SkillRun` walker.
- `docs/vision/CORE.md:47-62` (skills are Lifecycle templates),
  :56-60 (gates via elicit), :131-133 (capability-owned ontology).
- `Plan/inprogress/012-jules-complete-lifecycle-and-watcher/spec.md` — the
  `INSTRUCTIONS` table this design updates; the watcher's `recover`
  flow that consumes the new skills.
- `Plan/012-…/DOGFOOD-NOTES.md:77-85, 148-149` — live evidence of the
  silent-fail this design closes.
