# Specs

Agency is built spec-by-spec. This folder explains the spec system and points at the
canonical sources — it does **not** duplicate them (that would drift instantly).

## The two canonical sources

| Source | What it is |
|---|---|
| [`/TODO.md`](../../TODO.md) | **The binding spec status index** — verdict (Shipped / Partial / Not started / Drafted), a one-line summary, and the blocker/next step for *every* spec. The single source of truth for "what's done". |
| [`/Plan/NNN-slug/spec.md`](../../Plan/) | **The per-spec detail** — why, design, spec-panel critique, Done-When, and a `## Followup — Implementation Status` section grounding the verdict in `file:line` evidence. |

`TODO.md` rolls up; each `Plan/NNN/spec.md` grounds. There is no drift between the two by
rule: **every spec-touching commit updates the matching `TODO.md` row** (CLAUDE.md rule 4).

➡️ **[index.md](index.md)** — every spec listed + linked (generated from `Plan/`
frontmatter by `scripts/gen-spec-index`; re-run after adding/closing a spec).

## The spec lifecycle

```
research → design → spec-panel (multi-expert critique) → refine → IMPLEMENTATION-PLAN → TDD
```

Per phase: **RED → GREEN → green suite → commit → push**. Feature branches; PRs target
`main`; additive history (never rewrite/force-push). The `develop` capability ships these
disciplines as walkable skills (`brainstorm`, `plan`, `spec-panel`, `tdd`, `verify`, …).

## Reading the landscape

- **Verdicts at a glance** + the full status table live at the top of
  [`/TODO.md`](../../TODO.md).
- The **vision specs** (the authoritative per-part contracts) are in
  [../vision/specs/](../vision/specs/).
- The **cluster map** (which of the 13 SDLC+meta clusters a verb/skill lands in) is
  Spec 047 (`Plan/047-cluster-integration/`).

## Recently shipped (this generation)

Highlights — see `TODO.md` for the authoritative list: **002** Driver registry · **026**
skills capability + projection + graph promotion · **080/081** docstring-derived +
walkable Agent Skills · **082** TokenCounter · **083** Skills-API publishing · **084**
`analyze.graph` · **007** music clustered-Driver example + computed gates · **091**
`intent` critical-thinking capability.

<!-- doc-source: TODO.md -->
<!-- doc-hash: b8c5cd0c70c7ef35 -->
