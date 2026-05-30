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
- [ ] **Three capability deltas on `jules.dispatch`**: `automation_mode=""`,
  `protocol_preset=""`, `agents_md_path=""` — all default-off, all
  pass-through to `_jules_api.jules_create` / the prompt assembler.
- [ ] **A `protocol_preset` recipe registry** — module-level dict in
  `agency/capabilities/_jules_preambles.py` mapping `preset_name →
  preamble_text`. One canonical preset (`agency-default`) covers the 5
  invariants (A2 §5). Verbs and skills consume it by name; tokens are paid
  once per repo not per dispatch.
- [ ] **Spec 012's `INSTRUCTIONS` table is updated** to name the right Jules
  tools per A1 §3 — `recover_silent_fail` explicitly tells the agent to call
  `pre_commit_instructions()` then `submit(...)`; `dispatch_fresh` names the
  full must-name set; `answer_agent_question` instructs the agent to use
  `request_user_input` (NOT `message_user`).
- [ ] **`AGENTS.md` at the repo root** carries the 5 invariants from A2 §5.
  Per `_jules_reference.md §2`, every Jules dispatch into this repo
  inherits it automatically — no per-prompt boilerplate.
- [ ] **`jules.verify` already uses `vcs.remote_exists`** (Spec 012 Phase 5,
  shipped at commit `6059c74`). This spec re-affirms: never trust local HEAD.

## Design — the skill set

Six intersecting skills. **Chaining via shared hard gates is the canon-aligned
intersection model** (A3 §3, recommended (a); proven by `develop.review.dispatch`
invoking `delegate.fan_out`). One skill's hard gate is the next's precondition;
no new walker support is required.

### 1. `jules-protocol-preamble` (4 phases, 1 hard gate)

```
verify-remote-state   advisory  → produces: remote_head, vcs_clean
name-canonical-tools  advisory  → produces: submit_named, precommit_named, request_user_input_named, replace_diff_named, request_review_named
set-scope             advisory  → produces: affects_paths, no_create_outside
dispatched            HARD GATE → produces: session_id
```

Walked **once per dispatch**. Phase 4's gate is the elicit pause
(`CORE.md:56-60`): walker stays at `input-required` until a real `session_id`
is supplied by the dispatch flow. Phase 1 verifies via a recorded
`git ls-remote` invocation (the `COMPLETED ≠ done` predicate from spec 012).

### 2. `jules-tool-discipline` (5 phases, advisory)

```
plan-named               → produces: set_plan_named, request_plan_review_named
edit-discipline-named    → produces: replace_with_git_merge_diff_named
verify-named             → produces: read_file_list_files_before_advance_named
review-named             → produces: request_code_review_named
publish-named            → produces: pre_commit_instructions_named, submit_named
```

Walked when a `dispatch` preamble is composed. Each phase records that the
named tool is present in the prompt being assembled. Produces are simple
booleans validated at `submit()`; no run-time work — pure prompt-assembly
discipline.

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

### `jules.dispatch` — 3 new pass-through args

```python
@verb(role="effect")
def dispatch(self, source, starting_branch, prompt,
             title="", require_plan_approval=True, auto_create_pr=False,
             alias="",
             # NEW (spec 013):
             automation_mode="",      # "" | "AUTO_CREATE_PR"; lift to top of API call
             protocol_preset="",      # named preamble bundle; see registry below
             agents_md_path="") -> dict:
```

- `automation_mode` maps directly to the Jules API's `automationMode`
  field (`_jules_reference.md §4`). Distinct from `auto_create_pr` —
  that's the boolean shape we already had; this is the canonical name.
- `protocol_preset` looks up the canonical preamble + tool-discipline
  text from the registry (below) and prepends it to `prompt`. The
  ~700-token boilerplate (A2 §4) is paid **once at registry definition**,
  not per dispatch.
- `agents_md_path` (optional) writes an `AGENTS.md` into the source repo
  at the named path if it does not already exist — useful for one-shot
  spec-locked sessions; usually unset because the **repo-root `AGENTS.md`
  is committed permanently** (next section).

### `agency/capabilities/_jules_preambles.py` — the recipe registry

Module-level dict:

```python
PRESETS: dict[str, str] = {
    "agency-default": _AGENCY_DEFAULT_PREAMBLE,  # 5 invariants + must-name set
    "research-pass":  _RESEARCH_PASS_PREAMBLE,   # read-only research dispatch
    "code-edit":      _CODE_EDIT_PREAMBLE,       # TDD + submit + review
}
```

Each preamble names the must-name tools (A1 §2) and the 5 operational
invariants (A2 §5). Underscore-prefixed file: skipped by capability
discovery; consumed lazily by `_jules_api.jules_create` when
`protocol_preset` is non-empty.

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

## Design — `AGENTS.md` at the repo root

Per `_jules_reference.md §2`, an `AGENTS.md` at the repo root is a
**localised overriding system prompt** scoped to the entire directory
tree from its location. Every Jules dispatch into `netzkontrast/agency`
inherits it without us re-pasting boilerplate.

Content (≤ 60 lines): the 5 invariants from A2 §5, the must-name tool
list from A1 §2, the conventional-commits rule, `pytest -q` as the
verification command, and one line each on `replace_with_git_merge_diff`,
`request_user_input`-vs-`message_user`, the silent-fail diagnostic, and
the `git ls-remote` verification step.

This is the *single highest-leverage* artefact in the whole design:
written once, inherited by every future Jules dispatch.

## Files

- **Create**:
  - `AGENTS.md` (repo root) — the inheritable agency-wide system prompt.
  - `agency/capabilities/_jules_preambles.py` — the recipe registry +
    canonical text constants.
  - `agency/capabilities/_jules_skills.py` (or extend `ontology.skills` in
    `jules.py`) — the six skill definitions.
  - `tests/test_jules_skills.py` — every skill walks end to end on a
    `StubJulesClient` + `StubVCS`; gates pause/resume correctly; preamble
    text shows up in the assembled prompt.
  - `Plan/013-…/REVIEW.md` (Phase C output).
- **Modify**:
  - `agency/capabilities/jules.py` — extend `dispatch` with the three new
    pass-through args; extend `JulesCapability.ontology.skills` to register
    the six skills.
  - `agency/capabilities/_jules_api.py` — `jules_create` accepts
    `automation_mode` and prepends the resolved preset to the prompt
    when `protocol_preset` is set.
  - `Plan/012-…/spec.md` — fold the `INSTRUCTIONS` table update into the
    spec's WatchEvent design (Phase 7 of spec 012's IMPLEMENTATION-PLAN
    will pick it up).

## Open Questions / for the spec-panel

1. **`automation_mode` default.** The agency-driving-Jules pattern wants
   `AUTO_CREATE_PR` (A2 §2; eliminates the publish-confirmation pause
   that caused half of our PR #2/#3/#4/#5 round noise). Interactive
   workflows want manual confirm. **Recommend default `""`** (opt-in via
   the new dispatch arg); maintainer confirms before Phase E.
2. **Preset registry vs per-dispatch arg.** This design ships both —
   registry + override. Panel: is the registry over-engineered for v1,
   or is the override under-engineered for spec-driven dispatch?
3. **The intersection model.** A3 recommended `develop`-style chaining
   via shared hard gates. Panel confirms or proposes (b) shared-by-name
   (walker has no support today; needs a feature) or (c) meta-skill.
4. **AGENTS.md scope.** This design commits a *root-level* `AGENTS.md`.
   Should there also be a nested `agency/AGENTS.md` (Python-specific
   conventions: ruff/black/mypy/pytest discipline) that the lexical
   scoping mechanism (`_jules_reference.md §2`) would let override the
   root for source edits?
5. **Jules `inspect_and_resume` semantics.** Spec 012's table says
   PAUSED. The reference doc says PAUSED is "manually suspended"
   (`§4 state machine`). Is `inspect_and_resume` the right action there,
   or should the watcher emit `answer_agent_question` with the last
   activity-stream content?
6. **Token budget for `INSTRUCTIONS`.** Spec 012 caps templates at 280
   chars. With Jules-tool naming, several entries grow to ~480 chars.
   Relax to 480? Or keep 280 + add a `tools_needed:[…]` field the
   instruction renders by reference?

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
- `Plan/012-jules-complete-lifecycle-and-watcher/spec.md` — the
  `INSTRUCTIONS` table this design updates; the watcher's `recover`
  flow that consumes the new skills.
- `Plan/012-…/DOGFOOD-NOTES.md:77-85, 148-149` — live evidence of the
  silent-fail this design closes.
