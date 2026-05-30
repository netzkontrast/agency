# REVIEW — Spec 010 Novel Domain Capability

**Reviewer:** spec-panel (domain-expert lens) · **Date:** 2026-05-27
**Subject:** `/home/user/agency/Plan/010-novel-domain/spec.md`
**Ground truth:** `the-agency-system @ 0a6a9e71` — read the actual Plan specs AND
the shipped server implementation under
`servers/agency-mcp/src/agency_mcp/{handlers/novel,lib}/`.

---

## Verdict

**Conditional accept — re-base the spec on the SHIPPED code, not the source specs.**

The architectural translation is sound and genuinely faithful to the Agency
substrate: novel-as-`OntologyExtension`, structural-truth-as-`transform`,
editorial-pipeline-as-gated-skills, the 6-gate as a `gate.check` composition, the
`apply=True` disk-export flag mirroring `dry_run`. The skill-walker / hard-gate
contract the spec leans on is real (`agency/skill.py:40,71`) and the
`extra_capabilities` extension path is the right home.

BUT the spec was written against the-agency-system's **Plan specs** (the
aspirational contracts) and inherited their claims wholesale. The **shipped
implementation diverges materially** from those specs, and the spec repeats the
source specs' own inaccuracies as if they were verified facts. Three of the
"Done When" acceptance bullets describe data shapes and behaviours that **do not
exist in the real domain**. If a Jules session implements this spec literally it
will faithfully reproduce a fiction. Every numeric and structural claim below must
be corrected against the shipped artefacts before this goes to a session.

The core-vs-examples placement, the dependency posture, and the v1 scope cut are
all defensible (with one correction on `jsonschema`). The blocking issues are
**fidelity**, not architecture.

---

## Source-grounded corrections (cite: the-agency-system path:line)

### 1. The ontology is **303 entries, not 304** — and the kind breakdown is wrong

The spec says "304-entry ontology" **six times** (lines 36, 38, 91, 182, 209, 263)
and "304 entries: 4 Classes, 16 Types, 64 Variations, 64 Elements, plus 156
supporting term entries" (the-agency-system `Plan/012-…/spec.md:42`).

The **shipped** `reference/novel/dramatica/ontology.json` actually carries
`{"entries": [...]}` of length **303**, with this kind distribution (measured):

```
archetype 8 · character-dynamic 4 · class 4 · concept 38 · dynamic-pair 65
element 63 · plot-dynamic 4 · quad 35 · throughline 4 · type 16 · variation 62
```

So: **63 Elements (not 64), 62 Variations (not 64), 16 Types, 4 Classes** — and
crucially `dynamic-pair` and `quad` are their OWN node kinds (65 + 35 entries),
not relationships derived from elements. The decidability brief itself
(`Plan/013-…/references/dramatica-decidability.md:7`) already records the correct
"303… 62 variations, 63 elements" breakdown — the 012 spec's "304 / 64+64" was
never reconciled with what shipped. **Do not pin "304" in an Agency acceptance
test.** Pin "the count of the bundled `entries` array" or assert ≥ 300, and copy
the file's real length into the `.sha` provenance.

### 2. The "75 canonical dynamic-pair reciprocities" number is unverified and likely wrong

Spec line 216: "The 75 canonical dynamic-pair reciprocities are covered
parametrically." This is lifted verbatim from `Plan/012-…/spec.md:58,156` ("All
75"). The shipped ontology has **65 entries of `kind: dynamic-pair`** and only
**108 entries carrying a `dynamic_pair_id`** field, yielding **54 distinct
reciprocal `(a,b)` pairs** when de-duplicated (measured). The number 75 comes from
a vendor reference markdown (`dynamic-pairs-index.md`) that was never reconciled
with the JSON that actually shipped. **Do not hard-code 75.** Extract pairs from
the bundled data at test-collection time (the 012 spec's own anchor 012.4 says
"extract… not hard-coded" — then contradicts itself by asserting "exactly 75").

### 3. The NCP top-level shape is `{schema_version, story}` — NOT `{storyform, players, scenes, metadata}`

This is the most serious correction. Spec line 158 defines the `ncp` artefact
schema as `[storyform, players, scenes, metadata]`, and line 88/166 asserts
`ncp_validate` checks against "the pinned NCP-v1.3.0 schema." The **shipped**
`state/schema/ncp.schema.json`:

- is **JSON Schema draft-07**, not "Draft 2020-12" (spec lines 219, 269 are wrong).
- has top-level `required: ["schema_version", "story"]` with only those two
  properties.
- nests everything under `story` (`required: [id, title, logline, created_at,
  narratives]`, props include `genre, ideation, narratives`).

There is **no `storyform`/`players`/`scenes`/`metadata` top-level shape anywhere
in the shipped NCP.** That shape is the 012 *spec's* acceptance fiction
(`Plan/012-…/spec.md:166`) that the implementation did not honour. The shipped
coherence checks read a THIRD, different shape:
`ncp["storyform"]["throughlines"]["mc"|"os"|"ic"|"rs"]` (see
`handlers/novel/coherence.py:111`) — which matches neither the schema nor the
spec. **The Agency spec must decide which NCP shape it is porting and state it
explicitly**, because the source repo ships three mutually-inconsistent ones. The
honest port is the draft-07 `{schema_version, story{…narratives…}}` schema, with
the coherence transform operating on a documented projection of it.

### 4. The "11 decidable checks against the ontology" are, as shipped, **fixture-discriminating heuristics** — not decidable ontology traversals

Spec lines 84-85, 196-205 present the 11 checks as "pure functions over the
bundled ontology + an NCP doc (no LLM)… decidable, replayable." The decidability
brief sells the same story. But read `handlers/novel/coherence.py`:

- `check_ktad_coverage` (line 145): `if concern_id == "t.progress": FAIL` — a
  single hard-coded magic value matching one broken fixture. No quad traversal.
- `check_mental_sex_problem_solving` (line 182): `if mental_sex == "holistic" and
  resolve == "change": FAIL`. Hard-coded fixture discriminator.
- `check_quad_completeness` (line 247): `if problem == "el.pursuit": FAIL`. Magic
  value.
- `check_signpost_permutation` (line 165): `if sp[0] != "t.past": FAIL`. No
  permutation table.
- `check_approach_concern` (line 228): `if approach == "be-er" and concern ==
  "t.past": FAIL`. Hard-coded.
- Even `check_dynamic_pair_reciprocity` (line 110) has an "ontology incomplete"
  fallback that decides on `mc_dyn != os_dyn` when the navigator can't resolve.

Only `check_storybeat_moment_refs` (line 273, a genuine FK traversal) and the
*happy path* of `check_dynamic_pair_reciprocity` are truly decidable against data.
`handlers/novel/structure.py` is a **pure stub** — every one of its 7 checks is
`return {"status": "PASS"}` (lines 4-10).

**Implication for the Agency spec:** claiming `coherence_check` is a clean
`transform` that "runs the 11 decidable checks against the vendored Dramatica
ontology" overstates the available source by a wide margin. The Agency port has a
choice: (a) port the heuristics honestly and label them as such (cheap, faithful
to what runs, but not "decidable"); or (b) build the *actually decidable* checks
the brief describes (real work — needs the quad reverse-index, the KTAD
membership test, the precompiled signpost-permutation table). **The spec must pick
one and not pretend (a) is (b).** Recommend (b) for the 2-3 checks that are
genuinely data-decidable from the bundled ontology (`pair_reciprocity`,
`ktad_coverage`, `quad_completeness`, `storybeat_moment_refs`,
`throughline_partition`, `slot_fill`) and explicitly defer the rest as
"heuristic / judgement → skill" rather than mislabel them `transform`.

### 5. Check-name drift: `resolve_outcome_judgment` vs shipped `resolve_mirror`

Spec line 201 lists `resolve_outcome_judgment` as one of the 11 keys (matching the
brief, `dramatica-decidability.md:19`). The **shipped** `_CHECKS` registry
(`coherence.py:315`) has **`resolve_mirror`** instead (MC/IC resolve must differ),
not the brief's outcome/judgment table-lookup. The shipped 11-key set is:
`dynamic_pair_reciprocity, ktad_coverage, throughline_partition,
signpost_permutation, resolve_mirror, mental_sex_problem_solving,
crucial_element_placement, approach_concern, quad_completeness,
storybeat_moment_refs, slot_fill`. The Agency spec's compact-report key list (and
any test) must match whichever set it ports — do not copy the brief's names if
porting the shipped behaviour.

### 6. `coherence_correct` is **NOT_IMPLEMENTED** for real fixes in the source

Spec lines 186, 205 promise `coherence_correct` "applies mechanical autofixes…
records a `Coherence` node + a corrected `Artefact`." The shipped
`novel_coherence_correct` (`coherence.py:350`) returns
`{"error": "NOT_IMPLEMENTED"}` for `dry_run=False`; only the dry-run planning
branch exists, and even that only plans `dynamic_pair_reciprocity`. The Agency
spec is free to *build* the autofix (it would be net-new), but it should not imply
it is "porting" a working corrector — it is not. Scope it as new work or defer it.

### 7. The substrate is disk + StateCache in the source, graph + Memory in Agency

The source novel domain is **disk-first**: works live as files under
`novels/{author}/works/{genre}/{slug}/`, indexed into a `StateCache`
(`state/cache.py:22`), with no graph nodes (`grep` for graph/`record` in the novel
handlers returns nothing). Agency's substrate is the bi-temporal graph. The spec
correctly inverts this (graph canonical, disk an optional `apply=True` export,
Open Q 5) — this is a genuine and correct *re-architecture*, not a port, and the
spec should say so plainly rather than framing the layout as "mirrored." The
14-entry manifest (7 root files + 7 subfolders) IS faithful to
`Plan/010-…/spec.md:80-81` (chapters/scenes/characters/world/revisions/art/research
+ work/premise/cast/dramatica/outline/ncp/README). Good.

### 8. The cited research file does not match the spec

`/home/user/agency/research/capability-specs/specs/novel.md` (the spec's Evidence
line 292) describes a **completely different** capability: `agency/capabilities/
narrative.py` with verbs `outline` / `draft` / `review_arc` — not `examples/
novel.py` with the 11 verbs in this spec. The spec has clearly superseded that
research stub; either update the research file or drop the citation, because it
will mislead an implementer who opens it.

---

## Missing depth vs the real domain

The spec actually scopes UP from the bare research stub, which is good. But three
real-domain capabilities present in the source are silently dropped without being
named in the scope cut:

- **Premise-idea lifecycle as state, not nodes.** Source `ideas.py` keeps premise
  ideas in `state.json:novel.premise_ideas` with a `draft → promoted` status and a
  `promoted_to` backref (`Plan/011-…/spec.md:111-112`). The spec's `Premise` node +
  `promote_premise` verb captures the spirit but loses the `status`/`promoted_to`
  bookkeeping — fine for v1, but call it out.
- **Status state-machines.** Source ships `status.py` with legal-transition tables
  at work/chapter/scene granularity (`Plan/011-…/spec.md:113`). The Agency spec
  folds status into Lifecycle implicitly but never maps the transition table. The
  `revision_pass` enum is captured; the entity-status enum is not.
- **`force=True` override + audit trail.** The source 6-gate writes
  `force_overrides[]` with timestamp+caller when a gate is bypassed
  (`Plan/014-…/spec.md:41`, anchor 014.3). The Agency spec's `pre_drafting_gate`
  records `BLOCKED_ON` on failure but says nothing about the override path. In the
  graph model the natural analogue is an explicit supersede/override edge — specify
  it, or the gate is stricter than the source (no escape hatch).

Correctly-captured depth worth affirming: the 6 gate names
(`dramatica_confirmed, ncp_valid, premise_locked, cast_complete, pov_declared,
sources_verified`) match the shipped `gates.py:81-191` exactly; the 4 revision
passes (`structural/line/copy/proof`) match `Plan/014-…/spec.md:42`; the
"tools assert structure, skills assert meaning" boundary (Q1–Q5 scene bridge stays
a skill) is faithful to `dramatica-decidability.md:48`.

---

## Open-Questions triage

| # | Spec's question | Triage |
|---|---|---|
| 1 | Core vs examples | **Settled: examples/ for v1.** Matches `music`, matches CLAUDE.md ("domain capabilities live OUT of the core"). The vendored data weight is not a reason to promote — it is the capability's private concern (see Q2). Revisit only if a second domain needs the same dataset. |
| 2 | Dramatica/NCP vendoring home | **Settled: `examples/novel/data/` is correct.** The engine's strict ontology-merge has zero awareness of data files and needs none (confirmed: `ontology.py:104 extend()` only touches nodes/edges/enums/skills/schemas/templates). Data is purely the capability's concern. Add a `.sha` sidecar as the spec proposes — the shipped repo does exactly this (`ncp.schema.json.sha`). |
| 3 | `jsonschema` dependency | **DECIDE NOW, and the spec's lean is wrong.** The spec leans "hand-rolled stdlib to keep core dep-free." But (a) the **shipped** validator uses real `jsonschema` (`lib/ncp/validator.py:8`), and (b) this is an `examples/` capability, NOT the core — `requirements.txt` core purity is irrelevant to an out-of-tree example. Add `jsonschema` as an **example/extra** dependency (or a `requirements-examples.txt`), use the real library, and validate against the **draft-07** schema that actually ships. Hand-rolling a validator to dodge a dep in an *example* is wasted effort and a fidelity regression. |
| 4 | v1 scope cut | **Mostly right — tighten (see below).** |
| 5 | Disk vs graph source of truth | **Settled: graph canonical, `apply=True` is an optional export `effect`.** This is the correct Agency re-architecture (the source is disk-first; Agency is graph-first). Keep. |
| 6 | Skill walker vs `gate` composition duplication | **Intentional and fine — but document the split.** `pre_drafting_gate` (verb) = programmatic/composable; `pre-drafting-check` (skill) = walkable UI. The source ships BOTH a `novel_run_pre_drafting_gates` tool AND a `pre-drafting-check` skill (`Plan/014`, `Plan/015`), so the duplication is faithful. State that the skill delegates to the verb (one source of truth), not that they reimplement each other. |

---

## Must-fix list (blocking)

1. **Replace every "304" with the real bundled count (303) — or assert the array
   length, not a literal.** Fix the kind breakdown in the Why (63 elements, 62
   variations, dynamic-pair/quad as first-class kinds). Lines 36, 38, 91, 182,
   209, 263.
2. **Fix the NCP shape.** Drop the `ncp` schema `[storyform, players, scenes,
   metadata]` (line 158). The shipped schema is draft-07 `{schema_version, story}`
   with `story.narratives`. State which NCP shape the port targets and make
   `ncp_validate`/`ncp_compile`/`coherence_check` agree with it. Fix "Draft
   2020-12" → "draft-07" (lines 219, 269).
3. **Stop hard-coding "75" dynamic pairs.** Extract from the bundled data at test
   time; the real count is ~54 distinct reciprocal pairs (line 216).
4. **Re-label the coherence checks honestly.** Either port the shipped heuristics
   and call them heuristics, or build the genuinely-decidable subset and defer the
   rest to skills. Do not assert "11 decidable checks against the ontology" when
   the source ships fixture-discriminators + a `structure.py` stub (lines 84-85,
   196-205). Align the 11 key names with whichever set ships (note
   `resolve_mirror` ≠ `resolve_outcome_judgment`).
5. **Reframe `coherence_correct` as net-new, not a port** (it is `NOT_IMPLEMENTED`
   upstream), or move it to v2.
6. **Resolve `jsonschema`: add it as an example dependency and use the real
   library** against the draft-07 schema. Reverse the "hand-rolled" lean (Open
   Q3).
7. **Add a `force`/override path to `pre_drafting_gate`** (graph-edge analogue of
   the source's `force_overrides[]` audit), or document its intentional removal.
8. **Fix or drop the stale research-file citation** (line 292) — it describes a
   different `narrative.py` capability.

## Should-fix (non-blocking)

- Name the dropped depth in the scope cut: premise `status`/`promoted_to`,
  entity status-transition tables, the gate override audit.
- The `affects:` list (lines 8-21) is large for "4 jules sessions." The data
  files + 5 helper modules + 3 test files + example are ~14 files of real code
  plus a vendored dataset. Either raise the estimate or tighten v1 (below).
- `dramatica_lookup` is described as resolving "elements/classes/variations + check
  dynamic-pair reciprocity" — the shipped navigator (`navigator.py`) does exactly
  this via `by_id/by_class/by_type/by_variation/by_element/by_dynamic_pair/
  check_dynamic_pair_reciprocity`. This one IS a faithful, clean port — affirm it
  and use it as the reference signature.

---

## Recommended v1 scope cut

The spec's proposed v1 (scaffold + conceptualize + dramatica/ncp/coherence +
6-gate + 4 skills + scene-prompt) is too wide given the fidelity work needed.
**Cut to a faithful, honest, decidable core:**

**v1 (one capability, prove the contract at fidelity):**
- `scaffold` (effect, graph-canonical, `apply=True` disk export) — the 14-entry
  manifest. Faithful, low-risk.
- `conceptualize` (act) + the `work-concept` gated skill ending in a hard confirm
  gate — the direct `music.album-concept` analogue. This is the proof that matters.
- `dramatica_lookup` (transform) — clean port of the shipped navigator. **Use the
  real 303-entry bundled dataset.**
- `ncp_validate` (transform) — real `jsonschema` against the **draft-07** shipped
  schema. Never raises on bad data.
- `coherence_check` (transform) — port ONLY the **genuinely decidable** checks:
  `pair_reciprocity`, `storybeat_moment_refs`, `throughline_partition`,
  `slot_fill`, and (if the quad reverse-index is built) `ktad_coverage` +
  `quad_completeness`. Emit the compact `{status, violations, checks{…}}` report
  (PASS carries no items). Label the rest "needs-judgement → skill" — do not ship
  fixture-discriminators.
- `pre_drafting_gate` (act) composing `gate.check` over the 6 gates, WITH an
  override/audit path.

**Defer to v2 (explicit, in the scope-cut section):**
- `ncp_compile`, `coherence_correct` (both net-new vs source), `analyze_prose`
  beyond a trivial rule set, `promote_premise` status bookkeeping, the
  non-decidable coherence checks, `build_scene_prompt` and the other 9
  prompt-builders, `manuscript-revision` + `scene-bridge-audit` skills, promo
  authoring, the 32-skill prose catalogue.

This keeps v1 to **two jules sessions** (capability + ontology + data vendoring;
then the gated skills + example + tests), proves the same two novelties the spec
claims (vendored dataset through `OntologyExtension`; a real schema-validation
`transform`), and — critically — ships something that is *true to the source*
rather than true to the source's unbuilt specs.
