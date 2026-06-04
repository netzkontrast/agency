# Internal Spec-Implementation Research Prompts

These five briefs (S1–S5) are **agency-internal research questions**
informing the implementation of the Novel-Capability spec (Plan/010).
Each references agency-internal artefacts (Spec 010, the
OntologyExtension contract, the bundled the-agency-system source SHA,
etc.) and is **NOT self-contained for Gemini**.

## How these differ from the top-level F1-F5 prompts

The top-level `../F1-F5*.md` prompts are **self-contained Domain-SOTA
surveys** for Gemini Deep Research — Gemini gets all context inline,
returns general novel-writing / Dramatica / agentic-writing SOTA. They
require no agency context.

These S1–S5 prompts are the opposite: they ask **narrow implementation
questions** with explicit agency-spec references. They're intended to be
run by **a Deep Research subagent with access to the agency repo + the
spec files** — not Gemini cold.

## How to use them

Each S* prompt is meant for an **internal Deep-Research subagent**
dispatched by the agency engine itself (or by a Claude session with
access to the repo). The agent:

1. Reads the agency spec(s) the prompt references.
2. Performs the targeted research (likely fanning out further subagents
   per Spec 044's `research` capability pattern).
3. Returns a focused answer that maps directly to the named Spec-010
   Done-When item.

## The five briefs

| File | Question (one-line) | Maps to Spec 010 § | Loop blocked |
|---|---|---|---|
| [`S1-narrative-validation-sota.md`](S1-narrative-validation-sota.md) | What's the canonical 2026 SOTA for narrative-structural validation? | Source fidelity §3 (NCP draft-07) | Loop 2 (`ncp_validate`) |
| [`S2-deferred-coherence-checks.md`](S2-deferred-coherence-checks.md) | Which of the 11 deferred coherence checks can be made genuinely decidable? | Open Question 7 | Loop 4 — v2 followup |
| [`S3-walker-phase-order.md`](S3-walker-phase-order.md) | What's the optimal phase order for the `work-concept` skill walker? | Skills §`work-concept` | Loop 6 |
| [`S4-decidable-style-transforms.md`](S4-decidable-style-transforms.md) | Which prosodic/style features survive as `transform`s? | Deferred §revision passes | v2 |
| [`S5-dramatica-lookup-edges.md`](S5-dramatica-lookup-edges.md) | How should `dramatica_lookup` handle edge cases beyond reciprocity? | `dramatica_lookup` verb | Loop 1 |

## Why both sets coexist

- **F* (Domain-SOTA, Gemini)** — produces general knowledge usable for
  any project working with novel-writing / Dramatica / agentic
  authoring. Stays useful even if Spec 010 changes shape.
- **S* (Spec-implementation, agency-internal subagent)** — produces
  decisions for the specific Spec 010 v1 / v1.5 / v2 surface. Tightly
  coupled to the spec; rewritten if the spec re-architects.

The F* set is the broader, more durable research. The S* set is the
narrower, more directly-actionable research. They complement each
other; running both surfaces both the SOTA landscape AND the
spec-grounded design decisions.
