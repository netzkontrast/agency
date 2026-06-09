# First-Principles Decomposition of the Novel Capability

**Goal of this plan:** turn the imported `Legacy/` corpus into a *researched and
brainstormed* design for how the **Kohärenz Protokoll** repository should be
structured as a novel-writing environment — grounded in (a) the patterns proven
in `Legacy/` and (b) the `netzkontrast/agency` plugin contract (one FastMCP
engine + bi-temporal graph; wire contract `search · get_schema · execute`; four
concepts Intent · Capability · Lifecycle · Memory; the graph is the store, files
are a rendered view).

## Method

Five Jules sessions run in parallel. Each owns **one slice** of the novel
capability and **one target directory** under this folder. No two sessions write
to the same path. Each session:

1. Reads `JULES_PROTOCOL`-style gates: Confidence ≥ 0.90 → (TDD where code) →
   Evidence pasted → Self-Review. This work is analysis/design, so TDD is N/A —
   evidence = cited `Legacy/` paths + measured numbers + grep hits.
2. Reads its assigned `Legacy/` inputs (read-only).
3. Read-only clones **`netzkontrast/agency`** to learn the plugin contract
   (`examples/` capability pattern, `OntologyExtension`, `@verb` role tags,
   the engine's `extra_capabilities` wiring).
4. Writes **only** inside its target dir:
   - `DECOMPOSITION.md` — first-principles breakdown of the slice (what the
     primitives really are, stripped of incidental implementation).
   - `PROPOSAL.md` — how this slice should live in the KP repo (paths, files,
     capability verbs, on-disk layout, what becomes a graph node vs a rendered
     file).
   - `OPEN-QUESTIONS.md` — decisions that need a human call (esp. the
     graph-canonical vs disk-first authoring tension).
5. On ambiguity it cannot resolve from the data, calls `request_user_input`
   once and stops — it does **not** guess load-bearing decisions.

## The five slices

| # | Target dir | Slice | Primary `Legacy/` inputs |
|---|---|---|---|
| 1 | `01-dramatica-engine/` | Dramatica model & lookup | `skills/dramatica-theory`, `skills/dramatica-vocabulary`, `tools/dramatica-nav`, `tasks/042,078-082`, `maintenance/schemas/narrative-ontology` |
| 2 | `02-ncp-protocol/` | Narrative Context Protocol (state, schema, validation) | `skills/ncp-author`, `research/ncp-novel-co-authoring-spec`, `tasks/015,076`, `maintenance/schemas/narrative-ontology` |
| 3 | `03-novel-architect-orchestration/` | Phase orchestration, gates, commands | `skills/novel-architect`, `skills/novel-architect-legacy`, `tasks/003,070,071,083,088`, `research/integrate-dramatica-ncp-skills` |
| 4 | `04-character-and-world/` | Character & world subsystems | `skills/novel-architect-character`, `skills/novel-architect-world` |
| 5 | `05-structure-scene-coherence/` | Structure, scene matrix, coherence/linters, render | `skills/novel-architect-structure`, `skills/novel-architect-scene`, `tasks/073,074,075,084,085,086,087,090`, `decisions/0010-...` |

## After the five sessions complete

A synthesis step (`SYNTHESIS.md`, authored here) reconciles the five proposals
into one **KP repo design**: the directory layout, which novel primitives become
agency capability verbs, the on-disk novel layout (`novels/{author}/works/...`),
and a resolution of the graph-vs-disk source-of-truth question.

Each session's exact dispatch brief lives in `<target-dir>/BRIEF.md`.

---

## Reference files (copied from the incubator)

The full decomposition outputs are mirrored here so the KP repo is self-contained
(originals were authored in `netzkontrast/agency-backups` under
`kohaerenz-protokoll-novel-writing-incubator/`, PRs #137–#142):

- [`PLUGIN-CONCEPTS.md`](./PLUGIN-CONCEPTS.md) — the Agency plugin contract the slices were decomposed against.
- [`SYNTHESIS.md`](./SYNTHESIS.md) — reconciliation of all five slices into one `novel` capability design.
- Per slice (`01`–`05`): `CONCEPTS.md` · `COHERENCE.md` · `PROPOSAL.md` (+ the original `BRIEF.md`).

The formal normative spec derived from these lives at
[`../spec/novel-capability.spec.md`](../spec/novel-capability.spec.md).
