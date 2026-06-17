---
spec: 304
title: prompt-framework-library
status: Draft
depends_on: [109, 129, 292]
clusters: [prompt]
vision_goals: [1, 4, 9]
---

# Spec 304 — `prompt.frameworks`: the 27-framework library, first-class

> First slice of the **prompt-architect reimplementation** (cf. the SuperClaude
> binding goal, Specs 294-301): extract → design → reimplement prompt-architect
> as first-class agency substrate. NOT an ingested prompt "port" — graph-native
> data + verbs, mirroring Spec 129 (Dramatica-as-prompt-fragments).

## Why

prompt-architect (ckelsoe — 27 research-backed frameworks across 7 intent
categories) is, structurally, a **template library + a decision tree**. Each
framework (APE, CO-STAR, ReAct, …) is a *metaprompt template*: a named-slot
skeleton you fill to produce a better prompt. agency already ships the exact
substrate this needs — Spec 129's fragment library (vendored JSON + per-project
overlay + budget-aware composition). Spec 304 applies that pattern to
frameworks: "every template is a prompt" (now doctrine — CLAUDE.md rule 2 /
Spec 292) made queryable, composable, and runtime-extensible.

This slice ships the **library + lookup**. Routing (305) and self-improvement
(306) build on it.

## Design

A new `frameworks` cluster in the existing `prompt` capability (cluster
coherence — the cap is literally prompt-engineering; do NOT spawn a new
top-level capability — the drop-in-capability bar).

- **Data (sourcing-model first):**
  `agency/capabilities/prompt/data/frameworks.json` is the source of truth —
  one entry per framework:
  `{slug, name, intent_category, complexity_tier, audience, components[],
    template, discriminators[], when_to_use, source_ref}` where
  `audience ∈ {user, functional}` (functional = a meta-framework for agency's
  own docs, Spec 306 — held OUT of the 7 user `intent_category` values so
  routing never surfaces it as a user-prompt pick), and `source_ref` names the
  upstream prompt-architect framework + its license. A per-project overlay
  (`.agency/prompt-frameworks-overlay.yaml`) adds/overrides without editing the
  vendored file (mirrors Spec 129 `register_fragment`).
- **Reference prose preserved (owner Q2 directive):** the 27 human-readable
  framework docs land at `agency/capabilities/prompt/references/frameworks/*.md`
  — rendered references for human readers, NOT parsed at runtime (routing reads
  the JSON; the prose is for people).
- **Ontology extension** (`prompt/ontology.py`): `PromptFramework` node
  `{slug, name, intent_category, complexity_tier}`; `INTENT_CATEGORY` enum
  `{recover, clarify, create, transform, reason, critique, agentic}`;
  `COMPLEXITY_TIER` enum `{simple, medium, comprehensive, reasoning, structure,
  critique, meta}`; `AUDIENCE` enum `{user, functional}`; edge `FILLS_FRAMEWORK`
  (PromptInstance → PromptFramework,
  traversed by 305 `render` — declare-an-edge ⇒ traverse-it).
- **Verbs (mirror Spec 129 fragments exactly):**
  - `framework(slug) -> {slug, name, intent_category, complexity_tier,
    components, template, when_to_use, tokens}` | `{slug, error: NO_FRAMEWORK}`.
  - `frameworks_for(intent, max_tokens=2000) -> {frameworks: [...],
    total_tokens, truncated_at}` — budget-aware candidate list for a known
    intent (order = library priority; reuse `budget_take`).
  - `register_framework(slug, payload, overlay_path="") -> {...}` — write a
    custom framework to the overlay (effect; runtime-extensible).

## Done-When

- [ ] `frameworks.json` ships every prompt-architect framework (the canonical
  set — RISE split into `rise-ie`/`rise-ix`, `hybrid` deferred per Q3), each with
  slug · intent · tier · audience · components · template · discriminators ·
  when_to_use · source_ref, extracted from prompt-architect's `assets/templates/`
  + `references/frameworks/`. Coverage asserted by a name MAP (upstream → slug),
  not a count literal (rule 8).
- [ ] Reference `.md` docs preserved under `references/frameworks/` (one per
  framework).
- [ ] **Attribution preserved:** prompt-architect is MIT (ckelsoe); the ported
  templates + reference docs carry upstream attribution (a `NOTICE` / per-entry
  `source_ref` + the MIT license text under `references/frameworks/`). Porting
  must not strip provenance.
- [ ] `PromptFramework` node + `INTENT_CATEGORY` + `COMPLEXITY_TIER` enums +
  `FILLS_FRAMEWORK` edge in `prompt/ontology.py`.
- [ ] `framework` / `frameworks_for` / `register_framework` in a new
  `prompt/clusters/frameworks.py` mixin, composed into `PromptCapability`.
- [ ] Overlay round-trips (register → framework reads it back); loader cache
  invalidated on write (Spec 129 parity).
- [ ] Acceptance scenarios (pytest-bdd): lookup hit/miss, all-frameworks-present
  (count DERIVED from the JSON, not a hardcoded 27 — rule 8), intent filter,
  budget truncation, overlay round-trip. Drift clean; TODO row.

## Design notes / interconnections

- **Spec 129 (fragments)** is the structural template — same loader, overlay,
  `budget_take`, cache-invalidation. 304 is "129 for frameworks". Reuse the
  helpers; do not re-implement.
- **Spec 292 (document.mirror / every-file-is-a-prompt)** — frameworks are the
  vocabulary 306's evaluator scores docs against; 304 is the library that bridge
  consumes.
- **Spec 291 (pillar reorg, draft)** — the `frameworks` cluster rides along with
  `prompt` into `agency/intent/prompt/` when 291 lands; zero extra work.
- **No-hardcoded-values (rule 8):** tests assert "≥ 1 entry per intent_category"
  and "every entry has a non-empty template", not "exactly 27".

## Open questions

1. Seed `PromptFramework` graph nodes at install, or keep JSON-as-store with
   lazy node-on-reference (129's model)? **Recommend 129's model** — JSON is the
   store; nodes record only when a framework is actually used (305 `render`),
   keeping install light and the graph free of dormant nodes.
2. RISE has two variants (IE / IX). **Recommend two slugs** (`rise-ie`,
   `rise-ix`) — distinct components + when_to_use; one-node-with-variant would
   re-grow the schema.
3. The `hybrid` template (modular section assembly) — port as a framework, or
   defer to 305's `render` (which already composes sections)? **Recommend
   defer** — hybrid IS what `render` does; don't duplicate.
