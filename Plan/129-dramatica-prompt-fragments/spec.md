---
spec_id: "129"
slug: dramatica-prompt-fragments
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["103", "120"]
affects:
  - agency/capabilities/novel/data/dramatica/ontology.json
  - agency/capabilities/prompt/_main.py
  - tests/test_dramatica_prompt_fragments.py
domain: novel / prompt / dramatica
parent_spec: "101"
mvp-source:
  - "agency/capabilities/novel/data/dramatica/ontology.json (304 entries)"
  - "agency/capabilities/novel/data/reference/coherence-checks-spec.md (Dramatica vocabulary)"
---

# Spec 129 — Dramatica as composable prompt fragments

## Why

The 304-entry Dramatica ontology shipped in Spec 103 holds the **knowledge**
(types, elements, variations, throughlines, archetypes, quads, dynamic-pairs).
What's missing is the **delivery layer**: each entry needs a tiny prompt
fragment that tells an agent *how to write* a scene serving that particular
ontology position. Without it, the vocabulary sits inert.

This is what gives Novelcrafter / Scrivener their edge — small composable
prompt blocks selected by context. Agency has a richer ontology already; the
fragments turn it into a working prompt-assembly substrate.

## Done When

- [ ] **`fragment` field added** to ontology entries (304 entries), each a
      ≤300-token guidance string written in second person to an agent:
      "Scenes on the Past concern dwell on what was; the protagonist's
      relationship to memory is the axis of change. Avoid…"
- [ ] **`prompt.fragment(slug, kind=None) -> {slug, kind, text, tokens}`** —
      single-entry lookup. Resolves via Spec 120's `_resolve_term` so
      caller's kind-prefix guess (el./var./t.) doesn't matter.
- [ ] **`prompt.fragments_for(scope) -> [{slug, kind, text}]`** — multi-entry
      lookup. `scope` is a dict describing a storyform slice
      (`{throughline: "mc", concern_id: "t.past", problem_id: "el.self-interest"}`)
      and the verb returns ALL relevant fragments token-budgeted to ≤2000
      tokens total. Order: throughline → concern → problem → solution →
      crucial element.
- [ ] **Hybrid surface** — fragments live IN `ontology.json` (one source
      of truth) but a sibling `fragments-overlay.yaml` (gitignored)
      lets a project add/override without touching the vendored data.
      Overlay loads on top with `dict.update` semantics.
- [ ] **Author-extensible** — `prompt.register_fragment(slug, kind, text)`
      writes to the overlay so a workflow can author a fragment on the
      fly and it's available on the next `prompt.fragment` call.
- [ ] **Token-budget rule** — each fragment ≤ 300 cl100k tokens (lint),
      multi-entry assembly ≤ 2000 tokens (verb cap with `truncated: True`
      signalling).
- [ ] **Test fixture** — 6 representative fragments hand-authored (one
      per kind) + golden assembly for the good_work storyform's MC
      throughline (5-fragment chain, ≤2000 tok).
- [ ] `TODO.md` row + drift clean.

## Design notes

- **Why on `prompt` cap, not `novel`**: the fragments are general
  prompt-engineering primitives. Other domains (music with its own
  ontology, screenplay if it lands) reuse the pattern.
- **Why per-entry fragments, not category-only**: granularity. "Past
  concern" reads differently from "Future concern" — both deserve
  bespoke guidance. The redundancy at the *category* level is the
  point; category fragments compose with kind fragments.
- **Author workflow**: 304 fragments is large but most ontology entries
  ship empty initially. Lint enforces "fragment OR placeholder" so the
  field exists but the corpus grows incrementally as authors work.
  The bootstrap set is the 30 most-used entries (4 throughlines, 16
  types, 8 archetypes, 2-3 representative variations).

## Open questions

1. **Storage**: hand-author in `ontology.json` OR a sibling
   `fragments.yaml` keyed by id? Recommend YAML — easier to diff,
   readable in PR review, ontology.json stays validator-shaped.
2. **Voice**: second-person to agent ("Write the scene with…") or
   third-person commentary ("Past-concern scenes typically…")?
   Recommend second-person — agents follow imperatives better.
3. **Language**: English-only v1, or vendor `aliases_de` as a hint that
   we MAY need DE fragments? Recommend English-only; i18n is its own
   spec.

## Followup

(Populated when the PR ships.)
