---
spec_id: "278"
slug: universal-frontmatter-discipline
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "149"
depends_on: ["149", "054", "080", "081", "163"]
vision_goals: [7, 6, 4, 2]
affects:
  - scripts/check_frontmatter.py
  - scripts/embed_frontmatter.py
  - Plan/_planning/frontmatter-baseline.txt
  - .github/workflows/test.yml
  - tests/test_universal_frontmatter.py
  - agency/_frontmatter.py
---

# Spec 278 — Universal frontmatter discipline (graph-embedded in every rendered file)

## Why

CLAUDE.md rule 2 says **the graph is the store; files are a rendered
view**. Today, only spec files carry structured frontmatter — the rest
of the rendered surface (skill READMEs, capability skill briefs, the
generated capability reference page, planning docs, music-cluster
briefings, novel chapter-briefings, the TODO roll-up, even the agency
welcome payload) renders WITHOUT round-trippable graph metadata, so
re-ingesting them loses provenance and the file→graph reverse map is
hand-built every time. Spec 149 cracked the door — `vision_goals:` on
specs — but the principle generalizes: **every file the substrate
RENDERS must carry the minimum graph slice needed to reconstruct its
node + outgoing edges from the file alone.** That is the only way the
file/graph duality stays lossless under rule 2.

This spec ships the universal frontmatter contract (which fields go on
which file type), the validator that gates regressions per Spec 054,
and the embedder that derives + writes frontmatter from the live graph
so authoring stays one-shot.

## Done When

- [ ] **`agency/_frontmatter.py` defines the universal contract** —
      typed schema per rendered-file kind:
      - `spec` (Plan/NNN-*/spec.md): `spec_id`, `slug`, `status`,
        `last_updated`, `owner`, `enhances?`, `depends_on?`,
        `vision_goals`, `affects?` (Spec 149 extension)
      - `skill` (skills/*/SKILL.md): `skill_id`, `capability`,
        `serves_intents?`, `triggers`, `last_synced`, `derive_source`
      - `capability_brief` (agency/capabilities/*/briefs/*.md):
        `capability`, `verbs`, `last_synced`, `derive_source`
      - `generated_doc` (docs/**/* with `<!-- doc-source: -->`):
        `doc_kind`, `derive_sources` (list of file:line refs),
        `last_synced`, `source_hash`
      - `template` (agency/capabilities/*/templates/*.md):
        `template_id`, `capability`, `cluster?`, `serves_phase?`,
        `agent_directive` (the `<!-- AGENT: -->` block index)
      - `planning` (Plan/_planning/*.md): `doc_kind`,
        `derives_from` (graph edge spec), `last_synced`
- [ ] **`scripts/embed_frontmatter.py` derives + writes** —
      reads the live graph (Intent / Capability / Lifecycle / Memory
      nodes + edges) via `ctx.find(...)` / `ctx.neighbors(...)`,
      composes the appropriate frontmatter block for each file kind,
      writes it idempotently between
      `<!-- frontmatter:auto -->` … `<!-- /frontmatter:auto -->`
      fences (when a file already has hand-authored frontmatter, the
      derived fields land in the auto-fence and the hand block stays
      authoritative for the non-derived keys).
- [ ] **`scripts/check_frontmatter.py` gates regressions** — Spec 054
      drift-baseline pattern:
      - audits every rendered file by kind
      - exits 1 when a NEW file of a kinded type lands without the
        required frontmatter block (or with an invalid schema)
      - tracks the historical gap in
        `Plan/_planning/frontmatter-baseline.txt` (one path per line)
      - surfaces `baseline_shrinkable` when a baseline-tracked file is
        fixed so authors trim the baseline
- [ ] **Round-trip property** — for every rendered file kind there is
      a `from_frontmatter(path) -> GraphSlice` constructor in
      `agency/_frontmatter.py` that yields the node + outgoing edges
      the file represents; the validator asserts a round-trip on a
      sampled set of files (file → graph slice → re-render → byte-identical
      frontmatter block).
- [ ] **CI gate added** to `.github/workflows/test.yml` step
      "Universal frontmatter" running
      `python -m scripts.check_frontmatter`.
- [ ] **Spec 149 baseline is folded in** — `vision_goals:` becomes one
      of the required `spec`-kind fields; the Spec 149 baseline +
      validator continues to ship (no breaking change), but Spec 278's
      generalized validator runs ALSO for the broader file set.
- [ ] **Doctor surfaces frontmatter health** — `agency_doctor`
      reports `frontmatter.kinds_audited`, `frontmatter.regressions`,
      `frontmatter.baseline_size`, `frontmatter.shrinkable`.
- [ ] **Acceptance invariants** (rule 8):
      - `embed_frontmatter --dry-run` is idempotent (running twice
        yields zero diffs);
      - `check_frontmatter` exit code is 1 iff `regressions` is
        non-empty;
      - `from_frontmatter(p) → re-render → byte-identical fenced block`
        for every kinded sample file;
      - `baseline_path.read_text().splitlines()` is a SUBSET of the
        live audit's `kind=missing` paths (a baseline that names a
        non-existent file is itself drift and fails);
      - the set of file kinds covered EQUALS the set named in
        `agency/_frontmatter.py` (no silent widening or gap).

## Slices

### Slice 1 — minimum viable kinds (spec + skill + template)

Ship the validator + embedder for THREE file kinds first — `spec`
(extends Spec 149), `skill` (skills/*/SKILL.md), `template`
(agency/capabilities/*/templates/*.md, the music + novel cluster
briefings). These three already have de-facto frontmatter conventions
elsewhere in the codebase; codifying them is low-risk + immediately
useful.

### Slice 2 — derived docs + capability briefs

Add `capability_brief` + `generated_doc` kinds. `generated_doc` ties
into the existing `<!-- doc-source: -->` markers — Spec 278 widens
that marker into structured frontmatter so the doc-drift hasher reads
from the auto-fence instead of HTML comments scattered through the
body.

### Slice 3 — planning docs + round-trip property

Add `planning` kind and the `from_frontmatter` round-trip property
test. This is the slice that PROVES rule 2 — every file the substrate
renders can be reconstructed back into a graph slice without
information loss.

## Tests (RED → GREEN)

- `tests/test_universal_frontmatter.py` — unit tests per kind, fakes a
  graph slice, asserts the embedder writes the expected fenced block;
  validator unit tests for missing / invalid / baseline / shrinkable;
  round-trip property test (Hypothesis-style or table-driven).
- Live-tree regression test asserting `rep.regressions == []` against
  `Plan/_planning/frontmatter-baseline.txt`.

## Failure modes (Nygard)

- **Frontmatter explosion** — embedder writes 200 lines of frontmatter
  to a 5-line file. Mitigation: a per-kind FIELD WHITELIST capped at
  ~12 fields; everything else stays in the graph, the file holds the
  key + a `derive_source` pointer.
- **Stale auto-fence** — embedder writes once, the graph drifts, the
  file lies. Mitigation: `last_synced` field + `check_frontmatter`
  re-derives + diffs every CI run; stale = regression.
- **Round-trip lossy under reorder** — YAML preserves order;
  re-rendering must sort keys deterministically (alphabetical within
  the auto-fence) so the byte-identical assertion holds.
- **Baseline rot** — files deleted but still named in baseline.
  Mitigation: invariant above (baseline ⊆ live audit's missing set).

## Why this matters (rule 2 closure)

Rule 2 is the substrate's most important rule and the LEAST enforced
today. Spec 149 enforced it on `vision_goals:` for specs; Spec 278
generalizes it to the full rendered surface. After this spec ships,
every file the substrate produces can be re-ingested into the graph
with no hand-mapping — the file IS the graph slice, written down. The
Vision-Charter chain "intent → invocation → artefact → reflection"
becomes lossless across the file boundary, which is what enables the
provenance moat (CLAUDE.md "Why this matters" §"the provenance moat IS
the moat").
