# TODO — Spec State

> **Binding spec status index.** `Plan/NNN-slug/spec.md` holds per-spec details.
> Every PR that ships, opens, or changes a spec's status MUST update the row here.
> Shipped spec directories are deleted — the code is the record.
>
> **Last reviewed:** 2026-06-19 · **Shipped:** 119 · **Closed:** 8

## Verdicts at a glance

| Verdict | Count | Detail |
|---|---|---|
| **Shipped** | 119 | Spec dirs removed; see git log |
| **Closed / Superseded** | 8 | 008→042, 009→041+046, 010→101–108, 014→150+264, 028→060, 032→060, 063→065, 069 cancelled |
| **Partial** | 13 | 003, 004, 005, 094–099, 311, 317, 318, 322 |
| **Drafted** | ~168 | Not started or typed-stub only |

---

## Partial — in-flight slices

| Spec | Slug | Done so far | Next |
|---|---|---|---|
| 003 | skill-phase-objects | Typed Skill/Phase parse boundary (Slice 1) | Slice 2: wire into `develop.skill_walk` |
| 004 | template-schema-coverage | Coverage audit + spurious detection (Slice 1) | Slice 2: WARN→error gate |
| 005 | context-mode-and-token-economics | Overflow capture + recall library (Slice 1) | Slice 2: wire into `_envelope.py` body |
| 094 | music-lifecycle-cluster | Verbs + tests GREEN | Cluster-module file-split (batch with 095–099) |
| 095 | music-lyrics-cluster | Verbs + tests GREEN | File-split batch |
| 096 | music-audio-cluster | Verbs + tests GREEN | File-split batch |
| 097 | music-catalogue-cluster | Verbs + tests GREEN | File-split batch |
| 098 | music-promo-cluster | Verbs + tests GREEN | File-split batch |
| 099 | music-research-cluster | Verbs + tests GREEN | File-split batch |
| 311 | ambiguity-clarification-loop | `discover.clarify` + ask composition (Slice 1) | Slice 2: wet Driver ClarifySpec + grounding-sharp options |
| 317 | acceptance-criteria-derivation | Gherkin criteria from deliverable (Slice 1) | Slice 2: wet LLM Gherkin fill; render to `acceptance-criteria` doc |
| 318 | scope-boundary-elicitation | In/out boundary via ask composition (Slice 1) | Slice 2: wet AskUser fold; decomposition as 2nd candidate source |
| 322 | intent-clarity-score-gate | 5-signal score read-only (Slice 1) | Slice 2: `clarity_gate` composite + override token + Gate recording |

---

## Drafted — Discover / Intent Pillar (Spec 307)

> **Direction (PR #168, 2026-06-18):** 308/309/310 fully shipped and deleted.
> Consolidation: `{311,318}→elicit(mode)`; `{315,316,317}→sharpen(pass)`;
> `314→ground(decide=True)`; `325→state(mode)`. Apply FORWARD; Slice-1s stand.
> Substrate gate first: `capture→draft+clarity_score`; `confirm` is the
> unbypassable gate; `guided-discovery` (323) is a Lifecycle skill.

| Spec | Slug | One-line |
|---|---|---|
| 307 | intent-pillar-deep-program | Master architecture + LOCKED 7-node ontology; 16-verb surface |
| 312 | research-grounded-intent | Dispatch research pipeline → GROUNDS Citations (313 folded in) |
| 314 | feasibility-prior-art-probe | go / no-go / refine probe before commitment |
| 315 | intent-framing-prompt-frameworks | Prompt-framework framing pass (Spec 304 router) |
| 316 | critical-thinking-examination | Thinking methods on draft intent (Spec 110 `examine`) |
| 319 | intent-decomposition-tree | Deferred — decompose candidate source for 318 |
| 320 | exploration-intent-refinement | Bi-temporal supersession from exploration session |
| 321 | session-new-intent-detection | Per-session hook detecting new Intent on Spec 076 |
| 323 | guided-discovery-discipline | 7-phase walkable discipline superseding `/agency-onboard` |
| 324 | discovery-read-api-management | Read-API composing `manage` (Spec 290) |
| 325 | discovery-provenance-replay | Completeness check vs independent Invocation census |

---

## Drafted — Core Backlog

| Spec | Slug | Status | One-line |
|---|---|---|---|
| 066 | token-economy-cluster | Master (children shipped) | Wave master; 070/071 warn-accepted (optional future) |
| 070 | verb-surface-consolidation | WARN-accepted | Optional: verb surface consolidation implementation |
| 071 | skill-surface-reconciliation | WARN-accepted | Optional: skill surface reconciliation implementation |
| 077 | bdd-gherkin-tests | Backlog | BDD/Gherkin test driver — research-first |
| 078 | static-walkable-skills | Backlog | Static walkable skills — research-first; needs clarification |

---

## Drafted — Novel / KP Wave (133–145)

| Spec | Slug | One-line |
|---|---|---|
| 133 | story-structure-templates | BeatExpectation + 6 pacing verbs (Save-Cat / Three-Act / Hero's Journey etc.) |
| 134 | pov-voice-profiles | Per-POV voice signature + drift gate + scene-writer phase-4 extension |
| 135 | sensitivity-reader-workflow | SensitivityFinding + 7 verbs + `sensitivity-reader-pass` 4-phase skill |
| 136 | dual-storyform-architecture | Post-Dramatica A‖B + Klein-c inversion + Vortex transitions |
| 137 | canon-provenance-locks | [K]/[V]/[S]/[L] markers + Lock registry + source-hierarchy |
| 138 | plural-character-system | Dissociative-system: alter roster + ANP/EP + conflict matrix; no-fusion |
| 139 | reveal-discipline | 3-tier reader/POV/antagonist reveal timeline + multiplicity-veil |
| 140 | project-rulesets-motifs | Author R-rules + severity + motif-echo budget + anchor tracking |
| 141 | chapter-briefing-mode-blocks | 13-section briefing + mode-blocks + genre-per-act (vendored template) |
| 142 | novel-craft-skill-walks | 6 walkable skills over 136–141 + `--dry-run` flag |
| 143 | kohaerenz-prompt-fragments | ~60 KP-derived fragments across 6 families extending Spec 129 |
| 144 | voice-locked-drafting-prompt | Alter + VoiceProfile drafting brief + non-truncatable §TABOO + co-front guard |
| 145 | novel-preflight-composite-skill | Daily-driver 5-phase audit composing 137/139/140/141/144 in <200 ms |

---

## Drafted — Substrate-Adjacent (111–116, 278, 281–302)

| Spec | Slug | One-line |
|---|---|---|
| 111 | capability-migration | Migration plan for 17 existing caps + 2 domain caps to folder-form |
| 112 | dossier-capability | Research-brief authoring + corpus management; feeds research cap |
| 113 | research-ingestion-port | Research ingestion port for the research pipeline |
| 116 | sqlmodel-data-layer | SQLModel data layer alternative to GraphQLite for structured data |
| 278 | universal-frontmatter-discipline | Universal frontmatter contract across all rendered file kinds (closes rule 2) |
| 281 | autonomous-completion-session-followups | Follow-up tracking spec from PR #140 autonomous run |
| 283 | capability-render-substrate | Render substrate wired per capability |
| 285 | mcp-sampling-and-assumption-gate | MCP sampling + assumption gate before dispatch |
| 286 | substrate-oop-refactor | Split engine.py → `_substrate_tools.py` + `_invoke.py` |
| 287 | develop-plan-execute-skill | plan/execute skill for the `develop` capability |
| 289 | sqlmodel-entity-store | SQLModel entity store (complements Spec 116) |
| 291 | pillar-package-reorg | `agency/<pillar>/<cap>/` restructure + substrate absorb + intent/thinking dedup |
| 292 | graph-markdown-interconnect | Bi-temporal Document node — graph/file as peer surfaces (Spec 292) |
| 293 | memory-crud-management | `manage` read+write; verbs folded into Spec 290; pending close |
| 294 | business-panel-capability | Multi-expert panel: Christensen / Porter / Drucker / Godin / etc. |
| 295 | behavioral-modes-capability | Behavioral modes capability |
| 296 | select-approach-capability | Approach selection capability |
| 297 | specialist-personas-capability | Specialist personas capability |
| 298 | recommend-routing-capability | Recommendation routing capability |
| 299 | superclaude-coverage-map | Coverage map vs SuperClaude surface |
| 300 | token-symbols-capability | Token symbols capability |
| 301 | superpowers-coverage-and-extension | Superpowers coverage + extension |
| 302 | plugin-accessibility-and-reload | Plugin accessibility + hot-reload |

---

## Drafted — Vision Enhancement Waves 1–12 (155–277)

Waves 1–2 (155–177): typed-shape Slice 1 registered in code. Waves 3–12 (178–277):
`EnhancementSliceStub` catalogue entries only. Low priority relative to discover pillar.

| Wave | Specs | Theme | Enhances |
|---|---|---|---|
| Wave 1 — substrate foundation | 155, 156, 157, 159, 160 | Wet test + arch + dogfood depth | 006, 011, 015, 017, 018 |
| Wave 2 — authoring discipline | 163, 166–177 | Lint depth + authoring | 031, 050–065 |
| Wave 3 — capability depth | 178–183 | LLM-judge axis + managed fanout | 042–048 |
| Wave 4 — token-economy + naming | 184–194 | Naming, install, lint output | 049, 065–076 |
| Wave 5 — substrate hardening | 196–205 | BDD, CLI mirror, publish | 077–084 |
| Wave 6 — music depth | 206–216 | LLM production pipeline | 093–119 |
| Wave 7 — novel depth | 217–219, 221–224 | LLM-assisted novel build | 101–108 |
| Wave 8 — substrate-adjacent caps | 225–229 | Prompt / thinking / dossier wet | 109–114 |
| Wave 9 — novel post-shipped | 230–242 | Storyform, scene, character LLM | 120–132 |
| Wave 10 — pacing + KP | 243–255 | LLM voice + sensitivity + KP | 133–145 |
| Wave 11 — cross-anchor | 256–270 | Driver fallbacks, meta-cap, stop | 146–149, charter |
| Wave 12 — coverage closure | 271–277 | Jules, monitor, graph, dispatch | 012, 013, 020–022, 030, 040 |
