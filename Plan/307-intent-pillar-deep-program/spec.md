---
spec_id: "307"
slug: intent-pillar-deep-program
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 4, 9]
depends_on: ["029", "044", "048", "091", "110", "147", "262", "290", "291", "304"]
domain: intent
wave: program-master
---

# Spec 307 — Intent-pillar deep program (master): guided intent discovery

> **Program master.** This is the source of truth for the **intent-pillar
> deep build-out** UNTIL its children are promoted (Spec 047 precedent: a
> cluster master governs until each child spec ships, then the child wins).
> It defines the architecture, the verb surface, the ontology, and the
> core-feature coverage matrix that the 17 child specs (308–325, 313 folded·319 deferred) all reference.
> No child re-derives the package layout or node names — they cite this file.

## Why (evidence + doctrine)

**The observed gap (owner directive, 2026-06-18):** *"The capability pillar is
nearly complete — but the intent is shallow."* The four pillars (CORE.md §"Four
complete pillars") are meant to each be a **complete suite of code + tools**.
The Capability pillar is rich: `agency/capabilities/prompt/` alone carries
`clusters/` (assembly · dossier · engineering · fragments · frameworks · gates ·
profiles), `data/`, `references/`, `templates/`, and a consolidated
`ontology.py`. The `research` capability is a real multi-agent pipeline
(`_lead` → `_specialist` → `_verify` → `_findings`). By contrast the **Intent
pillar's WRITE side is one thin file** — `agency/intent.py`: `capture · confirm ·
amend · chain · owners`. The only "intent" capability (`intent.py`, Spec 091)
holds critical-thinking *methods*, and Spec 291 even folds those into `thinking`.

So today an Intent is **born shallow**: a user types one sentence, the
`/agency-onboard` four-beat script (Spec 148) or a bare `intent_bootstrap`
(Spec 029) mints a `{purpose, deliverable, acceptance}` node, and the work
begins. There is **no guided exploration** — no research-backed grounding, no
ambiguity resolution, no AskUser clarification chain, no scope elicitation, no
acceptance derivation, no feasibility probe — before the intent is confirmed.
The provenance moat (Goal 2) records *what was done* against an intent that was
never *sharpened*. **The WHY is captured, not discovered.**

**The doctrine this serves.** CORE.md names Intent the **human-owned root** that
"everything edges back to via SERVES." If that root is vague, every downstream
SERVES edge inherits the vagueness. Spec 262 already saw the shape — wrapping the
`claude-api` managed-agents onboarding pattern (describe → configure →
environment → session) as a capability — but stayed a single 4-beat interview.
This program generalizes that insight into a **complete guided-discovery suite**,
giving the Intent pillar the same depth the Capability pillar has, and closing
the write-side gap the way Spec 290 closed the read-side gap.

## The thesis — guided exploration captures the WHY

A shallow intent is a *guess*. A discovered intent is *grounded*. The difference
is **guided exploration**, and exploration has exactly two engines this program
builds on top of the existing substrate:

1. **Research agents** (the `research` pipeline, Spec 044) — to **ground** the
   intent in evidence: does this already exist in the repo? has a prior
   reflection solved it? is it feasible? what's the prior art? Grounding turns
   "I want X" into "I want X, and here is what reality says about X."

2. **AskUser tool-call chains** (the `AskUserQuestion` harness tool) — to
   **resolve ambiguity** interactively: when the captured intent is
   underspecified, conflicting, or missing acceptance, the engine asks a
   *well-formed* question (2–4 options, recommended-first, multiSelect where the
   axes are independent) and folds the answer back into the Intent. The user
   stays creative; the engine captures everything.

Guided discovery is the **interleaving** of these two: research narrows the
option space so AskUser asks *sharp* questions (options derived from evidence,
never invented — the derivability audit, CLAUDE.md), and the answers narrow the
research so the next probe is *targeted*. The loop runs until the intent clears a
**clarity gate** (Spec 322), then `confirm` fires with a full provenance trail
(Spec 325) of *how the WHY was discovered*.

## Architecture — the `discover` capability (drop-in, prompt-shaped)

One new capability, `discover`, structured to **mirror `prompt/`** (the
reference for a deep capability) so the Intent pillar gains a peer to the
Capability pillar's richest member:

```
agency/capabilities/discover/          # auto-discovered like any cap (Goal 4)
  __init__.py                          # re-homes to agency/intent/discover/ when Spec 291 lands
  _main.py                             # DiscoverCapability(CapabilityBase) — verb surface
  ontology.py                          # consolidated OntologyExtension (nodes/edges/enums/schemas/skills)
  clusters/                            # one module per discovery phase (prompt-cluster pattern)
    _base.py                           #   shared helpers (intent recall, turn recording)
    interview.py                       #   Spec 309 — adaptive AskUser beat-chain
    ask.py                             #   Spec 310 — the well-formed-question primitive
    clarify.py                         #   Spec 311 — ambiguity detection + clarification loop
    ground.py                          #   Spec 312 (+scouts, was 313) / 314 — research dispatch + grounding + feasibility
    frame.py                           #   Spec 315 — prompt-framework framing
    examine.py                         #   Spec 316 — thinking-methods pass on the draft
    scope.py                           #   Spec 317/318/319 — acceptance · scope · decomposition
    refine.py                          #   Spec 320/322 — supersession + clarity gate
    session.py                         #   Spec 321/324/325 — watch · state · replay
  data/
    ambiguity-signals.json             #   ambiguity heuristics (definable registry, CLAUDE.md #8)
    interview-beats.json               #   the adaptive beat library
  templates/
    discovery-session.md               #   the session Document (Spec 292 convergence)
    intent-brief.md                    #   the discovered-intent brief
  references/
    elicitation.md                     #   how the interview works (doc-source marked)
    askuser-contract.md                #   the well-formed-question contract
```

> **Re-home note (Spec 291).** The pillar-package reorg targets
> `agency/intent/discover/`. This program lands `discover` at the *current*
> discoverable path (`agency/capabilities/discover/`) so it ships before the
> reorg; the reorg's loader transition moves it with the other intent-pillar
> caps (thinking · analyze · research · prompt). No code change at re-home — only
> the path. Children cite `discover/<cluster>.py` relative to the package root.

**The drop-in bar (CLAUDE.md).** Adding `discover/` adds verbs + ontology + a
docstring-derived SkillDoc + a walkable discipline — and **nothing else**. The
engine `discover()`s it; the CLI mirrors it (Spec 079); MCP wires it; emit
renders its skill. If any child needs an edit outside `discover/` (beyond the
documented seams — the session-start hook in Spec 321 and the `manage`
composition in Spec 324), that coupling is the bug.

## The verb surface (locked here; children implement)

| Verb | Role | Cluster | Spec | One-line |
|---|---|---|---|---|
| `interview` | act | interview | 309 | adaptive AskUser beat-chain → draft Intent + ElicitationTurns |
| `ask` | transform | ask | 310 | build ONE well-formed AskUser question (options/recommended/multiSelect) |
| `clarify` | act | clarify | 311 | detect ambiguity, ask targeted questions, fold answers into the Intent |
| `ground` | effect | ground | 312 | dispatch the research pipeline to ground the Intent in evidence |
| `feasibility` | act | ground | 314 | research-backed go / no-go / refine probe on the draft Intent |
| `frame` | transform | frame | 315 | apply a prompt framework → sharp purpose/deliverable/acceptance |
| `examine` | act | examine | 316 | run thinking methods on the draft Intent (decompose/assumptions/premortem) |
| `acceptance` | transform | scope | 317 | derive testable, Gherkin-shaped acceptance criteria |
| `scope` | act | scope | 318 | elicit in-/out-of-scope boundaries (AskUser) |
| `decompose_intent` | act | scope | ~~319~~ | split a large Intent into a sub-intent tree — **DEFERRED** (trim, panel-driven; not in the active 17) |
| `refine` | act | refine | 320 | supersede the Intent from an exploration finding (bi-temporal) |
| `clarity` | transform | refine | 322 | score the Intent's clarity; the `confirm` gate reads it |
| `watch_intent` | transform | session | 321 | detect a NEW intent emerging mid-session → trigger capture |
| `state` | transform | session | 324 | discovery read-API — what's captured/ambiguous/grounded/confident |
| `replay` | transform | session | 325 | reconstruct a discovery from its provenance (the moat) |
| `discover` | act | interview | 323 | the full guided-discovery walk (composite) — the discipline's spine |

(Names + signatures are the scope, not frozen wire shapes — each child's
spec-panel may refine within this surface; the **set** is the contract.)

## The ontology (locked here; children populate)

New node types (all under `discover`'s `OntologyExtension`):

| Node | Key props | Recorded by |
|---|---|---|
| `DiscoverySession` | seed, status, clarity_score | interview / discover |
| `ElicitationTurn` | beat, kind, question, answer | interview / clarify |
| `ClarificationQuestion` | text, options, ambiguity_kind | ask / clarify |
| `ScopeBoundary` | item, side | scope |
| `AcceptanceCriterion` | text, gherkin, measurable | acceptance |
| `FeasibilitySignal` | verdict, rationale | feasibility |
| `IntentRefinement` | trigger, before, after | refine |

New edges:

| Edge | From → To | Meaning |
|---|---|---|
| `ELICITS` | DiscoverySession → ElicitationTurn | the turns of a session |
| `DISCOVERED` | DiscoverySession → Intent | the session that captured this Intent |
| `CLARIFIES` | ClarificationQuestion → Intent | a question that sharpened the Intent |
| `GROUNDS` | Citation → Intent | research evidence grounding the Intent (reuses research's `Citation`) |
| `BOUNDS` | ScopeBoundary → Intent | a scope edge on the Intent |
| `VALIDATES` | AcceptanceCriterion → Intent | a criterion that says "done" for the Intent |
| `REFINES` | IntentRefinement → Intent | a supersession trigger (paired with the substrate `SUPERSEDED_BY` edge — `agency/memory.py`) |

New enums:

| Enum | Members |
|---|---|
| `ambiguity_kind` | underspecified · conflicting · vague-scope · missing-acceptance · unstated-assumption |
| `feasibility_verdict` | go · no-go · refine |
| `scope_side` | in · out |
| `turn_kind` | describe · configure · constrain · ground · clarify · confirm |

New schemas (Document/artefact, Spec 292): `discovery-session` · `elicitation-turn`
· `scope-boundary` · `acceptance-criteria` · `feasibility-probe` · `intent-brief`.

Walkable skill: **`guided-discovery`** (authored discipline, Spec 323) — overrides
the derived `discover-usage` (Spec 081).

## Core-feature & capability coverage matrix (the explicit ask)

The owner directive: the program must *"implement and use all Core Features as
well as the capabilities."* This matrix is the contract — every core feature and
every sibling capability is exercised by at least one child:

| Core feature / capability | How `discover` uses it | Child |
|---|---|---|
| **Intent node** (capture/confirm/supersede/chain) | the whole point — discovery mints/sharpens/confirms it | 308, 309, 320 (·319 decompose *deferred*) |
| **Capability (open set, drop-in)** | `discover` IS a drop-in folder (Goal 4) | 308 |
| **Lifecycle (skill_walk, gates)** | `guided-discovery` walkable discipline; hard clarity gate | 322, 323 |
| **Memory (record/link/project, bi-temporal)** | every turn/finding a node; `refine` supersedes; `state` projects | 308, 320, 324, 325 |
| **`research` capability** (lead→fan-out→verify) | `ground` dispatches it; the intent-discovery scouts (folded from 313) | 312, 314 |
| **`prompt` capability** (framework library, Spec 304) | `frame` routes a framework over the raw intent | 315 |
| **`thinking` capability** (Spec 110 methods) | `examine` runs decompose/assumptions/premortem on the draft | 316 |
| **`intent` critical-thinking** (Spec 091) | folded via `examine` (honours the 291 merge into `thinking`) | 316 |
| **AskUser tool-call chain** (`AskUserQuestion`) | `ask` primitive + the testable emit→fold protocol; `interview`/`clarify`/`scope` compose it | 309, 310, 311, 318 |
| **Driver seam** (Spec 147 structured-output) | the interview/clarify next-question generation runs through it | 309, 311 |
| **`manage` read-API** (Spec 290) | `state` composes `manage`; discovery dashboard | 324 |
| **Document convergence** (Spec 292) | the session renders to `discovery-session.md` | 308, 324 |
| **Provenance moat** (Goal 2) | replayable discovery — every turn an edge | 325 |
| **Session-start hook** (Spec 076) | `watch_intent` detects new in-session intents | 321 |
| **Token economy** (Goal 1) | budgeted projections; AskUser collapses N research turns into 1 question | 310, 324 |

## The guided-discovery flow (what the discipline walks)

```
seed ──► interview ──► [draft Intent] ──► ground ──► clarify ──► frame
 (309)      (AskUser beats)        (research agents)  (AskUser)   (prompt fw)
                                       │                              │
                                       ▼                              ▼
                                  examine (thinking) ──► scope ──► acceptance
                                       (316)            (318)        (317)
                                                          │
                                       ┌──────────────────┴───────────────┐
                                       ▼                                   ▼
                              clarity gate (322) ◄── refine (320)   decompose_intent (319)
                                       │ (passes)                          │
                                       ▼                                   ▼
                                  confirm Intent  ◄────────────────  sub-intent tree
                                       │
                                       ▼
                            replay/state (325/324) — the durable moat
```

Each arrow records a graph edge; `watch_intent` (321) can re-enter the flow at
`interview` when a NEW intent emerges mid-session.

## Child-spec index (16 active + 1 deferred)

> **Trim 19→17 (panel-driven, 2026-06-18).** A spec-panel + business-panel pass
> (`spec-panel-review.md`, `business-panel-review.md`) trimmed the corpus: **313
> folded into 312** (the scouts were too coupled to `ground` to stand apart — a
> literal `depends_on` cycle), and **319 deferred** (sub-intent decomposition is
> machinery to add *after* the core loop is dogfooded — Taleb via-negativa,
> Meadows lightest-touch). Active build set = this master + 16 children.

| Spec | Title | Layer |
|---|---|---|
| **308** | `discover` capability scaffold + intent-pillar code structure | foundation |
| **309** | Elicitation interview engine (`discover.interview`) | guided exploration |
| **310** | AskUser well-formed-question primitive (`discover.ask`) | guided exploration |
| **311** | Ambiguity detection + clarification loop (`discover.clarify`) | guided exploration |
| **312** | Research-grounded intent + intent-discovery scouts (`discover.ground`) | research agents |
| ~~313~~ | ~~Intent-discovery research specialists (scouts)~~ — **folded into 312** | research agents |
| **314** | Feasibility + prior-art go/no-go probe (`discover.feasibility`) | research agents |
| **315** | Intent framing via prompt frameworks (`discover.frame`) | sharpen the WHY |
| **316** | Critical-thinking examination of the draft (`discover.examine`) | sharpen the WHY |
| **317** | Acceptance-criteria derivation (`discover.acceptance`) | structure |
| **318** | Scope-boundary elicitation (`discover.scope`) | structure |
| ~~319~~ | ~~Intent decomposition into a sub-intent tree~~ — **DEFERRED** (kept on disk, not in the active set) | structure |
| **320** | Exploration-driven intent refinement (`discover.refine`) | lifecycle |
| **321** | Per-session new-intent detection (`discover.watch_intent`) | lifecycle |
| **322** | Intent clarity score + capture gate (`discover.clarity`) | quality gate |
| **323** | Guided-discovery walkable discipline | discipline |
| **324** | Discovery read-API + management/dashboard (`discover.state`) | read side |
| **325** | Discovery provenance + replay (`discover.replay`) | the moat |

## Cross-spec coherence (the rules children must not break)

1. **One capability, one folder.** All children land code under `discover/`;
   only 321 (session-start hook), 324 (`manage` composition), and 312 (the
   `research/_specialist.py` scout seam) touch a documented seam outside it.
2. **Derive, don't invent (CLAUDE.md derivability audit).** Every AskUser option
   and every acceptance criterion is *derived* from research/context/the intent —
   never a literal the verb made up. `ask` (310) enforces this with a **resolvable
   `provenance` pointer** (each option names the context item it derives from; an
   option with no resolving source is rejected) — not a trivial token-overlap check.
3. **No transform mutates the Intent — proposals have ONE writer (the
   proposal→apply protocol).** "Transform" here means **does not mutate the Intent
   or any pre-existing node**; a transform MAY append its *own* provenance artefact
   (the question `ask` asked, the criteria `acceptance` derived) — that append is
   not a mutation. `clarity`, `state`, `replay`, `frame`, `ask`, `acceptance` are
   `transform`; the `act`/`effect` writers that mutate the Intent or fan out a
   pipeline are `interview`, `clarify`, `examine`, `ground`, `scope`, `refine`,
   `feasibility`, `discover`. The keystone rule the spec-panel asked for: a verb
   that *proposes* a change to the Intent's triple (`frame` → a sharper
   `{purpose, deliverable, acceptance}`; `examine` → surfaced assumptions;
   `acceptance` → criteria) **returns the proposed delta; it never writes the
   Intent's fields itself**. The delta is applied by exactly one writer — the
   caller via `intent.amend` (inside `interview`/`clarify`) or `discover.refine`
   (320). So `frame`'s role contradiction dissolves: it is `transform` *because* it
   only proposes; no two writers race on the Intent.
4. **The AskUser seam is a typed, testable protocol (not an unwritten doc).** `ask`
   (310) emits a `ClarificationQuestion` + `question_id`; the harness renders it;
   the caller folds the answer via `_base.fold_answer(question_id, answer)`. An
   injected `AnswerProvider` exercises the full round-trip with no live
   `AskUserQuestion`. The 9 AskUser-consuming specs share this one seam.
5. **No second source of truth (Spec 290 rule).** `state` composes `manage` /
   `analyze.graph` / `project`; it never reimplements a query that exists.
6. **Invariants, not snapshots (CLAUDE.md #8).** Every test asserts a
   relationship computed from the live graph (turn-count == beats elicited;
   clarity gate monotonic in answered-questions) — never a pinned count.
7. **Provenance or it didn't happen (Goal 2).** Every discovery action records
   its node + edge; 325's replay is the acceptance test that the moat is whole —
   checked against the independent Invocation census, not a self-referential walk.

## Done When (program-level — children carry their own)

- [ ] All active children (308–325 minus folded 313 & deferred 319) are drafted with `## Why`, `## Design`,
      `## Tests` (RED→GREEN, rule-8 invariants), `## Acceptance`, `## Followup`.
- [ ] The verb surface + ontology in this master are the single source the
      children cite (no child redefines a node name or verb signature).
- [ ] The coverage matrix holds: every core feature + sibling capability is
      exercised by a named child.
- [ ] `TODO.md` carries the program row + the child rows (16 active + 313 folded + 319 deferred).
- [ ] On promotion (each child ships Slice 1), this master's child-index row
      flips to a pointer at the promoted spec (Spec 047 precedent).

## Acceptance

A reviewer reading this master can answer, without opening a child: *what code
lands where, what verbs exist, what nodes/edges the discovery writes, which core
feature and which sibling capability each child exercises, and how the
guided-discovery flow runs from seed to confirmed, grounded, clarity-gated
Intent.* The 16 active children make it real; this master makes it coherent.

## Followup — Implementation Status (2026-06-18)

- **Status: draft (program master).** Authored on
  `claude/intent-pillar-deep-specs-uag2v0`. No code yet — this is the design
  layer (the deliverable is the spec corpus, per the branch name). Execution is
  Slice-1-per-child (typed shapes first, LLM/AskUser seams behind the typed
  contract, per the wet-LLM follow-up pattern), gated by the acceptance suite.
- **Next step:** children 308–325 drafted in the same commit; first build slice
  is 308 (scaffold) → 309/310 (the AskUser core) → 312 (the research core).
