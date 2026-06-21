---
review_of: Plan/superseded/008-superclaude-analysts/spec.md
reviewer: vision-alignment (spec-panel critique mode, canon axis)
axis: VISION CANON fidelity (NOT SuperClaude-source fidelity — that is REVIEW.md)
canon:
  - docs/vision/CAPABILITY-CLUSTERS.md   # the "few primitives" verdict (§26-43)
  - docs/vision/CORE.md                  # four concepts + "no new concepts" (16-18)
  - docs/vision/specs/capability.md      # role-tags act/transform/effect
  - docs/vision/specs/superpowers-port.md
code:
  - agency/capabilities/develop.py
  - agency/capabilities/reflect.py
  - agency/capabilities/transmute.py (DOES NOT EXIST — the cluster is unbuilt)
date: 2026-05-27
---

# VISION REVIEW — Spec 008 (SuperClaude Analysts)

> Scope note: the existing `REVIEW.md` is a **source-fidelity** critique (does the
> spec match the SuperClaude tree?). This review is the orthogonal **canon-fidelity**
> axis: does the spec match the Agency vision canon, and in particular is a *new
> top-level `analyze` capability* justified under the "few primitives" verdict? The
> two reviews agree on the lens/mode/role-tag findings; they diverge on the
> capability-shape question, which REVIEW.md never asked.

## Alignment verdict

**ALIGN-WITH-ONE-RESHAPE.** The spec is deeply canon-literate in its *mechanism*:
personas-as-lens-DATA and modes-as-descriptors are exactly right, the verbs are
correctly `transform`, and the OntologyExtension / self-registration framing is
faithful. But it commits the one sin the canon names most explicitly — it
**multiplies a top-level primitive** (`analyze`) where the canon already provides a
home for it. This is a reshape, not a redesign: every verb, lens, and mode survives;
only the *capability boundary* must move.

## Canon citations (the tension)

1. **`analyze` is NOT in the cluster table.** `CAPABILITY-CLUSTERS.md:10-24`
   enumerates the entire candidate surface that was "surveyed, clustered, and
   spec-paneled" (`CORE.md:137-141`). `analyze` appears nowhere in it. The verdict
   is explicit that this surface is *closed by construction*: "the four concepts +
   the engine absorb it all; the only net-new specs were `delegate` and `reflect`"
   (`CORE.md:139-141`). A new `analyze` primitive is a 12th capability the canon's
   own census did not find a need for.

2. **The `transform` set already HAS a named home: `transmute`.**
   `CAPABILITY-CLUSTERS.md:20` — `transmute` | `transform` | "pure functions over
   artefacts: views, indexes, summaries, tool-list shaping | **the open `transform`
   set**." Severity-ranked findings over a target, an effort band, a layered
   explanation, a persona lens, a mode descriptor — these are *exactly* "pure
   functions over artefacts" (read → derived view, no external mutation). The spec
   even SAYS so: Design (spec.md:163-169) argues "the `/sc:` analysis surface is
   stateless compute over a target … which is exactly the `transform` role." That
   sentence is the argument for folding into the open `transform` set — yet the spec
   then mints a *named* primitive instead of populating the named-but-unbuilt one.

3. **"Multiplying concepts re-introduces bloat."** `CAPABILITY-CLUSTERS.md:26-33`:
   "Most clusters are **facets of the four concepts**, not new top-level primitives
   … Multiplying concepts would re-introduce bloat. After the collapse, the one
   net-new primitive — `delegate`." The bar for a new top-level capability is a
   *new concept the four cannot absorb* (delegate = agent-fan-out + quota + join).
   `analyze` introduces no new concept; it is read-compute over Memory artefacts.

4. **"No new concepts."** `CORE.md:16-18` ("Cross-cutting guards … are engine
   middleware, **not** concepts") and the whole "Dropped" section
   (`CORE.md:82-90`) establish that the four concepts are the irreducible core and
   the move is always *fold into one*, never *add a fifth thing*. A capability is
   not a concept, true — but a *top-level named capability that the cluster census
   rejected* is the same instinct the canon warns against.

## The new-capability-vs-fold ruling

**RULING: `analyze` should NOT exist as its own top-level capability.** Its surface
splits cleanly across the canon's existing homes, with zero loss:

| spec-008 verb / artefact | canon home | why |
|---|---|---|
| `analyze(target, dimension)` — severity-ranked findings | **`transmute`** (the open `transform` set, `CLUSTERS:20`) | pure read→derived-view; "summaries/indexes/views over artefacts" |
| `estimate(scope)` — effort band | **`transmute`** | pure derived view |
| `explain(subject, level)` — layered explanation | **`transmute`** | pure derived view |
| `lens(persona)` — expert-lens DATA | **`transmute`** (judgment-as-data, a catalogue lookup) | not a discipline, just data retrieval |
| `mode(name)` — descriptor | **`transmute`** OR a 1-line `reflect`/`develop` pointer | descriptor lookup |
| `troubleshoot(symptom)` — diagnosis-only | **`transmute`** (diagnosis = derived view); fix-loop already → `develop` `debug` | spec already splits it correctly |
| `Analysis` node + `dimension` enum | the `transmute` capability's `OntologyExtension` | unchanged — moves with the verbs |
| `design` discipline | **`develop`** `DEV_SKILLS` (spec already does this) | correct as-is |
| `analyze`/`business-panel`/`brainstorm-discovery` skills | `skills/` Lifecycle templates (spec already does this) | correct as-is |
| `introspection` mode | pointer to **`reflect`** (spec already says this) | correct as-is |

So the canon-faithful shape is: **populate the named-but-unbuilt `transmute`
cluster** with the analytic read-verbs, **extend `develop`** with `design` (already
specced), **point at `reflect`** for introspection (already specced), and ship the
walkable skills under `skills/` (already specced). Net-new primitives created: **0**
(matches the canon's "0 new primitives beyond delegate/reflect" census). Net-new
*facet population*: the `transmute` row goes from specced to built — which is
*exactly* how the canon says the surface grows (`CORE.md:143-144`: "grow the
capability set by dropping files into `capabilities/`").

**Caveat (honest steel-man of the spec's position):** the canon also says a new
capability "arrives by dropping a file … each self-registers and owns its ontology
fragment" (`CLUSTERS:5-8`) and capabilities are an OPEN set (`capability.md:15`,
`CORE.md:25`). So a *file named `analyze.py`* is not per se a canon violation the way
a fifth *concept* would be. The violation is narrower and is about **legibility, not
legality**: the cluster table is the canon's map of the territory, and shipping an
`analyze` primitive that the table neither lists nor folds leaves the map and the
code disagreeing. The fix is therefore either (a) build it as `transmute` (preferred
— it matches the existing map), or (b) if the team insists on the `analyze` filename,
**amend `CAPABILITY-CLUSTERS.md` first** to add the row and state why `analyze` is a
distinct facet from `transmute` — "the canon wins; code serves it" (CLAUDE.md,
spec.md:28) forbids letting code silently outrun the canon. What the spec must NOT
do is ship a primitive the canon's own census did not surface, leaving REVIEW.md and
this file as the only record that the boundary was even debated.

## Q-by-Q (the three alignment questions)

**Q1 — new `analyze` vs fold.** Ruled above: **FOLD**, primarily into `transmute`
(the open `transform` set, `CLUSTERS:20`), with `design`→`develop` and
`introspection`→`reflect` (both already in the spec). A standalone `analyze`
primitive contradicts `CLUSTERS:26-33` and the `CORE.md:139-141` census. ALIGNED on
*role* (transform), MISALIGNED on *boundary* (new top-level capability).

**Q2 — personas-as-lens-DATA, modes-as-descriptors.** **FULLY ALIGNED.** This is the
spec's strongest canon move. `capability.md:62-66` ("a voice/AI-pattern check is a
`transform` whose output is … data, never gates") and `CORE.md:64-80` (Schemas &
Templates as "ordinary nodes in Memory", judgment-as-data) directly endorse a
persona being review-questions/priorities/anti-patterns returned as DATA, not a new
agent or concept. `CORE.md:33-35` is explicit: "An agent … is a Lifecycle
parameterization" — so a persona that does NO lifecycle work is correctly NOT an
agent; it is data. The spec's insistence (spec.md:166-169) that "personas are not
agents … they are lenses (data the verb iterates)" is textbook four-concepts
fidelity and introduces **no new concept**. Modes-as-descriptors (trigger/posture/
output-shape returned as data) is the same pattern and equally clean. KEEP both
verbatim — they belong on whatever capability hosts the verbs (`transmute`).

**Q3 — role-tags + verb-frame naming.** **ALIGNED with one nuance.** Tagging
`analyze`/`troubleshoot`/`estimate`/`explain`/`lens`/`mode` as `transform` is
correct per `capability.md:18-22` (transform = "stateless compute, no side-effect")
and is reinforced by `capability.md:67` ("A capability spanning two roles … is split
by role") — which is *precisely* why splitting `troubleshoot` (diagnose=transform)
from the `--fix` loop (effect/lifecycle → `develop` `debug`) is canon-correct. The
nuance: the canon's **Lifecycle verb-frame** is `open·move·close` + `read·find·check·
watch` (`CORE.md:30-32`); these analytic names are NOT lifecycle verbs and should not
be — they are open-set Capability verbs, which "are capability-defined"
(`capability.md:15-16`), so domain names like `analyze`/`explain` are legitimate.
No verb-frame violation. (Minor: `analyze.analyze` is a verb whose name equals its
capability — under the `transmute` reshape this disappears, e.g. `transmute.findings`
or `transmute.analyze`, removing the stutter.)

## Misalignments (canon axis)

- **MA1 (CRITICAL, boundary):** `analyze` is minted as a top-level capability though
  the cluster census (`CLUSTERS:10-24`) and verdict (`:26-43`) closed the surface at
  the four concepts + `delegate`. It is read-compute = the `transmute` facet
  (`CLUSTERS:20`), not a new primitive.
- **MA2 (MAJOR, legibility):** `transmute` — the canon's NAMED home for the open
  `transform` set — is never mentioned in the spec. The spec argues its verbs are
  "exactly the `transform` role" (spec.md:165) yet does not connect that to the
  cluster the canon already reserves for it. The map and the plan are disconnected.
- **MA3 (MINOR, canon-maintenance):** if `analyze` ships anyway, `CLUSTERS.md` is
  left stale (no row, no fold-rationale), violating "keep `docs/vision/`
  authoritative" (CLAUDE.md) and "the canon wins; code serves it" (spec.md:28).
- **MA4 (MINOR, stutter):** `analyze.analyze` — verb == capability name; an artefact
  of the wrong boundary, gone under the `transmute` reshape.

(Source-fidelity misalignments — dimension enum, mode count, select_tool, persona
catalogue — are already captured in REVIEW.md and not re-litigated here. The spec.md
has since absorbed REVIEW's must-fixes; this review found no NEW source issues.)

## Recommended aligned framing

> Port the `/sc:` analysis surface by **building the `transmute` capability**
> (`agency/capabilities/transmute.py`, home `capability`/`transform`) — the
> canon's named-but-unbuilt "open `transform` set" (`CLUSTERS:20`). It carries the
> analytic read-verbs (`analyze`/`troubleshoot`/`estimate`/`explain`), the
> `lens`/`mode` data lookups, and the `Analysis` node + `dimension` enum as its
> `OntologyExtension`. Extend `develop` with the `design` discipline; point
> `introspection` at `reflect`; ship the walkable `analyze`/`business-panel`/
> `brainstorm-discovery` skills under `skills/`. Net-new top-level primitives: **0**
> — the surface grows by populating an existing cluster facet, exactly as the canon
> prescribes (`CORE.md:139-144`, `CLUSTERS:26-43`).

If the team has a defensible reason `analyze` is a *distinct* facet from `transmute`
(e.g. "transmute = data-shaping, analyze = judgment-bearing findings"), that case can
be made — but it must be made **in `CAPABILITY-CLUSTERS.md` as a new/split row with
rationale**, landed *before* the code, not asserted only in the plan.

## Must-change list (canon-blocking)

1. **Rehome the verbs onto `transmute`, not a new `analyze` primitive** (MA1/MA2).
   Rename the capability to `transmute` (the canon's named `transform` home,
   `CLUSTERS:20`); move `analyze`/`troubleshoot`/`estimate`/`explain`/`lens`/`mode`
   + the `Analysis` ontology fragment onto it. Update `affects:`, Design, Files,
   Done-When, and tests accordingly. — **OR** —
2. **(If `analyze` is kept) amend the canon FIRST.** Add an `analyze` row to
   `CAPABILITY-CLUSTERS.md:10-24` and a fold-vs-distinct rationale to the verdict
   (`:26-43`) explaining why `analyze` is a facet the four-concept census missed.
   No code lands until the canon lists it. ("The canon wins; code serves it.")
3. **Wire the spec's own `transform`-role argument to the named cluster.** The
   Design rationale (spec.md:163-169) must cite `CLUSTERS:20` (`transmute` = the open
   `transform` set) and state explicitly that this port *populates* that facet — so
   the plan and the canon map agree. Keep personas-as-lens-DATA, modes-as-
   descriptors, and the `transform` role-tags **exactly as written** (Q2/Q3 are
   already canon-faithful).
