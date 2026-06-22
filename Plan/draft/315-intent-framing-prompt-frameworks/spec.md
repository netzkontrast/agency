---
spec_id: "315"
slug: intent-framing-prompt-frameworks
status: draft
state: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [1, 9]
depends_on: ["304", "307", "308"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 315 — Intent framing via prompt frameworks (`discover.frame`)

> Child of the intent-pillar deep program (Spec 307), **"sharpen the WHY"
> layer**. This is the bridge from the PROMPT pillar into Intent: it routes a
> Spec 304 framework over the raw captured seed and returns a structured,
> sharper `{purpose, deliverable, acceptance}` draft for the caller to amend.
>
> **★ CONSOLIDATED by Spec 307 §Refinement (2026-06-18).** `frame` becomes the
> *prompt pass* of the merged **`sharpen`** proposal verb (with `examine`/`acceptance`)
> — all three propose a triple-delta under the single-writer protocol (master rule
> 3). The `prompt.frameworks_for` composition is the keeper; the standalone verb
> folds. Retained as the framing mechanism record.

## Why (evidence + doctrine)

Spec 307 §"The thesis" says a shallow intent is a *guess* — and the rawest of
all is the very first sentence a user types. `intent_bootstrap` (Spec 029) mints
a `{purpose, deliverable, acceptance}` node from that seed verbatim: vague in,
vague out. The Capability pillar already owns the cure. Spec 304 ships a
31-entry **prompt-framework library** (`agency/capabilities/prompt/data/frameworks.json`
— CO-STAR, CRISPE, APE, …), each a named-slot metaprompt skeleton routed by
`intent_category`, with `intent_signals` keyword routing already in the data.

The coverage matrix (Spec 307 §"Core-feature & capability coverage matrix") binds
the `prompt` capability to exactly one child: *"`frame` routes a framework over
the raw intent."* This is that child. Prompt engineering is, structurally, the
discipline of turning a vague ask into structured fields — precisely the shape of
an Intent's three fields. CO-STAR's Context/Objective/Style/Tone/Audience/Response
maps a one-line seed into a structured WHY; CRISPE's Capacity/Insight/Statement
does the same for an exploratory one. Framing is **token-efficient** (Goal 1): one
routed template collapses what would otherwise be a multi-turn clarification into a
single sharpened draft, and the framed brief is a **Document-convergence** artefact
(Goal 9) the session renders.

Doctrine guardrails this honours: **read-only stays read-only** (Spec 307 rule 3 —
`frame` is `transform`; `clarify`/`interview` do the mutation) and **derive, don't
invent** (CLAUDE.md derivability audit — the framework is *routed* from the live
library, never a literal the verb makes up; the sharpened fields are *derived* by
mapping the seed onto the framework's named components).

## Design

**Cluster:** `agency/capabilities/discover/clusters/frame.py` — the
`FrameCluster` mixin composed into `DiscoverCapability` (Spec 308 `_base.py`
pattern; uses `_recall_intent`).

**Verb:**

```python
@verb(role="transform")
def frame(self, intent_id: str = "", framework: str = "") -> ToolResult:
    """Route a prompt framework over the raw intent → a sharper triple (transform).

    Inputs: intent_id (defaults to ctx.intent_id), framework (a Spec 304
            slug; "" ⇒ auto-route via the prompt router over the seed shape).
    Returns: {framework, rationale, framed: {purpose, deliverable, acceptance},
              components, source_ref}.  Read-only — the caller amends.
    chain_next: discover.clarify (311) on any field the framing left thin.
    """
```

**Composition of the named sibling (Spec 304).** `frame` calls the `prompt`
capability — it does NOT reimplement routing (Spec 307 rule 4, no second source
of truth):

1. **Route.** When `framework=""`, call `prompt.frameworks_for(intent=<seed>)`
   (Spec 304 verb) — the seed is `_recall_intent(intent_id)`'s `purpose`/`raw`.
   The router scores the seed against `intent_signals` and returns the
   budget-ranked candidate list; `frame` picks the top `audience="user"` entry.
   When `framework=<slug>` is given, call `prompt.framework(slug)` directly and
   honour the explicit choice.
2. **Map.** Take the framework's `components` (e.g. CO-STAR →
   `[Context, Objective, Style, Tone, Audience, Response]`) and its `template`,
   and project the seed onto the three Intent fields: components describing the
   *what/why* feed `purpose`; the concrete output component (Response / Expectation)
   feeds `deliverable`; the quality-bar component (Expectation / Response format)
   seeds `acceptance`. The mapping is the **driver seam** (Spec 147 structured
   output) behind the typed contract — Slice 1 returns the component-tagged
   scaffold; the wet-LLM fill lands behind it.
3. **Return** the framed triple + which framework + a one-line `rationale`
   (why the router chose it) + `source_ref` (Spec 304 attribution carries
   through). No graph mutation beyond the Invocation.

**Spec 307 ontology used (no new nodes — `frame` is `transform`).** `frame` reads
the `Intent` node via `_recall_intent` and the `PromptFramework` node (Spec 304)
via the `prompt` composition. It records its `Invocation` SERVES the Intent
(provenance moat); the framed brief renders to the `intent-brief` schema /
`intent-brief.md` template (Spec 308 templates, Spec 292 convergence). The chosen
framework is named in the Invocation's payload so `replay` (Spec 325) can show
*which* framework sharpened the WHY. The caller folds the framed triple back via
`discover.refine` (320) or a plain `intent.amend` — `frame` never writes the
fields itself.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Read-only invariant (Spec 307 rule 3):** invoking `frame` records exactly one
  `Invocation` and **adds no domain node/edge** — assert the graph node-count
  delta equals the single Invocation, computed from a live census (never a pinned
  count). No `PromptFramework` is minted (it's read from Spec 304's library).
- **Routing is derived, not invented (derivability audit):** when `framework=""`,
  the returned `framework` slug is a member of the live
  `prompt.frameworks_for(seed)` candidate set — assert membership against the live
  router output, not a hardcoded "CO-STAR". A seed with no signal hit still
  returns a valid library slug (router default), never a made-up name.
- **Composition, not reimplementation (rule 4):** `frame` with an explicit
  `framework=<slug>` returns the SAME `components`/`source_ref` that
  `prompt.framework(slug)` returns for that slug — assert field-equality against
  the sibling verb's live output, so the two surfaces can't diverge.
- **Field coverage:** the framed result populates all three Intent fields
  (`purpose`, `deliverable`, `acceptance` each non-empty) — assert the triple is
  complete, derived from the framework's component count (a framework with N
  components maps onto ≥1 field each), not a frozen string.
- **Attribution carries (Spec 304):** `source_ref` is present and non-empty on
  every framed result — assert it is propagated from the routed framework.

RED: `frame` absent → `capability_discover_frame` unresolved. GREEN: the cluster
lands, the five assertions pass against the live graph + live Spec 304 library.

## Acceptance

A caller hands `discover.frame` a vague seed and receives a structured
`{purpose, deliverable, acceptance}` draft tagged with the framework that shaped
it and why — without the verb writing anything. Auto-routing picks a real library
framework derived from the seed; an explicit slug is honoured and matches the
`prompt` capability's own view of that slug. The framed brief is render-ready
(`intent-brief`), and the provenance trail names the framework so a later
`replay` (325) can show how the WHY was sharpened. `clarify` (311) and `refine`
(320) do the mutation; `frame` only proposes.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** "Sharpen the WHY" child of the Spec 307 program; depends on
  the Spec 308 scaffold (cluster home + `_base.py`) and the Spec 304 framework
  library (the composed sibling). Authored as design only — no code.
- **Slice plan:** Slice 1 = typed contract (route via `prompt.frameworks_for`,
  return component-tagged scaffold + rationale + source_ref, read-only invariant
  green). Slice 2 = the wet-LLM seam-fill (driver maps seed→components into prose
  fields, Spec 147), landing behind the same typed signature.
- **Open question (resolve at build):** when the router returns multiple
  same-tier candidates, does `frame` pick top-priority silently or surface the
  choice as an AskUser via `discover.ask` (310)? Default: pick top, name the
  runner-up in `rationale`; promote to an `ask` only if signal scores tie.
