# Spec 013 — REVIEW.md (Phase C)

Spec-panel review of `DESIGN.md` (Phase B). Three orthogonal axes: **vision
canon**, **source faithfulness**, **implementability**. Evidence-cited.

---

## Verdict

**Aligned with one needs-reframe (the recipe registry) + a tight list of
source-faithfulness corrections.** No multiplication of primitives; the six
skills compile cleanly into `OntologyExtension.skills`; the three dispatch
deltas slot onto the existing verb surface without a walker change; the
`AGENTS.md` placement is the single highest-leverage artefact (CORE.md:55,
_jules_reference.md §2). The biggest watch-out is **over-engineering the
preset registry** — A2 §5 lists exactly **one** canonical preamble; shipping a
three-preset dict at v1 is speculative and burns the token-efficiency win the
design itself claims.

---

## Vision-alignment findings

1. **No new top-level concept; no new role-tag.** The six skills are
   `Lifecycle` templates per CORE.md:47-62 ("a skill is **not** a monolithic
   `SKILL.md` … a Lifecycle template: a graph of atomic Capability steps +
   Gates"). The three dispatch deltas are pass-through args on an existing
   `effect` verb — no new node, no new edge, no new enum. Matches the
   "few primitives" verdict (CLUSTERS:26-43): "Most clusters are facets of
   the four concepts."

2. **Skill IS a capability, properly.** Per CORE.md:47-54 the chain mirrors
   itself into provenance via `call_tool` recording Invocations; each skill's
   `invoke`-bound phases (e.g. `jules-recovery-when-stuck` binding
   `jules.status`/`message`/`patch`) make this real. Good.

3. **Gates via `elicit` is preserved.** Each hard gate documented in §`Design
   — the skill set` is an `elicit` per CORE.md:56-60 ("askuser is therefore
   not a special case — it is one node in the chain"). The walker's
   `submit(confirmed=True)` (`skill.py:71-72`) supplies the resume. ✓

4. **Capability-owned ontology is honoured.** Per CORE.md:131-133 each
   capability contributes its own skills via `OntologyExtension.skills`. The
   design extends `JulesCapability.ontology.skills` — exactly the contract
   `develop.py:127` exercises (`OntologyExtension(skills=dict(DEV_SKILLS))`).

5. **One concern with `jules-self-improvement`.** This skill's "fold dogfood
   notes into reflections" overlaps the `reflect` capability already shipped
   (CLUSTERS:14, CLAUDE.md `reflect`). The skill is the *composition*, not a
   new primitive, so it's still canon-aligned — but the design must make
   crisp that Phase 2's `invoke: reflect.note` is the actual mechanism, not a
   re-implementation. Minor — flag for refinement, not blocking.

**No multiplication-of-primitives found.** The design fits the four-concepts
model cleanly.

---

## Source-faithfulness corrections

Cited against `_jules_reference.md` (the architectural ground truth).

1. **`jules-tool-discipline` Phase 1 should include `record_user_approval_for_plan`
   too** — `_jules_reference.md §3b` lists it as a separate state-machine
   tool. The draft enumerates `set_plan`, `request_plan_review`; adding
   `record_user_approval_for_plan` mirrors the plan trio. (Low-impact —
   record-only, but completeness for the "name the tools" promise.)

2. **`replace_with_git_merge_diff` is a Special-tool / DSL**, not a Standard
   tool (_jules_reference.md §3f). The design's `jules-tool-discipline`
   `edit-discipline-named` phase is correct in spirit, but the AGENTS.md +
   any preamble text MUST flag this is DSL syntax (tool name on line 1, raw
   args after) — otherwise the agent may try Python-call form and fail. Add
   one explicit example to the AGENTS.md (the design says "one line each on
   `replace_with_git_merge_diff`" — extend it to a 4-line DSL snippet).

3. **`recover_silent_fail` table row — `submit` signature.** The design's
   table cell ("`pre_commit_instructions()` → `submit(branch, commit_message,
   title, description)`") matches `_jules_reference.md §3c` exactly. ✓

4. **`answer_agent_question` row — correct.** `request_user_input` is the
   blocking primitive (_jules_reference.md §3e: "the **dedicated blocking
   tool** for clarification / scope escalation"). The "NOT `message_user`"
   parenthetical lands the §3e prohibition. ✓

5. **State-machine value drift in OQ5.** The design says "Jules
   `inspect_and_resume` semantics. Spec 012's table says PAUSED." Cross-check:
   `_jules_reference.md §4` enumerates PAUSED as a terminal-ish state in
   the state machine `… → COMPLETED | FAILED | PAUSED | CANCELLED`. The
   reference does NOT say "manually suspended" anywhere — the draft mis-
   characterises it. Recommend the answer in §"Open-Questions triage"
   below.

6. **MCP allow-list.** §6 of the reference is explicit: Linear, Stitch,
   Neon, Tinybird, Context7, Supabase — closed. The design correctly does
   NOT propose Jules calls an agency MCP; the GitHub MCP work in
   `jules-pr-review-cycle` is agency-side, not Jules-side. ✓ (Make this
   explicit in the AGENTS.md so the agent inside Jules doesn't try to
   call our MCP.)

7. **`automationMode` field name.** The Jules API field is `automationMode`
   (camelCase per `_jules_reference.md §4`); the design's
   `automation_mode=""` Python arg is correct, but `_jules_api.jules_create`
   must serialise to the camelCase JSON key. Worth one explicit sentence in
   the design.

8. **Activity types claim in `_jules_reference.md` §4.** The reference
   lists `PlanGenerated, PlanApproved, UserMessaged, AgentMessaged,
   ProgressUpdated, SessionCompleted, SessionFailed, CodeChanges, BashOutput,
   Media`. The design does not enumerate these explicitly; spec 012's
   `_classify` only references `agentMessaged`/`planGenerated`. The
   richer taxonomy (esp. `CodeChanges`, `BashOutput`) is a spec-012 concern
   the operational research (A2) flags as orbital. Not a 013 bug — but the
   spec-012 INSTRUCTIONS-table update §should at minimum mention that
   `CodeChanges` is now the canonical signal a `submit` happened, so the
   watcher can stop guessing "did submit get called?"

---

## Implementability findings

Cited against the live code paths.

1. **Skill schema compiles cleanly** — `agency/skill.py:40-46`'s
   `current()` returns `{index, name, produces, inputs, gate}`; each of the
   six skills in the design uses exactly these fields. The `_phase(idx, name,
   produces, gate=...)` helper from `develop.py:21-25` is reusable verbatim
   for `jules-*` skills. ✓

2. **`invoke` binding is sound** — `agency/skill.py:60-67` shows the
   `{"capability": "...", "verb": "..."}` shape; `inputs` are pulled from
   the prior phase's outputs. Each `invoke:` cited in the design (e.g.
   `jules-recovery-when-stuck`'s `jules.patch` invocation, `jules-fanout`'s
   `delegate.fan_out` invocation, `jules-self-improvement`'s `reflect.note`)
   compiles directly. ✓

3. **Hard-gate pause/resume works as designed** — `skill.py:71-72`. No
   walker change needed for the "chaining via shared hard gates" model. ✓
   (BUT — see Watch-out below: `skill.py:71-72` does NOT yet persist a
   `Gate{passed:False, paused:True}` node; DOGFOOD-NOTES.md:131-137 flags
   this as Codex C3, deferred. The 013 skills won't have provenance for
   their pause states until C3 lands. Not a blocker for 013 — but the
   design should call this dependency out.)

4. **`OntologyExtension.skills` collision rule** — `ontology.py:114-117`
   raises on duplicate skill names. The six `jules-*` names don't collide
   with `DEV_SKILLS` (`brainstorm`, `plan`, `tdd`, `debug`, `verify`,
   `spec-panel`, `review`, `execute`) or `ALBUM_CONCEPT_SKILL`
   (`album-concept`). ✓ Recommend naming check be added to
   `tests/test_jules_skills.py` to lock this.

5. **Three new dispatch args fit cleanly** — `jules.py:152-190` is the
   only call site; the API client (`_jules_api.jules_create`) needs the
   matching kwargs added. **Watch out:** the existing dispatch already
   defaults `require_plan_approval=True` (line 154); the design's
   `automation_mode=""` and the existing `auto_create_pr=False` BOTH influence
   what happens at submission time. The relationship needs an explicit table:

   | `require_plan_approval` | `auto_create_pr` | `automation_mode` | Effect |
   |---|---|---|---|
   | True (default) | False (default) | "" (default) | manual: approve plan, approve PR |
   | True | True | "" | manual approve plan, auto-PR |
   | False | * | `AUTO_CREATE_PR` | zero-touch end to end |

   Without this, the two booleans + the mode-string create a 6-way space
   the agent has no doctrine for.

6. **`_jules_preambles.py` as the recipe registry** — module is fine
   structurally; the underscore-prefix correctly opts out of capability
   discovery (matches `_jules_api.py`, `_jules_watch.py`, `_jules_reference.md`
   convention). Per A2 §4 the prompt cost is ~700 tokens — paying that once
   at registry definition is a real win. **BUT see Watch-out: ship ONE
   preset, not three.**

7. **`agents_md_path` write semantics.** The design says "writes an
   `AGENTS.md` into the source repo at the named path if it does not already
   exist." Implementability question: the source repo lives inside Jules's
   VM, not our filesystem. The only way the agency writes to it is by
   prepending `AGENTS.md` content into the prompt itself (or by committing
   to GitHub via the GitHub MCP before dispatch). The design is fuzzy here.
   Recommend: **drop `agents_md_path` from the v1 dispatch surface** — the
   root `AGENTS.md` is committed once via a normal PR, and any per-dispatch
   override is just the `protocol_preset` text. Re-add later if a per-
   dispatch override proves necessary.

---

## Skill-shape critique (per skill)

### 1. `jules-protocol-preamble` (4 phases)

- **Phase 1 `verify-remote-state`** — bind to `jules.verify` (already shipped
  per spec 012 Phase 5 / commit `6059c74`). The design says "advisory" with
  `produces: remote_head, vcs_clean`; recommend an explicit
  `invoke: {capability: jules, verb: verify}` and `produces: branch_on_remote`
  (the field `jules.verify` actually returns per `jules.py:261`). The draft's
  `remote_head`/`vcs_clean` are invented field names — not in the verb's
  return.
- **Phase 4 `dispatched` hard gate** — sound. The elicit resumes with
  `confirmed=True` carrying the `session_id`. Matches `skill.py:71-72`. ✓

### 2. `jules-tool-discipline` (5 phases, advisory)

- All five phases are "naming verifications" producing boolean fields. This is
  borderline-tautological — the `produces` are simply "was this string in the
  prompt?" which the walker can't actually verify without a predicate. **Reframe
  recommendation:** make this skill a single advisory phase that `invoke`s a
  small `jules.lint_prompt(prompt: str) → {missing_tools: list[str]}` verb
  (new transform verb on the jules capability), and the phase passes when
  `missing_tools == []`. That gives the discipline real teeth.

### 3. `jules-recovery-when-stuck` (4 phases)

- Bindings (`jules.status` Phase 1, `jules.message` Phase 2, `jules.patch`
  Phase 3) are correct. Phase 4's hard gate waiting for `pr_url` is sound.
- The `branch_on_remote` field in Phase 1 produces — should come from
  `jules.verify` not `jules.status` (the verify verb is the one that
  independently derives it; `status` returns the state shape).

### 4. `jules-pr-review-cycle` (3 phases, advisory)

- The design says it uses GitHub MCP (`mcp__github__list_review_comments`
  and `mcp__github__add_reply_to_pull_request_comment`). But the agency's
  skill walker can only `invoke` capability verbs, not external MCP
  tools directly (`skill.py:60-67`). **This skill needs an agency-side
  `github` capability** with `list_review_comments`/`add_reply` verbs, OR
  the skill needs to be document-phase only with the agent expected to call
  the GitHub MCP itself. Make this explicit in the refinement.

### 5. `jules-fanout` (3 phases)

- Direct mirror of `develop.review.dispatch`'s `delegate.fan_out` binding
  (`develop.py:65-71`). ✓ Clean.

### 6. `jules-self-improvement` (2 phases)

- Phase 2's `invoke: reflect.note` is canon-aligned. ✓ But the design
  doesn't name the Phase 1 mechanism — how are "dogfood observations"
  *gathered*? The DOGFOOD-NOTES.md file is just markdown today. Phase 1
  could `invoke: reflect.search` over an "in-flight-spec" scope tag, but the
  design must say so. Otherwise this skill stops at "vibes."

---

## Capability-delta critique

### `automation_mode`

- Maps cleanly to API `automationMode` (camelCase serialization, per §6
  faithfulness above). ✓
- Default `""` (opt-in) is the right call per the in-flight Phase 4/6
  silent-fail experience — flipping to AUTO_CREATE_PR by default would
  *amplify* the silent-fail blast radius (no human checkpoint between
  "submit" and "PR created" means a wrong-scope diff lands directly).
- **The relationship with `auto_create_pr` must be specified.** Both
  pre-exist + ride alongside; the table I gave under "Implementability" §5
  is the minimum doctrine.

### `protocol_preset`

- The mechanism (look up + prepend) is sound, and the token economics
  argument (pay 700 tokens once) is real per A2 §4.
- **Ship ONE preset for v1.** A2 §5 lists exactly five invariants — that's
  the canonical preamble. The `research-pass` and `code-edit` presets in
  the design's example dict are unmotivated by source research; they're
  speculative.

### `agents_md_path`

- See Implementability §7. **Recommend dropping from v1.** The committed
  root `AGENTS.md` covers the case; the `protocol_preset` covers the
  per-dispatch override case; there is no third case A2 surfaces.

---

## Token-efficiency / prompt-engineering critique

The spec-012 design promises "tailored, token-efficient, clear-and-complete
instruction" (spec.md:36-37) and caps `instruction` strings at 280 chars
(spec.md:142, 163).

1. **The 280 → 480 char relax in the design is justified — barely.** The
   spec-012 budget was set BEFORE Jules-tool naming was on the table. The
   four entries that grow most are `recover_silent_fail`, `dispatch_fresh`,
   `verify_pr`, `inspect_and_resume`. Each needs ~150 chars of tool naming
   ("call `pre_commit_instructions()` then `submit(branch, …)`"). 480 still
   yields ≤ 120 tokens per event (the spec's stated budget). Acceptable.

2. **Better alternative: structured `tools_needed` field.** Keep
   `instruction` at 280 chars (purpose) + add a `tools_needed: list[str]`
   field carrying the tool names. The agent's harness can render the names
   into the instruction at point-of-use, and the event payload stays lean.
   **Recommend OQ6 resolves as "add `tools_needed`, keep 280," not
   "relax to 480."**

3. **The committed root `AGENTS.md` is the single biggest token win.** Per
   A2 §4 the preamble is ~700 tokens; the design rightly observes this is
   paid ONCE if AGENTS.md is committed (every dispatch inherits per
   _jules_reference.md §2). This is correct and high-leverage.

4. **`protocol_preset` and AGENTS.md overlap.** If AGENTS.md covers the 5
   invariants, the preset's job shrinks to "must-name tool list" — a much
   smaller string (~200 tokens, not 700). The design implicitly assumes
   they don't overlap; in practice they will. Recommend the refinement
   nail down what AGENTS.md owns vs what the preset owns.

5. **"Tailored" check.** Per-action templates (the design's table) are
   action-specific and carry concrete tool names. That meets "tailored." ✓

6. **"Clear-and-complete" check.** The `recover_silent_fail` cell —
   "**`pre_commit_instructions()` → `submit(branch, commit_message, title,
   description)`**" — is clear (names the canonical missed pair) and
   complete (full `submit` signature, no implicit args). ✓

---

## Open-Questions triage

| OQ | Status | Recommendation |
|---|---|---|
| 1 (automation_mode default) | **Resolved by source.** | A2 §2 + _jules_reference.md §7 bullet 3 both name `AUTO_CREATE_PR` for the agency-driving-Jules pattern but FLAG the cost ("removes the only built-in pause point"). Keep default `""` (opt-in); document the recommendation in the docstring. |
| 2 (registry vs override) | **Partially answered.** | Ship the registry (1 preset), drop `agents_md_path` per Implementability §7. The override case is the preset itself. |
| 3 (intersection model) | **Resolved by source (A3 §3).** | A3 recommends (a) `develop`-style chaining; the walker has no name-keyed gate registry (`skill.py:24-86`); a meta-skill adds indirection. **Decision: (a).** |
| 4 (nested AGENTS.md) | **Reasonable defer.** | Root AGENTS.md first; nested `agency/AGENTS.md` only if v1 surfaces a Python-specific need. Track as Phase E follow-up, not v1 blocker. |
| 5 (PAUSED semantics) | **Source-faithfulness gap.** | `_jules_reference.md §4` does NOT define PAUSED as "manually suspended" — the draft mischaracterises. Per the state machine `… → COMPLETED \| FAILED \| PAUSED \| CANCELLED`, PAUSED is one of four terminals. Recommend: treat PAUSED as `inspect_and_resume` (i.e. read activities, then `message` to nudge) — the spec-012 table is correct as-is. |
| 6 (token budget) | **Resolve as: add `tools_needed` field, keep 280.** | See Token-Efficiency §2. |

**Net: of 6 OQs, 4 are resolved by the source/canon; 2 (registry size,
nested AGENTS.md) need the refinement pass to nail down.**

---

## Must-fix list for Phase D refinement (ranked)

1. **Cut the preset registry to ONE preset (`agency-default`).**
   `research-pass` and `code-edit` are unmotivated by A2; shipping them is
   speculative and undermines the "token win" claim by spreading the
   doctrine. (Vision: avoids primitive-multiplication via configuration.)

2. **Drop `agents_md_path` from the v1 dispatch surface.** The committed
   root `AGENTS.md` + `protocol_preset` cover every case A2 surfaces;
   `agents_md_path`'s write semantics are fuzzy (we don't have write
   access to Jules's VM filesystem from the dispatch side). Re-add when
   a concrete need appears.

3. **Specify the `automation_mode` × `auto_create_pr` ×
   `require_plan_approval` interaction matrix** (table in
   Implementability §5). Without doctrine, the 6-way space is a footgun.

4. **Fix `jules-protocol-preamble` Phase 1 field names.** `remote_head`
   and `vcs_clean` are invented; bind to `jules.verify` and `produces:
   branch_on_remote` to match the actual verb return shape.

5. **Reframe `jules-tool-discipline`.** Either (a) add a real
   `jules.lint_prompt` predicate verb the phases `invoke`, or (b) collapse
   the 5 phases into 1 advisory document phase. Five tautological
   booleans are not a skill.

6. **Resolve OQ6 as "add `tools_needed: list[str]` to WatchEvent,
   keep `instruction` at 280 chars."** Cleaner token economics than
   relaxing to 480; preserves the spec-012 promise.

7. **Make `jules-pr-review-cycle` mechanism explicit.** Either depends
   on a new `github` capability or is a document-only skill that
   prompts the agent to call the GitHub MCP. The current `invoke:
   github.list_review_comments` is not implementable today.

8. **Specify `jules-self-improvement` Phase 1 mechanism.** "Collect
   dogfood" via what? Recommend `invoke: reflect.search(scope=
   "spec-013-inflight")` and define the convention.

9. **Add `record_user_approval_for_plan` to the tool-discipline plan
   trio.** Completeness against `_jules_reference.md §3b`.

10. **AGENTS.md must include a 4-line `replace_with_git_merge_diff`
    DSL example.** Per §3f the syntax is unusual; one line is not
    enough.

11. **Make the `agency-default` preset and AGENTS.md ownership
    explicit and non-overlapping.** Token-efficiency §4: if both
    repeat the 5 invariants, the cost the design promises to pay once
    is paid twice. Suggested split: AGENTS.md = the 5 invariants
    (repo-wide doctrine) + the canonical commands (`pytest -q`,
    `git ls-remote`); preset = the must-name tool list + a one-line
    pointer to AGENTS.md ("see AGENTS.md for repo-wide invariants").

12. **Note the dependency on Codex C3** (`skill.py:71-72` paused-state
    persistence; DOGFOOD-NOTES.md:131-137). Until C3 lands, hard-gate
    pauses in `jules-*` skills won't show in `memory.provenance()`.
    Acknowledge in the design's "known gaps."

---

## Evidence

- DESIGN.md (entire) — reviewed end to end.
- `agency/capabilities/_jules_reference.md` §2-§7 — architectural truth.
- `RESEARCH-tools.md` §1-§4 (A1), `RESEARCH-operational.md` §1-§5 (A2),
  `RESEARCH-skills.md` §1-§5 (A3) — three orthogonal source feeds.
- `docs/vision/CORE.md:47-62` (skills are Lifecycle templates), :56-60
  (gates via elicit), :131-133 (capability-owned ontology).
- `docs/vision/CAPABILITY-CLUSTERS.md:26-43` (few-primitives verdict).
- `Plan/000-overview.md` — post-alignment shape; spec 013 sits cleanly
  in the existing "no net-new top-level capability" pattern.
- `Plan/inprogress/012-jules-complete-lifecycle-and-watcher/spec.md:130-163`
  (WatchEvent table the design updates), DOGFOOD-NOTES.md:77-85,
  131-137, 148-149 (the silent-fail this design closes; the C3
  dependency).
- `agency/capabilities/jules.py:127-336` (the verb surface this design
  extends; ontology extension at 135-147; dispatch at 152-190).
- `agency/capabilities/develop.py:65-71` (the `invoke`-binding precedent),
  :127 (`OntologyExtension(skills=dict(DEV_SKILLS))`).
- `examples/music.py:22-43` (gated-skill exemplar).
- `agency/skill.py:24-86` (the walker contract).
- `agency/ontology.py:60-86, 104-117` (the `OntologyExtension`
  contract; the collision rule the 6 new skills must respect).
