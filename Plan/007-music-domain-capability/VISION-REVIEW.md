# Vision-Alignment Review — Spec 007 (Music Domain Capability)

> Reviewer: vision-alignment pass against the canon (`docs/vision/`).
> Subject: `Plan/007-music-domain-capability/spec.md`.
> Method: spec-panel-style critique (Fowler / Wiegers / Newman / Cockburn lenses)
> keyed to the four alignment questions, each ruling cited to CORE.md /
> CAPABILITY-CLUSTERS.md line numbers.

## Alignment verdict

**ALIGNED WITH RESERVATIONS — proceed after the Must-change list.**

The spec is *structurally* faithful to the canon on three of four axes (it stays
in `examples/`, it role-tags verbs into `act`/`transform`/`effect`, and it routes
side-effects through injected drivers that are Spec-002 boundaries). It is in
**tension with the canon on the question that matters most**: whether a single
*example* should carry 89 verbs at all. The canon's whole thesis is *collapse*
(CORE.md:137-141; CLUSTERS:26-35) — "Multiplying concepts would re-introduce
bloat" (CLUSTERS:31). Porting bitwize's flat 89-tool surface 1:1, even role-tagged
and driver-backed, risks **re-importing the very bloat the example exists to
disprove**. The example's job is to *prove the contract*, not to *mirror the
legacy tool count*. This is fixable by reframing (see Recommended framing); the
mechanics are right, the ambition is mis-scaled.

Quality scores (panel composite, 0-10):
- Canon-disposition fidelity (example-not-core): **8.5** — correct home, but Why/Done-When lean on "retire the entire bitwize surface," a core-replacement framing.
- Role-tag + OntologyExtension contract: **9.0** — clean.
- Gated-skill / elicit model: **7.5** — gates land on `gate.check`, but `gate.check` is *computed*, not `elicit`; the human-in-loop canon (CORE.md:57-62) is under-served.
- Drivers as engine boundaries: **8.5** — correct shape; one core edit (engine injectors) leaks unless 002's `DriverRegistry` lands first.

## Canon citations (the load-bearing lines)

- **CLUSTERS:16** — the `music` row disposition is verbatim **"example extension
  (`examples/music.py`, loaded via `extra_capabilities`)"**. Music is explicitly
  NOT a core capability. The spec honors this (spec.md:76-80, Open Q #1 resolved
  to `examples/`).
- **CLUSTERS:10-24** — every cluster is "a *facet* of an existing concept" or a
  "candidate capability," arriving by "dropping a file … each self-registers and
  owns its ontology fragment" (CLUSTERS:6-8). The unit of growth is **one file =
  one capability owning one ontology fragment** — not 89 hand-enumerated tools.
- **CLUSTERS:26-35 (The verdict)** — "Most clusters are **facets of the four
  concepts**, not new top-level primitives … **Multiplying concepts would
  re-introduce bloat.**" The canon's value is *fewer*, not *complete-coverage*.
- **CORE.md:9-18** — "**Code-mode IS the contract** … the public surface is
  exactly `search · get_schema · execute`." A capability does NOT publish a wide
  tool menu; the agent discovers verbs via `search` and chains them inside
  `execute`. A 89-tool catalog is in tension with "lean — no four-verb surface."
- **CORE.md:28-29** — Capability verbs are "**role-tagged**: `act` … `transform`
  … `effect`." The spec's eight clusters comply (spec.md:157-170).
- **CORE.md:47-62 (Skills are atomic, gated, progressively-disclosed)** — "a
  skill is a **Lifecycle template: a graph of atomic Capability steps + Gates**,
  walked step-by-step." "**Gates / intent-verification / human-in-the-loop are
  `elicit` steps**" — the Lifecycle pauses at `input-required`, the answer
  resumes it. This is the canon's guard-rail mechanism, and it is `elicit`, not
  an imperative tool call.
- **CORE.md:131-133** — "an **extensible, capability-owned ontology** … each
  capability contributes its own node types / skills / template-schemas
  (`Capability.ontology`), merged **strictly** onto the core." The spec's single
  `OntologyExtension` (spec.md:99-106) is exactly this contract.
- **CORE.md:137-141** — the survey "Verdict: the four concepts + the engine
  absorb it all; the only net-new specs were `delegate` … and `reflect`." Music
  was surveyed and **absorbed** — it produced **no** net-new primitive. The
  example is the *proof of absorption*, so it must not behave like a new surface.

## Misalignments (panel findings, severity-ranked)

### CRITICAL — M1: Surface-count over-reach (Fowler / CLUSTERS:31, CORE.md:9-18)
The spec frames success as "**89 tools collapse to one capability**" but then
**enumerates all 89 as 1:1 verbs** (spec.md:208-300, "all 89, nothing dropped").
"Collapse" in the canon means the *concepts* collapse (89 tools → role-tagged
verbs over four concepts + drivers), NOT that the example must *reproduce every
legacy tool*. An example carrying 89 auto-wired MCP tools is, from the engine's
point of view, an 89-tool surface — the same flat menu CLUSTERS:31 warns against,
merely relocated to `examples/`. The canon's growth unit is "a file that owns an
ontology fragment" (CLUSTERS:6-8), proven by a *representative* slice, not an
exhaustive port. **The "nothing dropped" success criterion is itself the
misalignment**: it optimizes for legacy parity, which the canon never asks for.

### MAJOR — M2: "Retire the entire bitwize surface" reads as core-replacement (Cockburn / CORE.md:137-141)
Why/Done-When (spec.md:46-47, 84-87) cast 007 as the thing that lets "the entire
bitwize surface … be retired." That is a *product-migration* goal, not an
*example-extension* goal. The canon's stakeholder for `examples/music.py` is **a
plugin author learning the contract** (CORE.md:131-133; CLAUDE.md "proving the
extension contract end to end"), not a bitwize user awaiting feature-parity. The
example proves the *shape*; whether bitwize is retired is downstream and out of
the canon's scope for an example file. Reframe the goal as "prove the full
clustered contract on a real domain," with completeness as illustrative, not
contractual.

### MAJOR — M3: Gates are `gate.check` (computed), under-serving the `elicit` canon (CORE.md:57-62)
The spec maps bitwize's workflow chains onto `gate.check` (spec.md:308-320),
which is correct for the *computed* predicate (gate.py:20-32 records PASSED /
BLOCKED_ON). But CORE.md:57-62 is explicit that **gates / intent-verification /
human-in-the-loop are `elicit` steps** that pause the Lifecycle at
`input-required`. bitwize's pre-generation and release gates are precisely the
human-in-loop "is this ready?" checkpoints — the album-concept Phase-7 hard gate
(music.py:40-41) is `elicit`-shaped, not `gate.check`-shaped. The spec conflates
the two: a *computed* aggregate gate (the 8 checks) is fine for the machine-checkable
part, but the human confirmation at the end of pre-generation / release-qa is an
`elicit` step (the `lifecycle_gate` engine tool, engine.py:106-122), not
`gate.check`. The spec should name which gates are computed (`gate.check`) and
which are human (`elicit` / `lifecycle_gate`), per the canon's distinction.

### MINOR — M4: The one core edit (engine injectors) is a canon smell (Newman / CLUSTERS:6-8)
spec.md:340-345 and Open Q #2 concede that surfacing four new drivers needs an
edit to `agency/engine.py:55` (`registry.injectors`). The canon's contract is
that **adding a capability is adding a file** (CLUSTERS:6-8; CORE.md:123-125
"adding a capability is adding a file"). An `examples/` file that *requires a
core engine edit* violates "no wiring." The spec correctly flags this and points
at Spec 002's `DriverRegistry` (`ctx.drivers.get(...)`, 002 spec.md:104-109) as
the zero-core-edit path. **This must be a hard dependency, not an Open Q**: 007
must not touch `engine.py`. If 002's registry has not landed, 007 is blocked, not
licensed to edit core.

### MINOR — M5: Domain verbs that shadow core capabilities (Fowler / CORE.md:28)
`search`, `list_skills`, `get_skill` (map rows #36, #39, #40) overlap the engine's
public `search` (CORE.md:11) and `plugin.help` / `develop.reference`. Open Q #5
resolves this to "thin delegating verbs that `ctx.call` the core." Acceptable, but
each such shim is an MCP tool that *duplicates a discovery the canon already
provides via `search`*. Prefer dropping them in favor of the core surface unless
a domain-specific projection is genuinely needed; every redundant verb is one more
entry in the menu the canon wants lean.

## Recommended aligned framing

**1. Example-not-core (the headline ruling).** Keep music in `examples/`
(correct), but rewrite Why/Done-When so the deliverable's *purpose* is "prove the
clustered-capability + driver-boundary + gated-skill contract end-to-end on a
real, messy domain," NOT "achieve 1:1 parity so bitwize can be retired." The
canon's example exists to *falsify* the claim "the four concepts absorb the
surface" (CORE.md:39 "~0.9 that the four concepts + the engine absorb the entire
surface") — i.e., to show a hard domain *fits*, not to clone it.

**2. How much surface should a single example carry?** A *representative* slice
per cluster — enough to prove each role (`act`/`transform`/`effect`) and each
driver boundary fires, plus the two gated skills — NOT all 89 verbs. The panel
recommendation: ship **one or two exemplar verbs per cluster** as real auto-wired
verbs (≈12-16 verbs total), keep the full 89-row migration **map** as an appendix
documenting that every legacy tool *has a home* in the taxonomy, and mark the
long tail "covered-by-pattern, port-on-demand." This preserves the canon's "lean
surface" (CORE.md:9-18) while still proving completeness *of the contract* (the
map shows nothing is unmodelable). The provenance bonus (spec.md:302-306) is the
real proof point — it is what bitwize *cannot* do — so foreground it.

**3. Gates.** Split the gate mapping by mechanism per CORE.md:57-62: machine-checkable
aggregate → `gate.check`; the terminal human "ship it?" confirmation → an `elicit`
step (engine `lifecycle_gate`), exactly like album-concept Phase 7. Name both in
the gated-skill table.

**4. Drivers.** Keep the five-driver taxonomy (it is clean and matches Spec 002
Option B, spec.md:129-154). Make **"007 makes zero edits to `agency/engine.py`"**
a Done-When line; route all driver injection through Spec 002's `DriverRegistry`.
Remove the `engine.py` row from the optional `affects:` escalation.

## Must-change list (blocking)

1. **Re-scope the surface (M1).** Replace the "89 verbs, nothing dropped" success
   criterion (spec.md:84-87, 208-300 as *contract*) with "a representative verb
   per cluster proves each role + driver + both gated skills; the 89-row map is a
   documentation appendix proving every legacy tool has a taxonomic home, long
   tail port-on-demand." The contract is the *taxonomy*, not the *count*.
2. **Re-frame Why/Done-When away from core-replacement (M2).** State the purpose
   as "prove the clustered contract on a real domain" (CORE.md:131-133, 137-141);
   demote "retire the entire bitwize surface" to a downstream, out-of-scope
   consequence. Foreground the provenance moat (the one thing bitwize can't do)
   as the headline proof.
3. **Forbid the core edit (M4) + fix the gate split (M3).** Add Done-When lines:
   (a) "007 modifies no file under `agency/` — drivers inject via Spec 002's
   `DriverRegistry`; if 002's registry is unlanded, 007 is BLOCKED, not licensed
   to edit `engine.py`"; (b) "terminal human gates use `elicit`/`lifecycle_gate`
   (CORE.md:57-62); only machine-checkable predicates use `gate.check`." Remove
   `engine.py` from `affects:`.

Non-blocking: prefer dropping `search`/`list_skills`/`get_skill` shims (M5) in
favor of the core surface; keep them only if a domain projection is demonstrably
needed.
