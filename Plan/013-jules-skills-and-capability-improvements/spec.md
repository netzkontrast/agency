---
spec_id: "013"
slug: jules-skills-and-capability-improvements
status: draft
owner: "@agency"
depends_on: ["012"]
affects:
  - agency/capabilities/jules.py
  - agency/capabilities/_jules_api.py
  - agency/capabilities/_jules_reference.md
  - skills/   # one new sub-dir per ported Jules skill (named in Phase B)
source-repos:
  - "agency/capabilities/_jules_reference.md (in-tree authoritative reference)"
  - "https://github.com/netzkontrast/the-agency-system @ Master (operational lessons)"
estimated_jules_sessions: 0   # design only — implementation comes after Phase E
domain: capability
wave: 2
---

# Spec 013 — Jules skills and capability improvements (process spec)

## Why

The agency's `jules` capability covers the v1alpha REST surface (post-spec-012)
but does NOT carry the operational knowledge an agent needs to drive Jules
*reliably end to end*: which Jules tool publishes the work
(`submit(branch_name, commit_message, title, description)`), what
`automationMode` does, when to use `request_user_input` vs `message_user`,
how `replace_with_git_merge_diff` avoids JSON-escape failures, what
`AGENTS.md` scoping implies for the agency repo, etc.

A user-supplied research synthesis (now stored at
`agency/capabilities/_jules_reference.md`) makes this knowledge explicit.
Per the canon **a skill IS a capability** (CORE.md:47-62 — skills are
Lifecycle templates of atomic Capability steps); the right shape for
porting that knowledge is therefore **a set of intersecting skills on the
existing `jules` capability** plus targeted capability improvements,
NOT a new top-level concept.

This spec scaffolds the **established design loop** for that work:
**research → design → spec-panel → refine → implementation plan → TDD**.
It does NOT design the skills or the improvements itself — those are the
deliverables of phases B / D / F below. Per the user: design now,
implement later.

## Done When

- [ ] **Phase A (research)** is complete: parallel subagents have mined the
  reference doc + the current `jules` capability surface + the spec-012
  watcher design + the-agency-system lessons; each returns a tight (≤500-word)
  synthesis. Deliverables: `Plan/013-…/RESEARCH-{tools,operational,skills}.md`.
- [ ] **Phase B (design draft)** lands `Plan/013-…/DESIGN.md` covering:
  - The set of skills to add (with names, scope, and the
    intersecting Lifecycle phases each walks). Initial hypothesis:
    `jules-protocol-preamble`, `jules-tool-discipline`,
    `jules-recovery-when-stuck`, `jules-pr-review-cycle`,
    `jules-fanout`, `jules-self-improvement`; the design pins the real
    set against the research.
  - The capability deltas beyond spec-012 (e.g. `dispatch(automation_mode=)`,
    `dispatch(agents_md=)`, `recovery.use_submit` enforcement,
    `replace_with_git_merge_diff` suggestion in instruction templates,
    a `protocol_preset` arg).
  - The cross-cutting hooks into spec 012 (the WatchEvent instructions
    naming the right Jules tools so the watcher's auto-recovery actually
    succeeds).
- [ ] **Phase C (spec-panel)** runs a multi-expert review of DESIGN.md
  against (a) the canon (CORE.md, CAPABILITY-CLUSTERS.md), (b) the
  `_jules_reference.md` source, (c) spec 012's existing shape. Lands
  `Plan/013-…/REVIEW.md`.
- [ ] **Phase D (refine)** rewrites `DESIGN.md` per the panel's must-fixes;
  captures resolved questions in the body, leaves only true blockers in
  Open Questions.
- [ ] **Phase E (implementation plan)** lands
  `Plan/013-…/IMPLEMENTATION-PLAN.md` mirroring spec 012's structure
  (numbered phases · per-phase files · per-phase tests · parallel-safe
  pair labels). This is where the boundary between "us" and "Jules"
  gets drawn for each phase.
- [ ] **Phase F (TDD execution)** — explicitly OUT OF SCOPE for spec 013;
  begins under a separate intent once the maintainer confirms the
  IMPLEMENTATION-PLAN.

## Design — the process (deliberately not the design itself)

### Phase A — Research (parallel subagents)

Three subagents, each ≤500-word synthesis, all read-only:

| # | Subagent | Source | Output (`Plan/013-…/`) |
|---|---|---|---|
| A1 | **Tool-discipline mining** | `agency/capabilities/_jules_reference.md` §3a–§3f | `RESEARCH-tools.md` — every Standard + Special tool, when to use it, the dispatch-prompt phrasings that name it. Esp. `submit`, `pre_commit_instructions`, `request_user_input`, `replace_with_git_merge_diff`, `request_code_review`. |
| A2 | **Operational lessons mining** | `_jules_reference.md` §2 + §6 + DOGFOOD-NOTES.md + the-agency-system `_lessons-learned/` | `RESEARCH-operational.md` — environment snapshots, AGENTS.md scoping, MCP allow-list (Jules→external, not us→Jules), automation modes, the canonical silent-fail variants and which Jules tool resolves each. |
| A3 | **Skill-shape mining** | `_jules_reference.md` §7 + `CORE.md:47-62` (skills-as-Lifecycle-templates) + `examples/music.py:album-concept` (the existing gated-skill exemplar) | `RESEARCH-skills.md` — the *shape* a Jules skill should take (atomic gated phases, what each phase verifies via `read_file`/`list_files`, where `request_plan_review` belongs); how skills intersect (one skill's gate is another's entry). |

### Phase B — Design draft

I (the orchestrator) synthesize A1/A2/A3 into `DESIGN.md`. Covers the skill
set, the capability deltas, the spec-012 hooks. Skills are Lifecycle
templates — *not* new top-level concepts (canon-aligned).

### Phase C — Spec-panel

A single spec-panel subagent runs the multi-expert review (vision-alignment +
source-faithfulness + implementability), grounded in CORE.md +
CAPABILITY-CLUSTERS.md + `_jules_reference.md` + the existing `jules`
capability code + spec 012.

### Phase D — Refine

I rewrite DESIGN.md per the panel's must-fixes; resolved open questions move
into the body; only true blockers remain in Open Questions.

### Phase E — Implementation plan

Mirrors spec 012's `IMPLEMENTATION-PLAN.md` shape (numbered phases, per-phase
files, per-phase tests, parallel-safe pair labels, "us vs Jules" boundary
per phase). Adds: dispatch-prompt templates that **explicitly name** the
right Jules tools (the lesson from the in-flight Phase 4/6 silent-fail).

### Phase F — TDD execution

Out of scope here. A separate intent under a separate spec dispatch.

## Files

- **Create** (in `Plan/013-jules-skills-and-capability-improvements/`):
  - `RESEARCH-tools.md`, `RESEARCH-operational.md`, `RESEARCH-skills.md`
    (Phase A outputs)
  - `DESIGN.md` (Phase B), `REVIEW.md` (Phase C), `IMPLEMENTATION-PLAN.md`
    (Phase E)
- **Modify** later (after Phase F begins, separately):
  - `agency/capabilities/jules.py` (capability deltas)
  - `agency/capabilities/_jules_api.py` (any new endpoint surface
    the design names)
  - `skills/<jules-skill-name>/SKILL.md` per skill the design lands
  - Possibly an `AGENTS.md` at the agency repo root, scoped for Jules
    sessions dispatched against this repo

## Open Questions / Needs Research

1. **`AGENTS.md` at the agency repo root** — does the user want one
   committed (visible to Jules every dispatch and to other agents like me)
   or just shipped *in dispatch prompts* (hidden from the repo's casual
   reader)? Recommend committed — discoverable + scoped to the agency
   subtree per the reference doc.
2. **`automationMode: AUTO_CREATE_PR`** as the dispatch default — the spec-012
   refinement flips `require_plan_approval=True` as the default; should the
   complement also be `auto_create_pr=True`? Reference §6 + §3c argue yes
   for the "agency drives Jules end-to-end" pattern, but human-in-the-loop
   safety argues for `False`. Maintainer call before Phase E commits to a
   default.
3. **`protocol_preset` field on `dispatch`** (lesson-15 §7 echoes this) —
   a named bundle of canonical preamble + tool-discipline instructions so
   the ~700-token boilerplate doesn't ride every dispatch. Should it be a
   verb arg or a separate `jules.protocol_preset(name)` lookup?
4. **The intersection model.** "Several intersecting Jules skills … carry
   all the knowledge." Does that mean (a) one skill calls another via
   `develop`-style chaining, (b) skills share gates by name, or (c) a
   meta-skill `jules-driving` composes them? Phase B's hypothesis above
   leans (a)+(b); Phase C panel should challenge.
5. **MCP direction.** §6 of the reference says Jules → external MCP via a
   closed allow-list. Confirm our agency MCP cannot host tools for Jules
   to call; the integration is one-way (we drive Jules, not the reverse).
6. **Skill scope vs `develop` overlap.** `develop` already covers TDD /
   plan / brainstorm. The new Jules skills should NOT duplicate that —
   they extend it with Jules-specific phase gates. Phase B must draw the
   boundary explicitly.

## Evidence

- `agency/capabilities/_jules_reference.md` — the user-supplied research
  synthesis stored beside the capability (§1–§7).
- `Plan/012-jules-complete-lifecycle-and-watcher/spec.md` + `REVIEW.md` +
  `DOGFOOD-NOTES.md` — the operational input + the live silent-fail
  observations that this design must close.
- `docs/vision/CORE.md` §47-62 (skills are Lifecycle templates), §131-133
  (capability-owned ontology, strict merge), :7-18 (no new concepts, lean
  contract).
- `the-agency-system/Plan/JULES_PROTOCOL.md` + `_lessons-learned/02, 08,
  10, 12, 15` (the operational doctrine encoded into the watcher and the
  recovery flow).
