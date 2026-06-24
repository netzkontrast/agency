# Implementation Plan — Spec 013 (Jules skills + capability improvements)

TDD-first, phased, with a clean commit + green pytest gate per phase.
Each phase is independently revertable; the order minimises rework.
Mirror of Spec 012's plan shape; "us vs Jules" boundary called per phase.
Spec 001's `ToolResult` envelope is live; new verbs return through it
unchanged (engine unwraps `.data`).

## Phases

| # | Phase | Files | Notes | Boundary |
|---|---|---|---|---|
| **1** | **Doctrine docs at repo root** | `AGENTS.md` (extend) · `AGENCY_PROTOCOL.md` (new) | Highest-leverage artefact pair. Cuts ~580 tokens / dispatch (preamble 700 → 120) per the DESIGN split-ownership table. No `Plan/JULES_PROTOCOL.md` exists in this repo (lived in the-agency-system reference) — Phase 1 simplifies to "create both root docs fresh". RED: `tests/test_doctrine_docs.py` asserts both files exist + name every must-name tool + carry the silent-fail guard. **[SHIPPED — commit `9d6828f`.]** | **Us, inline.** |
| 2 | **Preamble + Mode A/B assembler** | `agency/capabilities/_jules_preambles.py` (new) · `tests/test_jules_preambles.py` (new) | Single `PREAMBLE` constant + `assemble(source, starting_branch, prompt, preset_name="agency-default")`. Branches Mode A (`source == DISPATCH_SELF_SOURCE`) vs Mode B (explicit clone instruction). Includes `lint_must_name(text, must_name=[…])` for Phase 3. Added in revision: `REVIEW_COMMENT_TAIL` + `review_comment(body)` helpers (AGENCY_PROTOCOL.md §9 handshake). **[SHIPPED — commits `91e6199`, extended by the §9 handshake commit.]** | **Us, inline.** |
| 3 | **`jules.lint_prompt` + `jules.review_comment` verbs** | `agency/capabilities/jules.py` · `tests/test_jules_lint_prompt.py` (new) | `lint_prompt(text, must_name="")` is the predicate; symmetric with `plugin.lint_skill`. `review_comment(body)` composes any `@jules` review with the mandatory §9 tail (idempotent). **[SHIPPED — commit `4ddaee8`, extended by the §9 commit.]** | **Us, inline.** |
| 4 | **`jules.dispatch` arg extension + deprecation alias** | `agency/capabilities/jules.py` (extend `dispatch` signature) · `agency/capabilities/_jules_api.py` (extend `jules_create` to forward `automationMode` + prepend assembled preamble) · `tests/test_agency.py` (extend dispatch tests for matrix) | Two new pass-through args: `automation_mode=""` (`"" \| "AUTO_CREATE_PR"`) and `protocol_preset=""`. `auto_create_pr=True` becomes a back-compat alias that maps to `automation_mode="AUTO_CREATE_PR"` and emits a `DeprecationWarning` once per process. Wire the Flag Interaction Matrix from DESIGN.md (4 cells). When `protocol_preset` non-empty, `_jules_api.jules_create` calls `_jules_preambles.assemble(...)` and prepends to `prompt`. | **Us, inline** (touches contract; downstream phases depend). |
| 5 | **Skill 1: `jules-protocol-preamble`** | `agency/capabilities/_jules_skills.py` (new) or extend `JulesCapability.ontology.skills` · `tests/test_jules_skills_preamble.py` (new) | 5 phases (`detect-mode` advisory · `verify-remote-state` advisory bound to `jules.verify` · `name-canonical-tools` advisory bound to `jules.lint_prompt` · `set-scope` advisory · `dispatched` HARD GATE). RED: walking with `mode="delegate"` produces an `agency_clone_ro_in_delegate=True` flag in the artefact; HARD GATE pauses until `session_id` is supplied. GREEN: `Phase.invoke` bindings consume Phases 2+3 verbs. | **Us, inline** (not context-heavy — see §9a heuristic). |
| 6 | **Skill 2: `jules-tool-discipline` (collapsed)** | Same file · `tests/test_jules_skills_tool_discipline.py` | 1 advisory phase `apply-tool-discipline` bound to `jules.lint_prompt`. Reusable from inside skill 5. RED: a draft prompt missing `submit` → `lint_result.ok=False`. | **Us, inline** (trivial). |
| 7 | **Skill 3: `jules-recovery-when-stuck`** | Same file · `tests/test_jules_skills_recovery.py` | 4 phases (`classify-state` · `probe-once` · `patch-or-empty` · `recovered` HARD GATE). Bindings: `jules.status` + `jules.verify` + `jules.message` + `jules.patch`. RED: probing a session where `verify` says `branch_on_remote=False` and `patch` says `bytes=0` → walker pauses on `recovered` with `pr_url=""`. | **Us, inline** (verb shapes already loaded). |
| 8 | **Skill 4: `jules-pr-review-cycle`** | Same file · `tests/test_jules_skills_pr_review.py` | 3 advisory phases composing the GitHub MCP read/reply path. `draft-replies` calls `jules.review_comment` so every reply ships with the §9 handshake tail. RED: walking through bindings produces `posted=True` only when both `comments` and `replies` are non-empty AND each reply contains `reply_to_pr_comments`. | **Us, inline.** |
| 9 | **Skill 5: `jules-fanout`** | Same file · `tests/test_jules_skills_fanout.py` | 3 phases (`plan-batch` · `fan-out` bound to `delegate.fan_out(driver="jules")` · `join` HARD GATE). RED: HARD GATE pauses until all `child_sessions` resolve to outcomes. | **Us, inline.** |
| 10 | **Skill 6: `jules-self-improvement`** | Same file · `tests/test_jules_skills_self_improvement.py` | 2 advisory phases. `collect-dogfood` reads from `Plan/**/DOGFOOD-NOTES.md`; `fold-into-spec` binds to `reflect.note(scope="dogfood")` → produces `Reflection` nodes. RED: a fixture DOGFOOD note with N observations produces N `Reflection` nodes. | **Us, inline.** |
| 11 | **Spec 012 `INSTRUCTIONS` table update** | `agency/capabilities/_jules_watch.py` (the file from Spec 012 Phase 6 once PR #8 merges) · `tests/test_jules_watch.py` (update the per-WatchAction instruction asserts) | Replace 280-char templates with the WatchAction → tool-naming map from DESIGN.md `## Design — capability deltas → INSTRUCTIONS update`. Cap relaxes to 480 chars / ≤ 120 tokens. RED: assertion that `INSTRUCTIONS[WatchAction.recover_silent_fail]` literally contains `"submit("` and `"pre_commit_instructions"`. | **Us, inline** (after PR #8 lands). |
| 12 | **Regenerate install + dogfood ledger entry** | `python -m agency.install` (auto) + `Plan/013-…/DOGFOOD-NOTES.md` (new) | The `help` skill picks up `lint_prompt` + `review_comment` + the six new skills; `test_agency_plugin_install_is_self_hosted` stays green. Open a `DOGFOOD-NOTES.md` for spec 013 the way Spec 012 did. | **Us, inline.** |

**Per-phase gate:** RED test → GREEN implementation → `pytest -q` all green
→ commit + push. No phase merges until its tests pass. Skills (phases 5-10)
each get a fixture file under `tests/fixtures/jules_skills/` with the
canonical dispatch shape + the expected walked artefact.

## Dispatch options

**Revised per the `delegate.dispatch-decision` skill (the dispatch-vs-inline
heuristic was moved out of `AGENCY_PROTOCOL.md` and into a walkable skill on
the `delegate` capability where it belongs — orchestrator decision-making,
not agent doctrine):** none of phases 5-10 individually meets the
"context-heavy" bar — each
needs to read 1-2 verb signatures + the existing skill exemplar
(`develop.py` / `music.py`), which the orchestrator already has in its
window. Dispatching them would pay ~700 tokens of preamble + review-cycle
overhead per skill for ~50-100 lines of clear greenfield writing.
**Default: ship inline, sequential 1→12.**

The Jules path becomes attractive if phases 5-10 are taken as a single
**bundled dispatch** (one Jules session lands all six skills together)
— amortises preamble across 6 outputs and gives Jules a context-heavy
brief (read 4 verbs + 2 exemplars + write 6 skills + 6 test files).
That bundle qualifies under §9a's "≥ 4 files to read" criterion.

- **Sequential inline (default, lowest overhead):**
  1 ✓ → 2 ✓ → 3 ✓ → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12.
- **Bundled Jules dispatch (alternative for skills 5-10):**
  1 ✓ → 2 ✓ → 3 ✓ → 4 inline → **one** Jules session for skills 5-10
  → 11 → 12 inline. Dispatch prompt includes the bash hints below.
- **Parallel-safe-pair dispatch (highest overhead, only if 4 humans
  babysit):** as originally planned; pays the per-skill cost six times.

## Mode-A/B dogfood loop (the spec-013 dogfood story)

If Spec 013 itself is implemented via Jules-dispatched phases, those
dispatches **must use Mode A** (`source == "netzkontrast/agency"`). The
preamble's clone block doesn't fire; AGENTS.md + AGENCY_PROTOCOL.md are
inherited via Jules's lexical scoping. This is the canonical dogfood: the
agency uses its own doctrine to build the doctrine-shipping spec.

Mode-B coverage is achieved by a single integration test in Phase 12 that
dispatches a stub-clients session with `source="somebody-else/whatever"`,
asserts the assembled prompt contains the clone block, and verifies the
preamble's pointer line points at the right paths.

## Bundled Jules dispatch prompt — bash-hint pattern

Per `delegate.dispatch_bash_hints` (and the `dispatch-decision` skill's
Phase 3): if skills 5-10 are dispatched as a single bundle, the prompt
MUST hand Jules the bash commands that surface the right context —
cheap on orchestrator tokens, fast for Jules:

```
Context — read these first, in this order:

# 1. The verb signatures the skills bind to:
grep -n '@verb' agency/capabilities/jules.py | head -30

# 2. The two skill exemplars:
sed -n '1,80p' agency/capabilities/develop.py        # invoke-binding pattern
sed -n '20,50p' agency/examples/music.py             # gated-skill exemplar

# 3. The skill walker (one phase at a time):
sed -n '1,90p' agency/skill.py

# 4. The OntologyExtension shape:
grep -n 'OntologyExtension\|ontology.skills' agency/capabilities/develop.py

# 5. The Spec 013 design — the six skills to implement (skim only):
sed -n '/^### 1. /,/^## Design — capability/p' \
  Plan/inprogress/013-jules-skills-and-capability-improvements/DESIGN.md
```

Each skill lands as one commit; test files are independent fixtures
under `tests/fixtures/jules_skills/`. The dispatch's `affects:` is
`{agency/capabilities/_jules_skills.py, tests/test_jules_skills_*.py,
tests/fixtures/jules_skills/**}` — a tight allow-list.

## Per-phase Jules dispatch prompt skeleton (for dispatched phases)

Standardised prompt shape (Phase 5+, when handing off to Jules) — fits the
preset-driven dispatch shape from Phase 4:

```
Source:           netzkontrast/agency
StartingBranch:   claude/extract-agency-plugin-o4JRc
ProtocolPreset:   agency-default     # → Mode A; AGENTS.md inherited
AutomationMode:   AUTO_CREATE_PR     # opt-in per matrix (zero-touch)
RequirePlanApproval: True            # plan-gated default

Task:
  - Implement Skill N (`jules-…`) per Spec 013 IMPLEMENTATION-PLAN.md
    Phase <N> (see Plan/013-…/IMPLEMENTATION-PLAN.md).
  - RED: write tests/test_jules_skills_<name>.py asserting the gated
    walk shape from DESIGN.md `## Design — the skill set` skill N.
  - GREEN: extend `JulesCapability.ontology.skills` (in
    `agency/capabilities/_jules_skills.py` or jules.py) with the skill.
  - Verify locally: `pytest -q tests/test_jules_skills_<name>.py`.

Affects (allow-list, hard scope gate):
  - agency/capabilities/_jules_skills.py
  - tests/test_jules_skills_<name>.py
  - tests/fixtures/jules_skills/<name>.py

Submit:
  - Run pre_commit_instructions() first.
  - Then submit(
      branch_name="jules-skill-<name>",
      commit_message="feat(jules): Skill N — jules-<name>",
      title="feat(jules): Skill N — jules-<name>",
      description="Implements Spec 013 Phase N (skill jules-<name>).",
    )
  - Verify via git ls-remote that the branch is on origin BEFORE
    declaring done. COMPLETED ≠ done.

If blocked:
  - Use request_user_input (NOT message_user) — one question at a time.
  - If anything is outside the Affects allow-list above, emit a BLOCKED:
    PR and stop.
```

The preamble carries the must-name tools + the pointer line; the dispatch
prompt above carries scope + acceptance + the explicit submit literal.

## Parking lot (out of v1 scope; track for follow-on)

- **AGENTS.md scope nesting** (Open Question 2 from DESIGN.md) — revisit
  if Python-style conventions diverge between subtrees.
- **Mode-A/B fork detection** (Open Question 1a) — v1 ships the
  configurable `agency.dispatch_self_source` toggle; smart-fork detection
  via default-branch ancestry is a v2 enhancement.
- **`agency.dispatch_protocol_source_url` configurability** (Open
  Question 1b) — v1 hardcodes the public GitHub URL; v2 lets private
  mirrors override.
- **Multi-preset registry** (originally OQ2; deferred per panel) — add a
  second preset only when a real distinct caller materialises.
- **`jules-self-improvement` auto-fold-back** — Phase 10 records
  `Reflection` nodes; promoting them to design deltas in DESIGN.md
  remains a human/orchestrator step in v1.

## Provenance

- `Plan/013-…/spec.md` — the process spec that authorised this plan.
- `Plan/013-…/DESIGN.md` (Phase D refinement) — the design this plan
  implements.
- `Plan/013-…/REVIEW.md` — the Phase C spec-panel verdict; must-fixes
  are folded into the phase-by-phase RED tests above.
- `Plan/012-…/IMPLEMENTATION-PLAN.md` — the structural template this
  mirrors.
- `agency/capabilities/_jules_reference.md` §2 (lexical scoping), §3
  (tool catalogue), §7 (operational implications) — the ground truth
  the doctrine docs in Phase 1 quote.
