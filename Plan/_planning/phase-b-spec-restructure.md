# Phase B — Spec corpus restructure (layered + archive)

> Vision-program Phase B (owner directive). Phase A realigned the vision docs;
> Phase B realigns the **spec corpus** onto code ground truth. Phase C (tests)
> follows. Each phase its own PR; this branch stacks on Phase A
> (`claude/agency-plugin-vision-review-1fjfv8`), PR base = that branch.

## Problem

230 specs across 269 `Plan/` folders + 13 SDLC clusters + 13 enhancement waves
(146–278), with heavy 1:1 base→enhancement proliferation. Disciplined
closure/supersession, but **no capability-indexed "current" view** — to learn
"what does `analyze` do today?" you read N spec fragments across waves. The
corpus tracks *history*, not *current state*.

## Decision (owner-confirmed)

**Layered + archive.** Introduce **~29 canonical living specs** — one per
capability + one per substrate concept — that describe **current state**, and
**move all 230 historical specs to `Plan/_archive/`** (preserved, never
deleted — the provenance trail is the moat). Living specs are **generated from
code as documentation** (interview Q2), then enriched with an authored intent
section the code can't derive.

## Target structure

```
Plan/
  _archive/                 # all 269 historical spec folders (git mv — history preserved)
  _planning/                # planning docs (this file lives here)
  living/
    intent/                 # ── Intent pillar
      intent.md  thinking.md  dogfood.md
    capability/             # ── Capability pillar
      plugin.md  skill_generator.md  skills.md  document.md  prompt.md
      analyze.md  music.md  novel.md
    lifecycle/              # ── Lifecycle pillar
      develop.md  gate.md  delegate.md  subagent.md  jules.md
      workspace.md  branch.md
    memory/                 # ── Memory pillar
      reflect.md  research.md  management.md   # management = Spec 290
    substrate/              # the Engine + the four-concept substrate modules
      engine.md  memory-store.md  ontology.md  intent-core.md
      lifecycle-core.md  capability.md  skill.md  toolresult.md
  README.md                 # index: the four pillars → their living specs
```

Organized **by the four pillars** (CORE.md §"Four complete pillars"), so the
corpus mirrors the Core Vision. `shell` folds into `substrate` or `workspace`
(TBD during build — it's a thin boundary cap).

## Living-spec format (generated surface + authored intent)

Each living spec = **generated from the registry** (the parts the code owns) +
**one authored section** (the part it doesn't):

```markdown
---
capability: analyze            # or substrate module
pillar: memory
vision_goals: [...]
status: living                 # regenerated from code; not a lifecycle status
sources: [Plan/_archive/042-…, Plan/_archive/050-…]   # the specs it supersedes
last_generated: <date>
---
# analyze — <one-line from the module docstring>
## Why (authored)        ← the ONLY hand-written section; the intent/trade-offs
## Verbs (generated)     ← from the registry: name · role · params · purpose
## Ontology (generated)  ← nodes · edges · enums the cap contributes
## Skills (generated)    ← walkable skills + phases
## History (generated)   ← the archived specs that built this (links into _archive/)
```

The generated sections are produced by extending `scripts/gen-capability-docs`
into a `scripts/gen-living-spec` pass (rule 2: derive, don't duplicate). The
`## Why` is the only place drift can enter — kept short, owner/subagent-authored.

## Execution plan

1. **Scaffold + exemplar (owner).** Build `scripts/gen-living-spec`; hand-write
   ONE exemplar living spec end-to-end (`analyze.md`) to lock the format. ← gate
2. **Archive move.** `git mv` the 269 historical folders → `Plan/_archive/`
   (preserve history; keep `_planning/`). One commit, reviewable as a rename set.
3. **Generate the ~29 living specs** from code (the generated sections).
4. **Dispatch sonnet subagents** (per pillar — 4 subagents) to author the `## Why`
   sections + curate each living spec's `sources:`/`## History` from the archived
   specs. PR review per pillar batch.
5. **Index + crosslinks.** `Plan/living/README.md` (pillars → specs); update
   `docs/specs/index.md`, `TODO.md`, and any `Plan/NNN` references.
6. **Guardrails.** Update `test_vision_goals_validator` + any spec-path tests for
   the new layout; `check-drift` green; living-spec generation is idempotent.

## Out of scope (coordinated, later)

- The `/plans` migration (specs → graph-backed Plans via the 286 agent's
  planning skill) — a *later* convergence of Phase B + Spec 287; flagged to the
  286 agent on PR #141. Phase B keeps specs as files (rendered/generated docs);
  the graph-backed move is its own step.
- Building the Management capability (Spec 290) — feature work, not this restructure.

## Risks

- **Irreversible-feeling move** — mitigated: `git mv` preserves full history;
  `_archive/` is preserved, never deleted; the move is one reviewable commit.
- **Path references** — many tests/docs reference `Plan/NNN-…`; the archive move
  must update or tolerate them (the validator's baseline, `docs/specs/index.md`,
  cross-spec `depends_on`). Sweep before the move.
- **Generated-vs-authored drift** — only `## Why` is authored; everything else
  regenerates, so drift is bounded (rule 8).
