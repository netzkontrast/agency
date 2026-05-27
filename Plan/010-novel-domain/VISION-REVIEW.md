# VISION-REVIEW — Spec 010 Novel Domain Capability

**Reviewer:** vision-alignment (spec-panel/critique lens) · **Date:** 2026-05-27
**Subject:** `/home/user/agency/Plan/010-novel-domain/spec.md`
**Canon:** `docs/vision/CORE.md`, `docs/vision/CAPABILITY-CLUSTERS.md`,
`docs/vision/EXAMPLE.md`, `docs/vision/specs/capability.md`
**Code precedent:** `examples/music.py`, `agency/capability.py`, `agency/ontology.py`,
`agency/skill.py`, `agency/capabilities/gate.py`

> Scope note: this is a *vision-alignment* review (example-vs-core, ontology
> isolation, gate/transform framing). It is complementary to the sibling
> `REVIEW.md`, which is a *source-fidelity* review (Dramatica/NCP/coherence
> accuracy vs `the-agency-system @ 0a6a9e71`). The two do not overlap; both must
> pass before a session runs.

---

## Alignment verdict

**ALIGNED — accept with minor must-changes.**

The spec is the cleanest possible expression of the canon's central claim: a heavy
external domain folds onto the four concepts as an **example extension**, with
**zero** new primitives and **zero** core edits. It is `examples/music.py` scaled
up — same `CapabilityBase` + `OntologyExtension` shape (spec L50-60, L74-82),
loaded via `Engine(..., extra_capabilities=[…])`, role-tagged verbs, a gated
conceptualizer skill, structural truth as `transform`. It even ships a hard
guardrail — *"Do not modify `agency/` core … If it cannot, that is a finding to
escalate, not a core edit to slip in"* (L327-329) — and an acceptance bullet that
**forbids touching the canon** (L126). This is exactly the falsification bar
CAPABILITY-CLUSTERS demands of every shipped capability.

The misalignments below are all *fine-grained* (enum-placement, one bespoke
`apply` flag, one provenance edge under-specified). None is structural. The
example-not-core framing is correct and should not change.

---

## Canon citations

- **Domain bundle = example extension, not core.** CAPABILITY-CLUSTERS L16 lists
  `music (domain bundle)` with disposition **"example extension (`examples/music.py`,
  loaded via `extra_capabilities`)"** — the *exact* model the spec follows. CORE.md
  CLAUDE.md echoes it: *"Domain capabilities live OUT of the core as example
  extensions in `examples/`."* Spec L131-141 ("Where it lives") cites this verbatim.
- **The absorption thesis (the "few primitives" verdict).** CAPABILITY-CLUSTERS
  L26-43: *"Most clusters are facets of the four concepts, not new top-level
  primitives … the four concepts + the engine absorb the entire surface"* (~0.9
  confidence, L38-43). CORE.md:137-141: *"The whole capability landscape … the four
  concepts + the engine absorb it all; the only net-new specs were `delegate` and
  `reflect`."* Novel adds **no** new primitive — it is pure Capability + Memory
  (ontology) + Lifecycle (gated skill). The thesis holds.
- **Capability-owned ontology, nothing leaks to core.** CORE.md:131-133: *"an
  extensible, capability-owned ontology — the core defines a base; each capability
  contributes its own node types / skills / template-schemas (`Capability.ontology`),
  merged strictly onto the core."* `agency/ontology.py:104-126` (`Ontology.extend`)
  enforces this: nodes strict (no redefinition), enums **widen-only**, skills/schemas/
  templates unique-name. Spec L143-187 lives entirely inside this fragment.
- **Role-tagged verbs.** CORE.md:26-29 + `specs/capability.md:18-23` define
  `act`/`transform`/`effect`. Spec's verb table (L189-203) tags all six; role-split
  is correct (structural truth = `transform`, craft write = `act`, disk write =
  `effect`).
- **Gates are elicit-gated Lifecycle templates.** CORE.md:47-62: *"a skill is a
  Lifecycle template: a graph of atomic Capability steps + Gates … a gate that needs
  a human is just an `elicit` → the Lifecycle pauses at `input-required`."*
  `examples/music.py:22-43` (the `album-concept` 7-phase skill, final phase
  `gate: "hard"`) is the precedent; spec's `work-concept` skill (L182-187) mirrors it
  one-to-one. `agency/skill.py` walker + `agency/capabilities/gate.py` (`gate.check`
  → PASSED / BLOCKED_ON + `input-required` pause) both exist, so `pre_drafting_gate`
  composing `gate.check` (L109-114, L198) is real composition, not new machinery.
- **transform/Schema-validate pair, not bespoke.** CORE.md:64-80: Schema +
  Template form a generate/validate pair; *"a Schema … powers `validate`/`check`."*
  `ncp_validate` (transform, real `jsonschema`) and `coherence_check` (transform,
  pure) are exactly this — decidable, replayable, no graph write (spec L86, L195-197).

---

## Misalignments

**M1 — `severity` enum is hung on a node that doesn't carry it (CORE.md:131-133;
ontology.py:136-138).** Spec L168 declares `("Coherence", "severity"): {"fail",
"warn", "info"}` but the parenthetical admits it lives "on violation items," and the
`Coherence` node schema (L159) is only `[work, status, violations]` — it has no
`severity` field. `Ontology` enums constrain a `(label, field)` pair on the *node*
(`ontology.py:136`); an enum keyed to a field that never appears on the node is dead
weight that never fires. Violation items are sub-objects inside the report artefact,
not graph nodes. **This is the one place the ontology fragment is mis-modelled.**
Either drop the `severity` enum (validate items inside the `coherence-report` artefact
schema instead) or promote `Violation` to a real node type if items must be queryable.

**M2 — `revision_pass` enum is keyed to nothing (same mechanism).** Spec L166-168
declares the `revision_pass` enum "carried on a `revision_pass` artefact field," but
the revision skill is deferred to v2 (L168, L376) and no v1 node/artefact carries the
field. An enum with no field to constrain is inert. Defer the enum with the skill, or
note it as documentation-only (not an `OntologyExtension` enum) until v2.

**M3 — `scaffold`'s `apply=True` is a bespoke flag where the canon already has a
discipline (CORE.md:21-22 deltas; specs/capability.md effect role).** Spec L88-91
invents an `apply` flag to gate the disk write, calling it the "graph analogue of
`dry_run`." That's reasonable, but the canon's effect discipline is that an `effect`
*is* the external side-effect and provenance records what reached the world — there is
no canonical `dry_run`/`apply` toggle in CORE.md or `specs/capability.md`. Risk: a
session reads "mirroring Agency's `dry_run` discipline" (L90) and hunts for a
`dry_run` primitive that does not exist. **Either** cite where this discipline lives
(it appears to be spec-local invention) **or** reframe: the default is graph-only
record (an `act`/`effect` that records the manifest), and disk materialization is a
*separate* `effect` verb — keeping one verb = one role cleaner than an `effect` that
sometimes has no side-effect.

**M4 — override-edge under-specified against the enumerated edge set (ontology.py:41-45;
CORE.md:131-133).** Spec references "a supersede/override edge for `promote_premise`
and the gate-override audit" (L173-174) and "an explicit override edge" (L113, L198)
but never names it. The core edge set is *closed* (`link()` rejects unknown edges,
`ontology.py:111,141-142`); `SUPERSEDED_BY` exists but an override is not a
supersession. The `OntologyExtension.edges` set must declare the exact override edge
label (e.g. `OVERRIDDEN_BY` or `FORCED`), or `pre_drafting_gate(force=True)` will hit
a runtime "unknown edge" rejection. (`promote_premise` is deferred to v2, so its
supersede edge can defer too — but the *gate-override* edge ships in v1.)

**M5 — `conceptualize` provenance edge names a Template that the extension never
defines (CORE.md:64-80).** Spec L194 says the `conceptualize` artefact is
`DERIVED_FROM the work-concept Template`. But the `OntologyExtension` declares
`skills={work-concept}` and `schemas={…}` — **no `templates={…}`** (contrast
`music.py`, which also omits templates, but `music.conceptualize` builds the body
inline and does *not* claim a `DERIVED_FROM Template` edge). Either add a `work-concept`
entry to `templates=` (so `ctx.render` + the `DERIVED_FROM` edge resolve), or drop the
`DERIVED_FROM Template` provenance claim and build inline like `music` (L51-55). As
written the acceptance bullet (L194) references a node that won't exist.

---

## Recommended aligned framing

**1. Example-not-core is settled and correct — do not revisit for "weight."** The
spec's own rebuttal (L137-141) is canon-true: the engine's `Ontology.extend` touches
only nodes/edges/enums/skills/schemas/templates — *it has zero awareness of data
files* (`ontology.py:104-126`). The 303-entry Dramatica dataset, the draft-07 NCP
schema, and `jsonschema` are the **capability's private concern**, vendored under
`examples/novel/data/`. A vendored reference dataset is genuinely new (no prior
example carries one), but it rides the *existing* extension contract — it is not a
reason to promote to core, and promoting it would re-introduce the bloat the
"few-primitives" verdict (CLUSTERS L26-43) exists to prevent. **The heavy domain is
the strongest possible proof of absorption, precisely because it stays out-of-tree.**

**2. Keep the ontology fragment hermetic — every enum must key a real field on a
real node.** The fix for M1/M2 is the same principle: an `OntologyExtension` enum is a
`(label, field)` constraint enforced on graph nodes (`ontology.py:136-138`). Enums for
fields that live only inside artefact JSON belong in the artefact **schema**
(`ctx.validate`), not the node enum map. Audit all four enums (L163-168) against the
node schemas (L151-159): `pov` keys `Chapter.pov` ✓; `Coherence.status` keys
`Coherence.status` ✓; `severity` and `revision_pass` key nothing ✗.

**3. Name every edge the extension uses.** The closed edge set is a *feature*
(drift-proof provenance, CORE.md:38-46). v1's extension must declare exactly the new
edges it writes — `COHERES_WITH` (already named, L170) plus the gate-override edge
(M4). Reuse core edges for everything else, as the spec already plans (L171-174).

**4. One verb = one role.** The `transform` verbs are pristine (pure, no graph/disk
write — L86, the cleanest part of the spec). Keep `scaffold` honestly an `effect`
(M3): if its default path writes nothing, it is not an effect. Prefer record-on-`act`
+ a separate materialize-`effect`, or document the `apply` flag as a deliberate
spec-local extension of the effect contract (not a citation to a non-existent
`dry_run` primitive).

---

## Must-change list (vision gate — block until resolved)

1. **M4 (blocking): declare the gate-override edge** in `OntologyExtension.edges`
   with an exact label, or `pre_drafting_gate(force=True)` raises "unknown edge" at
   runtime (`ontology.py:111,141`). Ships in v1.
2. **M1 (blocking): fix the `Coherence.severity` enum** — it keys a field the node
   doesn't have, so it never fires. Move item-severity into the `coherence-report`
   artefact schema, or model `Violation` as a node.
3. **M5 (blocking): reconcile the `conceptualize` → `DERIVED_FROM Template` claim**
   (L194) with the absent `templates=` map — add the template or build inline like
   `music.py` and drop the edge claim.
4. **M2 (minor): defer the `revision_pass` enum** with its v2 skill, or mark it
   documentation-only — it constrains no v1 field.
5. **M3 (minor): re-anchor or rename the `apply`/`dry_run` framing** — cite where
   the discipline lives in canon or own it as a spec-local effect-contract extension;
   do not imply a `dry_run` primitive exists.

**Not a finding:** example-vs-core placement (correct), role-tagging (correct),
no-core-edit guardrail (correct, L126/L327-329), gate-as-composition (real,
`gate.py`+`skill.py` exist), transform-validation pair (canon-true, CORE.md:64-80).
