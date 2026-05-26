---
slug: roadmap
type: roadmap
status: ready
summary: The Plan for the agency plugin (v4) — a running seed already proves the moat, code-mode chaining, and gate/elicitation; next, grow the seed into the Engine (the four-verb contract + code-mode), port the four concepts, then broaden capabilities per the PORTING-ROADMAP. The canon (docs/vision/) defines the model; this tracks the plan. Supersedes the v2.1 plan.
---

# Roadmap — the Plan (v4)

The canon in `docs/vision/` defines the **v4 four-concept model** (see
[CORE.md](vision/CORE.md)). This file tracks the Plan.

> **Supersedes the v2.1 plan** (establish three domains / anchor jules-in-who /
> lazy-domaining). The adversarial panel's verdict was unanimous: *stop spec'ing,
> build the smallest thing that proves the moat.* That seed now exists.

## 0 — DONE: the seed (the proof)

[`seed/`](../seed/README.md) — a running proof-of-concept on the **real
substrate** (`graphqlite` + `fastmcp`), **6/6 green**. It proves:

- **the moat** — cross-concern provenance in one graph traversal;
- **the falsifier** — one graph + the verb frame carry two genuinely different
  capabilities (a stateless `transform` and an agent);
- **bi-temporal Memory** — the *what* changes while the *why* holds (`as_of`);
- **`COMPLETED ≠ done`** — the silent-fail lesson as a first-class `verify` step;
- **the four-verb Engine** over real FastMCP with MCP-conformant names;
- **code-mode tool-chaining** — an executable graph mirrored into provenance;
- **gate/elicitation** — human-in-the-flow via `ctx.elicit`.

## 1 — Grow the seed into the Engine

- **Engine** — the four-verb contract (`list_tools` / `call_tool` /
  `list_skills` / `dispatch_skill`) + `execute(code)` code-mode, progressive
  disclosure, engine-guard middleware (quality-score, loop-detection, compaction,
  `Slot`/quota).
- **The four concepts** — harden the seed's `Intent` / `Capability` /
  `Lifecycle` / `Memory` into the production engine: `project(query, budget)`
  (ranked/budgeted/`as_of`), artefact drivers (`fs` → `repo`/`s3`/`http`/`drive`),
  the full provenance traversals.
- **Skills as atomic gated step-graphs** — the Lifecycle-template runner; gates
  as `ctx.elicit` steps recorded as `Gate` nodes. See
  [specs/skills-and-gates.md](vision/specs/skills-and-gates.md).

## 2 — Port the first real capability: `jules`

`jules` is the clearest instance of the v4 thesis: **an agent IS a Lifecycle
parameterization** whose transitions differ (it inserts `verify` because
`COMPLETED ≠ done`). Port it as the reference Lifecycle: `lifecycle_agent_*`
(open/move/close/watch) + the patch-recovery discipline. The seed already
encodes the `jules` capability and the `COMPLETED ≠ done` lesson.

## 3 — Broaden (per the PORTING-ROADMAP)

Every prototype skill and function is mapped to v4 in
[PORTING-ROADMAP.md](vision/PORTING-ROADMAP.md). Highlights:

- **bitwize-music** — craft acts (`capability_lyric_act`), transforms
  (`capability_syllable_transform`), effects (`capability_master_effect`),
  Lifecycle gates (`lifecycle_track_pregate_check`), Memory reads
  (`memory_album_recall`).
- **novel** — the second craft, the FALSIFICATION TEST that the verb frame + one
  graph carry two different crafts. Same four concepts, different Capability set.
- **The dual-store drift tools vanish** — `rebuild_state`, `db_*` tweet SQLite,
  path-resolution helpers exist ONLY because content lives on disk beside a
  cache. With one graph, ~12 tools delete rather than port (the strongest
  validation of the "one graph" thesis).

## Later

- Hot-reload of capabilities; an alternative graph driver for larger
  deployments; the A2A boundary adapter for external agents.
