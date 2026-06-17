---
spec: 305
title: prompt-framework-routing
status: Draft
depends_on: [304, 298, 109, 292]
clusters: [prompt]
vision_goals: [1, 2, 9]
---

# Spec 305 — `prompt.route_framework` + `render` + goal-aware `evaluate`

> Second slice of the prompt-architect reimplementation. A 27-framework library
> (304) is useless if you must read all 27 to pick one. This slice ships
> **token-efficient routing** (intent → the ONE right framework), **template
> rendering** (the prompt-creation tool), and a **goal-aware evaluator** (the
> 5-dimension quality grid, made target-aware).

## Why

prompt-architect's `framework_analyzer.py` is a bespoke keyword-scorer: detect
intent → discriminate within the candidate set → recommend a framework. agency
*already* ships that mechanism generically — `recommend` (Spec 298) routes a
free-text request to a capability+verb by scoring token overlap on the live
registry. Framework routing is the **same algorithm with a different registry**
(the 304 framework library instead of the capability registry). So 305 does NOT
port a parallel scorer (rule 8); it specializes 298's pattern.

`prompt_evaluator.py`'s 5-dimension grid (clarity / specificity / context /
completeness / structure) is what `prompt.audit` already gestures at. 305 grows
`audit` into a **goal-aware** evaluator: criteria adapt to the prompt's *target*
(a user-prompt is judged differently from a tool-description) — the seam 306
extends with functional-doc profiles.

## Design

- `route_framework(draft, intent_hint="", top=1) -> {intent, framework, alts,
  rationale, scaffold}` — **two-level routing**: (1) detect the `intent_category`
  by matching `draft` against signals AGGREGATED from the library entries (each
  framework's `intent_category` + `when_to_use` + `discriminators` — derived, not
  a hardcoded keyword table, rule 8), overridable by `intent_hint`; (2) within
  that category, rank candidates by token overlap + per-framework `discriminators`
  hits. Return the top framework + a filled-skeleton `scaffold` + a one-line
  `rationale`. **Token-efficient: returns ONE framework (plus ≤ 1 alt), never
  dumps the library.** Records a `Recommendation` node (298 parity) SERVING the
  intent. Scoring reuses 298's overlap helper IF cleanly extractable; otherwise a
  thin local `_score_overlap` (298 reuse is an optimization, NOT a build
  blocker — see Q1).
- `render(framework_slug, fields, max_tokens=…) -> PromptInstance` — fill a
  framework's `template` with `fields`, honoring the existing `engineer` token
  budget gate; records `PromptInstance` + `FILLS_FRAMEWORK` edge (304).
- `evaluate(prompt_body, target="user-prompt", min_score=…) -> {scores, flags,
  status}` — the 5-dim grid; `target` selects a criteria PROFILE. This slice
  ships the `user-prompt` profile + the seam; 306 adds `skilldoc` / `tool-desc`.
  Supersedes `audit` (kept as a thin back-compat alias).

## Done-When

- [ ] `route_framework` returns ONE framework + scaffold + rationale; intent
  detection DERIVED from the 304 library's `discriminators` (not a hardcoded
  keyword table — rule 8); `Recommendation` node recorded.
- [ ] Reuses 298's scoring substrate (import/extend — no parallel scorer).
- [ ] `render` fills a template → `PromptInstance` with `FILLS_FRAMEWORK` edge,
  budget-gated.
- [ ] `evaluate(target="user-prompt")` returns 5-dim scores + flags; `audit`
  aliases it **with its existing return contract preserved** — Spec 292's
  `document.ingest → prompt.audit` call must be unaffected (grep call sites;
  enforcement blast-radius).
- [ ] Token-efficiency invariant test: `route_framework` payload ≪
  `frameworks_for(intent)` payload (returns one, not the candidate set) — assert
  the RELATIONSHIP, not a byte count (rule 8).
- [ ] Acceptance scenarios; drift clean; TODO row.

## Design notes / interconnections

- **Spec 298 (recommend)** — the routing engine. 305 = "recommend, scoped to the
  framework library." If 298's scorer is not cleanly reusable, the spec-panel
  pass decides: extend 298 to take a pluggable registry vs. a thin shared helper.
  (Flagged for the panel — Open Q1.)
- **Spec 296 (select)** — sibling (approach-archetype routing). Cross-reference
  so a future "which prompt strategy?" query routes `select` → `route_framework`.
- **Spec 109 (engineer / audit)** — `render` reuses the budget gate; `evaluate`
  supersedes `audit`.
- **Spec 292 (document.ingest → prompt.audit)** — `evaluate` is the upgrade of
  the verb that bridge calls; 292's "score every file" gains target-awareness.
- **Spec 026/091 (intent critical-thinking)** — intent DETECTION here is
  lightweight signal-matching, distinct from the intent capability's reasoning
  methods; cross-referenced, not merged.

## Open questions

1. Extend `recommend.route` with a `registry=` param (frameworks as an alt
   registry), or a shared `_score_overlap` helper both call? **Recommend the
   shared helper** — keeps `recommend` request→capability-only; framework routing
   owns its candidate shaping. Panel to confirm.
2. Does `route_framework` ask discriminating questions when intent is ambiguous
   (prompt-architect's interactive step), or always commit to best-guess + alt?
   **Recommend best-guess + alt** (non-interactive; caller re-routes with
   `intent_hint` if wrong) — keeps the verb pure + token-bounded.
3. Keep `audit` as alias or deprecate? **Recommend alias for one spec cycle**
   (enforcement blast-radius — grep call sites first).
