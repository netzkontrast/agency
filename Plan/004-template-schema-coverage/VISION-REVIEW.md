---
slug: vision-review-004
type: review
status: ready
summary: Vision-alignment review of spec 004 (template-schema-coverage) against CORE.md §64-80. Verdict ALIGNED-WITH-RESERVATIONS — the spec correctly models coverage as nodes+edges and correctly diagnoses the unwired validate-side, but it scopes to artefact-kinds and explicitly defers the canon's stated next-step prize (verb-param schema as the single isomorphism source). Recommends widening the framing.
reviewer: vision-alignment
canon: docs/vision/CORE.md §64-80, docs/vision/specs/memory.md, docs/vision/VOCABULARY.md
---

# Vision-Alignment Review — Spec 004 (Schema Coverage for Uncovered Artefact Kinds)

> Reviewed: `/home/user/agency/Plan/004-template-schema-coverage/spec.md`
> Against: `docs/vision/CORE.md:64-80` ("Schemas & templates — the typed/generative
> layer"), `docs/vision/specs/memory.md`, `docs/vision/VOCABULARY.md`.
> Code: `agency/ontology.py`, `agency/templates.py`, `agency/memory.py:144`,
> `agency/capabilities/{plugin,jules,delegate}.py`, `tests/test_agency.py`.

## Alignment verdict

**ALIGNED-WITH-RESERVATIONS.** The spec is canon-respecting on the *mechanism*
(it models coverage as Schema/Template nodes and `VALIDATES_AGAINST`/`DERIVED_FROM`
edges, not ad-hoc Python dicts) and it is unusually honest about the validate-side
gap that most specs would paper over. But it deliberately scopes *away* from the
canon's stated NEXT STEP — "one schema per verb renders three ways… making the
ontology schema the single source" (CORE.md:68-72). It treats that as out of scope
without saying so explicitly, and it picks the *narrower* of two coverage axes
(artefact-kinds) when the canon names the *verb-param* axis as "the *isomorphism
glue*." This is a defensible MVP slice but it must be re-framed as the first rung
of that ladder, not as "the typed spine," or it risks ossifying a half-loop.

## Canon citations (the contract being measured against)

- **CORE.md:64-66** — "Both are ordinary nodes in **Memory**, forming a
  generate/validate pair." → Schema and Template are NODES, not registries.
- **CORE.md:67-68** — "A **Schema** is the typed contract for a node / artefact /
  **verb-params**. It powers `validate` / `check`." → the canon's Schema scope is
  three-fold; verb-params are first-class, not a follow-up.
- **CORE.md:68-72** — "**Design intent:** one schema per verb renders three ways
  (MCP `inputSchema`, the Skill's frontmatter, the bash CLI's arg parser) — the
  *isomorphism glue*. *(Not yet wired… making the ontology schema the single source
  is the next step.)*" → **the named NEXT STEP**, and it is verb-param-shaped.
- **CORE.md:74-76** — "A **Template** is a parameterized generator. It powers `act`:
  a Capability produces an Artefact `DERIVED_FROM` the Template, which
  `VALIDATES_AGAINST` its Schema." → the exact edge pair the spec must (and does) use.
- **CORE.md:78-80** — "**Proven runnable in `agency/`** (a Template renders an
  Artefact that a Schema validates; a missing field fails)." → the claim the spec's
  "validate side is not wired" section must reconcile.
- **memory.md:54-56 / VOCABULARY.md:18** — typed nodes include `Schema`/`Template`
  in the one graph; `validate` is a read-frame verb. Confirms node-modelling intent.

## Misalignments (severity-ranked, spec-panel critique mode)

### CRITICAL — Scope picks the wrong (narrower) axis; ignores the canonical prize
**Experts: Fowler (lead), Wiegers, Newman.**
The canon names **verb-param schemas** as "the *isomorphism glue*" and "the single
source… the next step" (CORE.md:67-72). Spec 004 instead covers **artefact-kind
schemas** for two recorded kinds (`jules-session`, `reduction`) and explicitly
*defers everything that smells like the real glue* — slot→artefact rewrites to spec
005 (spec.md:115-117), the 13-key superset deleted (spec.md:197-202). Artefact-kind
coverage is real and in-canon, but it is the *generate/validate-an-output* half;
the verb-param half is what makes the schema the SINGLE SOURCE rendered three ways
(MCP `inputSchema` ⇄ Skill frontmatter ⇄ bash arg parser). The spec never names
this larger prize, so a reader cannot tell whether 004 is *rung 1 of the
isomorphism ladder* or *a one-off patch that points the other direction*. As
written it reads as the latter. **Fowler:** "You are hardening the output contract
while the canon's stated single-source-of-truth is the input contract. Two schema
namespaces are forming; say which one you are building and how the other arrives."

### CRITICAL — "Proven runnable" is true only in tests; the spec's own framing overclaims
**Experts: Nygard (lead), Crispin.**
CORE.md:78-80 says the generate/validate pair is "Proven runnable in `agency/`."
The spec's "Why" opens by calling that loop "the typed spine of the graph… a
capability `act` renders an Artefact from a `Template`, and `Memory.validate_schema`
checks the recorded node against a `Schema` node" (spec.md:31-36) — present tense,
as if live. The spec's *own* later section (spec.md:119-145) correctly retracts
this: `grep -rn 'validate_schema\|VALIDATES_AGAINST' agency/` returns only the
definition and a docstring; **no production code records a `Schema` node, links
`VALIDATES_AGAINST`, or calls `validate_schema`.** I verified this independently:
the *only* place the pair runs end-to-end is the test suite
(`tests/test_agency.py:324-357`, `:501-508`), where the **test itself** hand-records
the `Schema` node (`mem.record("Schema", …)`) and hand-links the edge. So CORE.md's
"proven runnable" is *test-proven, production-unwired* — the canon and the spec are
reconcilable but only if both state it plainly. **The spec must not open with
"the typed spine of the graph" in the present tense while the spine is, in the live
engine, a registry with no enforcement point.** This is the exact "registry without
enforcement" gap the spec says it exists to close (spec.md:144-145) — good — but
the framing should lead with that, not bury it 90 lines down.

### MAJOR — The Schema-node bootstrap is the load-bearing change and is under-specified
**Experts: Hohpe (lead), Newman.**
The single architectural advance in 004 is "the engine records a `Schema` node per
`Ontology.schemas` entry" (spec.md:157-159, 289-298) — this is what turns the inert
registry into a checkable loop and is correctly node+edge-modelled (`node_id =
f"schema:{name}"`, then `VALIDATES_AGAINST`). But its placement is left as an Open
Question (spec.md:330-334: "engine or `ontology.py`?"), and its *lifecycle* is
unspecified: when in engine construction does it run, is it idempotent across
re-init, and does it run for ALL `Ontology.schemas` entries (i.e. the 5 already-
covered kinds get `Schema` nodes too, retroactively wiring them)? If yes, 004
silently wires the existing 5 as well — a bigger, better change than its title
admits, and one the canon would applaud. Make that explicit. **Hohpe:** "The
materialiser is the integration seam between the type registry and the graph; an
Open Question is the wrong home for it."

### MINOR — `string.Template` vs the canon's "ordinary node"
**Expert: Fowler.**
The spec adds `JULES_SESSION`/`DELEGATION_REDUCTION` as module-level
`string.Template` constants (spec.md:209-219). CORE.md:74 says a Template is "an
ordinary node in Memory." The existing code already lives in this tension (the 5
templates are also `string.Template` constants in `templates.py`, never recorded as
`Template` nodes in production — same gap as the Schema side). 004 faithfully
mirrors the existing pattern, so this is not a *regression*, but the spec's "Done
When" wires the **Schema** node (good) and leaves the **Template** node un-recorded —
so the `DERIVED_FROM` half of the canon's pair (CORE.md:74-76) stays unproven in
production even after 004. The round-trip the spec asserts is validate-only; the
generate-provenance edge (`Artefact -DERIVED_FROM-> Template`) is not closed.
**If you are wiring half the pair, say which half and why the other waits.**

### MINOR — Two schema namespaces, no parity story
**Expert: Wiegers.**
The spec rightly separates artefact-`kind`s (kebab, 7) from skill-`kind`s and
`produces:` slots (snake), and forbids dead schemas (spec.md:103-117) — disciplined
and well-evidenced. But it leaves no statement of how the *verb-param* namespace
(CORE.md:67) relates to either. A reader finishing 004 has three namespaces and a
rule for one. State the target end-state: which namespaces become `Schema` nodes,
and which single one is the canon's "single source."

## Recommended aligned framing

1. **Re-title and re-frame as the first rung, not the spine.** Something like
   "Wire the generate/validate loop end-to-end for two recorded artefact kinds
   (step 1 toward verb-param schema-as-single-source, CORE.md:68-72)." Add one
   paragraph in **Why** that names the canonical NEXT STEP and positions 004 as the
   *minimal runnable proof* of the node+edge mechanism that the verb-param work will
   reuse. This costs three sentences and converts a "narrow patch" into "rung 1."

2. **Widen the scope decision into an explicit, recorded choice.** Do NOT silently
   defer verb-params. Either (a) add a short "Out of scope / sequenced next"
   subsection that names verb-param schemas + the slot→artefact 005 work as the
   *deliberate* next rungs with a one-line rationale (recommended — keeps 004 small
   and shippable while honouring the canon), or (b) widen 004 to also materialise a
   `Schema` node from each verb's signature so the "one schema per verb" single
   source begins to exist. **Recommendation: (a) now, with (b) explicitly scheduled
   as 006.** A two-kind artefact patch that does not even *gesture* at the
   isomorphism prize is below the canon's bar; a two-kind patch that proves the
   node+edge loop AND names the ladder is exactly right.

3. **Promote the Schema-node materialiser out of Open Questions into Design.**
   Specify: where it runs (engine construction, after all extensions merged),
   idempotency, and that it materialises a `Schema` node for **every**
   `Ontology.schemas` entry (retroactively wiring the existing 5). That is the real
   deliverable; name it as such.

4. **Fix the overclaim and reconcile with CORE.md:78-80.** Open **Why** by stating
   the pair is *test-proven but production-unwired today*, and that 004's purpose is
   to make it production-runnable for the two new kinds via the materialiser. Add a
   one-line note that CORE.md:78-80's "proven runnable" refers to the test-level
   round-trip (`tests/test_agency.py:324-357`), so the canon and code do not appear
   to contradict.

5. **Decide the Template-node half explicitly.** Either record `Template` nodes and
   close the `DERIVED_FROM` edge in 004 (fully proving CORE.md:74-76 for the two
   kinds), or scope it OUT with a one-line reason and a note that the generate-side
   provenance edge remains test-only. Do not leave it implicit.

## Must-change list (blocking for canon-alignment)

1. **State the canonical NEXT STEP and 004's place on the ladder.** Add the
   verb-param-schema-as-single-source framing (CORE.md:68-72) to **Why** and an
   explicit "sequenced next" subsection. Without this the spec points away from the
   canon's named direction. *(addresses CRITICAL #1)*

2. **Fix the "typed spine" overclaim; lead with the unwired-validate diagnosis.**
   Rewrite the **Why** opening so it does not present the loop as live; reconcile
   explicitly with CORE.md:78-80 (test-proven, not production-wired). *(addresses
   CRITICAL #2)*

3. **Promote the `Schema`-node materialiser into Design with a full lifecycle**
   (placement, idempotency, runs for all `Ontology.schemas` entries incl. the
   existing 5). It is the load-bearing change and must not be an Open Question.
   *(addresses MAJOR #3)*

4. **Resolve the Template-node half** — record `Template` nodes + `DERIVED_FROM`
   for the two kinds, or scope it out in writing. The canon's pair is two edges;
   004 currently wires one. *(addresses MINOR — Template gap)*

## Scope recommendation (the headline question)

**Do not widen 004 itself to verb-param schemas — keep it the two-kind runnable
proof — but the spec MUST stop scoping toward the wrong axis silently.** The
verb-param schema (the canon's "single source… rendered three ways") is the real
glue and should be its own next spec (006), explicitly named in 004 as the rung
above it. Widen the *framing and sequencing*, not the *line count*. A 004 that
proves the node+edge loop end-to-end for two kinds AND names the verb-param ladder
is fully canon-aligned; the current 004, which proves the loop but points only at
artefact-kinds and defers the glue without acknowledging it, is not.
