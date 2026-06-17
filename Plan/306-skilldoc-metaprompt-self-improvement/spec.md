---
spec: 306
title: skilldoc-metaprompt-self-improvement
status: Draft
depends_on: [304, 305, 080, 292, 054]
clusters: [develop, prompt]
vision_goals: [2, 6, 9]
---

# Spec 306 — `develop.optimize_skilldoc`: functional-prompt framework + flagged linter

> Third slice — the **adaptation**, not the port. The 27 frameworks (304) optimize
> *rhetorical* prompts (a human asking an LLM for content). agency's own surface —
> capability docstrings, SkillDocs, verb descriptions, templates — are *functional*
> prompts: their job is correct ROUTING + correct INVOCATION, not persuasion.
> Owner directive (2026-06-17): "a function does not need a Role — it needs
> actionable insight." So 306 designs a **specialized functional-prompt
> framework**, a **`develop` verb** that authors optimized skilldocs/templates
> with it, and a **goal-aware linter with flags** keyed to the target. Advisory
> only — **no auto-rewrite.**

## Why

This is the metaprompt loop the whole effort exists for: agency using its own
framework substrate to **enrich its own documentation** (CLAUDE.md: "every tool
description is a prompt"). But applying CO-STAR (Context / Objective / Style /
Tone / Audience / Response) to a function's docstring is a category error — Tone
and Audience are noise; what a router needs is *when to call this* and *what it
does*. The functional surface needs its own framework.

`persona` (Spec 297) is the instructive contrast: it *adds* a specialist Role to
an AGENT doing work. 306 is its complement — it *strips* Role from a FUNCTION
exposing a capability. **Roles for agents; actionable insight for functions.**

## Design

- **A `functional` framework family in the 304 library** (`audience = functional`
  — Spec 304's discriminator; held out of the 7 user `intent_category` values so
  305 routing never offers it as a user-prompt pick), DERIVED from existing agency
  conventions (derivability audit) — the framework IS the convention made
  explicit:
  - `skilldoc` profile — components `use_when · triggers · red_flags ·
    actionable_imperative · sibling_disambiguation · token_budget` (mirrors the
    Spec 080 docstring grammar `Use when:` / `Triggers:` / `Red flags:` that
    SkillDocs already derive from).
  - `tool-desc` profile — components `what_it_does · when_to_route_here ·
    inputs · chain_next · failure_modes` (mirrors the verb-docstring grammar
    `Inputs:` / `Returns:` / `chain_next:`).
  - `template` profile — components `slots · invariants · budget`.
- **`develop.optimize_skilldoc(target_ref, kind="skilldoc") -> {flags, candidate,
  rationale, artefact_id}`** (advisory `act`):
  1. resolve `target_ref` → text (a capability docstring / SkillDoc / template);
  2. `evaluate(text, target=kind)` (305) → flagged findings;
  3. `render` the functional framework's profile → an optimized CANDIDATE;
  4. record `Artefact(kind="doc-optimization")` SERVING the intent;
  5. **return the candidate — do NOT write source** (owner directive). A human or
     a later `branch.commit_smart` applies it.
- **Goal-aware linter flags** (305 `evaluate`, functional profiles) — a FLAGS
  taxonomy keyed to the target GOAL, e.g.:
  - skilldoc: `role_padding` (a function doesn't need a role!) · `missing_trigger`
    · `no_red_flags` · `vague_imperative` · `sibling_collision` · `over_budget`.
  - tool-desc: `no_routing_signal` · `missing_inputs` · `no_chain_next` ·
    `no_failure_mode`.
  Each flag names the TARGET GOAL it violates, not a generic quality dip.
  **`role_padding` is the load-bearing novel heuristic — it fires when a doc whose
  `audience=functional` carries role-assignment framing (`you are a/an <role>`,
  `act as`, `as a <role>`, persona-style second-person address). That detection
  is the testable core of the owner's "a function needs no Role" insight.**

## Done-When

- [ ] `functional` framework family (skilldoc · tool-desc · template profiles) in
  the 304 library, components DERIVED from the 080 docstring grammar (no authored
  duplication — derivability audit).
- [ ] 305 `evaluate` gains `target=skilldoc|tool-desc|template` profiles + the
  flag taxonomy; `role_padding` fires when a functional doc carries rhetorical
  role framing.
- [ ] `develop.optimize_skilldoc(target_ref, kind)` returns flags + optimized
  candidate + rationale + `artefact_id`; **writes no source** (assert the verb is
  read-only against the target file).
- [ ] **Dogfood acceptance:** run on ≥ 1 real agency capability docstring; assert
  the INVARIANT — it returns a well-formed `{flags, candidate, artefact_id}` and
  records the artefact as graph provenance (NOT "exactly these flags on cap X" —
  that pins live state, rule 8). Proves the loop is live, not dormant
  (dormant-surface audit).
- [ ] `optimize_skilldoc` output feeds `develop.validate_skill` (Spec 080 gate)
  cleanly. Drift clean; TODO row.

## Design notes / interconnections

- **Spec 080 (SkillDoc derived from docstring)** — 306 optimizes the docstrings
  080's SkillDocs derive FROM; the `skilldoc` profile IS 080's grammar, scored.
  `optimize_skilldoc` is the authoring companion to `validate_skill`.
- **Spec 297 (persona)** — named contrast: persona adds Role to agents; 306
  forbids Role on functions (`role_padding` flag). Complementary, not
  overlapping.
- **Spec 292 (document.ingest → prompt.audit)** — 306's flagged evaluator is the
  target-aware upgrade of the scorer 292 runs on every ingested file; a SkillDoc
  Document now scores against the `skilldoc` profile.
- **Spec 054 (drift)** — the optimized candidate must preserve `# AGENCY-DRIFT`
  tags + `<!-- doc-source -->` markers; the verb carries them through.
- **Why `develop`, not `prompt`** — authoring a skilldoc is a development-workflow
  act (next to write_spec / implement / validate_skill). `prompt` owns the
  substrate (framework + evaluate); `develop` owns the workflow that applies it.
  Clean substrate/workflow split. **Dependency direction is acyclic: `develop`
  imports `prompt`, never the reverse.**

## Open questions

1. Should `optimize_skilldoc` batch-scan ALL capability docstrings (a repo-wide
   linter run) or one target per call? **Recommend one target** + a thin
   `develop` loop / script for the repo-wide pass (keeps the verb pure; batch is
   orchestration).
2. Where does the `functional` family live — in `frameworks.json` flagged
   `user_facing=false`, or a sibling `functional-frameworks.json`? **Recommend the
   same JSON, flagged** — one library, one loader; routing (305) filters out the
   `meta` intent so functional frameworks never surface as user-prompt
   recommendations.
3. Auto-apply path later? Out of scope now (owner: no auto-rewrite). A future
   spec could wire `optimize_skilldoc` → `branch.commit_smart` behind an explicit
   `--apply`. Noted, not built.
