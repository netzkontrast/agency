---
spec_id: "357"
slug: spec-state-lifecycle
status: draft
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["353", "292", "339", "351"]
vision_goals: [4, 7]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/workflow/__init__.py
  - agency/capabilities/workflow/_main.py
  - Plan/draft/
  - Plan/open/
  - Plan/inprogress/
  - Plan/superseded/
  - Plan/done/
  - scripts/check-drift
  - tests/acceptance/features/spec_state.feature
---

# Spec 357 — spec-state lifecycle: physical folders + graph mirror

> Child of **353**. The owner's Plan/ restructure: specs flow through physical
> state folders (`/draft /open /inprogress /superseded /done`), mirrored by a
> `SpecLifecycle` graph node (keep-both). The 339 existing flat specs are
> **grandfathered**. Hosts the spec-state verbs the `workflow` capability (358)
> drives.

## Why

Owner directive: *"Es gibt mehrere Verzeichnisse in Plan, dann neu: `/draft
/open /inprogress /superseded /done`. … Ziel: alle Specs sind indiziert, haben
korrekte Frontmatter."* Today `Plan/` is a flat list of `NNN-slug/` folders;
spec status lives only in `status:` frontmatter + `TODO.md` rows, and nothing
enforces that the two agree or that every spec is indexed (Spec 351's liveness
doctor began addressing spec_id uniqueness, but not state).

A spec's **state** is genuinely a Lifecycle (Spec 339): it `open`s as a draft,
`move`s through review/build, and `close`s as done or superseded. Making the
folder the human surface and a `SpecLifecycle` node the queryable spine gives us:
a board ("what's in `/inprogress`?") answerable from the graph, enforced
folder↔frontmatter agreement, and the transition guard the ADR gate needs (358).

## Design

### Physical folders (the human surface)

```
Plan/
  draft/        NNN-slug/spec.md   # design in progress (brainstorm→panel→brooks-lint)
  open/         NNN-slug/spec.md   # design done; decisions being extracted+approved
  inprogress/   NNN-slug/spec.md   # ADR-approved; implementation underway
  superseded/   NNN-slug/spec.md   # replaced by a later spec
  done/         NNN-slug/spec.md   # shipped + verified
  NNN-slug/                        # GRANDFATHERED legacy (flat) — indexed in place
  000-overview.md
```

New specs are born in `Plan/draft/`. The 339 existing flat folders stay where
they are (mass-moving them churns links, git blame, and PR history for no design
gain — 353 reconciliation #3). They are **indexed in place** via frontmatter; an
optional later migration (`workflow.migrate_legacy`, not built now) can fold them
under `done/`/`superseded/` once their state is confirmed.

### `state:` frontmatter (strict, indexed)

Every spec's frontmatter gains a `state:` field ∈ `spec_state` enum
(`draft · open · inprogress · superseded · done`), the single textual source for
the spec's stage. For new specs `state` MUST equal the parent folder; the indexer
enforces it. The legacy `status:` field (draft/partial/done) is retained for
back-compat and TODO.md roll-up; `state` is the finer workflow stage.

### `SpecLifecycle` node (the graph mirror, keep-both)

`workflow.move_spec` records/advances a `SpecLifecycle` node bound to the spec's
`Document`, carrying the current `spec_state` and `SERVES`-ing the spec's intent.
State is advanced via `ctx.lifecycle.move` (Spec 339), so each transition is
bi-temporal provenance — "when did 312 enter `/inprogress`, and what approved it?"
is a single traversal. The folder + frontmatter + node are reconciled keep-both
(Spec 292): on conflict, latest `recorded_at` wins, history retained.

### Verbs (in the new `workflow` capability — 358 hosts the orchestration)

| Verb | Role | Does |
|---|---|---|
| `move_spec(spec_id, to_state, confirm_token="")` | effect | Move the folder, update `state:` frontmatter, advance the `SpecLifecycle` node. **Guarded transitions** (below). Re-anchors intra-repo links. |
| `index()` | transform | The indexer: every spec (legacy + new) is listed with its `{folder_state, frontmatter_state, node_state}`; flags drift (folder≠frontmatter≠node), orphans (no node), and missing/invalid frontmatter. The "alle Specs sind indiziert, korrekte Frontmatter" guarantee. |
| `board(state="")` | transform | The graph-native board: specs grouped by `spec_state`, busiest/oldest first (reuses Spec 290 read style). |

### Guarded transitions (the state machine)

```
draft → open          : design gate passed (panel + brooks-lint findings folded — 358/359)
open → inprogress      : adr.spec_decisions_ready(spec) == true (356/355)  ← the ADR hinge
inprogress → done      : acceptance met + verified (develop.verify)
any → superseded       : a later spec SUPERSEDES this one (records the edge)
```

`move_spec` refuses an illegal transition and refuses `open→inprogress` while
`spec_decisions_ready` is false, naming the blocking decisions (356). A
provenance-stamped override exists for the owner (same pattern as 355).

### CI / drift

`scripts/check-drift` (Spec 054/351) gains a **spec-state check**: folder state ==
frontmatter `state` == latest `SpecLifecycle` node, every spec indexed, no orphan.
Red on drift. This is the enforcement that keeps the three surfaces honest.

## Done When

### Slice 1 — folders + frontmatter + index

- [ ] The five `Plan/<state>/` folders exist (with a `.gitkeep`); a new spec can
      be authored into `Plan/draft/NNN-slug/`.
- [ ] `state:` is documented in the spec frontmatter schema; `workflow.index`
      lists every spec with its three state readings and flags any drift, orphan,
      or invalid frontmatter. Legacy flat specs are indexed in place (no move).
- [ ] `check-drift` fails on a deliberately drifted fixture; green on the repo.

### Slice 2 — move_spec + board + guards

- [ ] `workflow.move_spec` moves folder + frontmatter + `SpecLifecycle` node
      atomically; illegal transitions rejected; `open→inprogress` blocked until
      `adr.spec_decisions_ready` (356).
- [ ] `workflow.board` answers "what's in each state" from the graph.
- [ ] Superseding a spec records `SUPERSEDES` and moves it to `superseded/`.
- [ ] Acceptance scenarios cover a clean draft→open→inprogress→done walk and a
      blocked open→inprogress (rule 7).

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| Mass-moving 339 legacy specs breaks links + git history | Grandfather: legacy stays flat, indexed in place; migration is opt-in and separate |
| Folder, frontmatter, and node drift apart | keep-both reconciliation + `check-drift` gate; `index` reports the three readings explicitly |
| `move_spec` breaks relative links between specs on the move | `move_spec` re-anchors intra-repo links; a test asserts no dangling link after a move |
| `open→inprogress` guard bypassed by hand-moving a folder | `index`/`check-drift` detect the folder-vs-node mismatch and flag it red |

## Interconnects

- **353** master; **358** hosts these verbs and drives them in the lifecycle skill.
- **356/355** — the `open→inprogress` guard is the ADR-approval hinge.
- **292 (Document)** — specs are Documents; keep-both reconciliation across the
  three surfaces.
- **339 (lifecycle)** — `SpecLifecycle` is a Lifecycle; transitions via `move`.
- **351 (liveness doctor) / 054 (check-drift)** — the spec-state check joins the
  existing drift gate.

## Followup — Implementation Status (2026-06-20)

### Done
- Spec authored (design depth).

### Still
- Slice 1 (folders + index) then Slice 2 (move_spec + guards) via TDD.
- Decide `.gitkeep` vs a README seed in each state folder at implementation.
