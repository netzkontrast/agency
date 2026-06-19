# Plan — Agency Spec Index

`TODO.md` is the **binding status index** (verdict + one-liner per spec).
This file is the navigation guide.

## Directory layout

| Path | Contents |
|---|---|
| `Plan/NNN-slug/` | Per-spec planning docs (`spec.md` + supporting files) |
| `Plan/living/` | Living docs per capability — authored Why + generated verb table |
| `Plan/_planning/` | Charter, drift/lint/schema baselines, meta-planning |
| `Plan/_research/` | Research materials (novel MVP source, agency system import) |
| `TODO.md` | Binding spec status index |

## Current state (2026-06-19)

- **119 shipped** — spec dirs deleted; code + git log are the record
- **8 closed/superseded** — see TODO.md Verdicts table
- **13 partial** — active in-flight slices: 003, 004, 005, 094–099, 311, 317, 318, 322
- **~168 drafted** — not yet started or typed-stub only

## Active fronts

1. **Discover / Intent pillar** (Spec 307) — 308 / 309 / 310 shipped; 311 / 317 / 318 / 322
   Slice 1 done; remaining: 312, 314–316, 320–325 plus verb consolidation to
   `elicit(mode)` / `sharpen(pass)` per PR #168 direction
2. **Music cluster file-split** — 094–099 verb surface + tests GREEN; need cluster-module
   migration (batch operation)
3. **Novel / KP wave** — 133–145 drafted; Dramatica + KP backbone ready to implement
4. **Vision waves 1–12** (155–277) — waves 1–2 have typed-shape Slice 1; waves 3–12
   stubs only; lowest priority relative to the fronts above

## How to navigate

```bash
# Live capability search (beats reading files):
mcp__agency__search query="<keyword>"

# Status of a specific spec:
cat Plan/NNN-slug/spec.md

# Which front to work on next:
cat TODO.md  # Partial section = in-flight work
```

## Spec lifecycle

```
research → design → spec-panel → refine → IMPLEMENTATION-PLAN → TDD
RED → GREEN → green pytest → commit → push → PR
```

Each `Plan/NNN-slug/spec.md` carries:
- Frontmatter (spec_id, slug, status, depends_on, affects, domain, wave)
- Why / Done-When / Files / Open Questions
- `## Followup — Implementation Status` (per-slice Done/Still, test counts, file:line evidence)
