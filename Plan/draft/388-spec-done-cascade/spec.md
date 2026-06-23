---
spec_id: "388"
slug: spec-done-cascade
status: partial
state: draft
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [3]
depends_on: ["357", "360"]
domain: workflow
---

# Spec 388 — `finish_spec`: the done-cascade as ONE owner trigger

> When the owner says "this spec is done", that is the approval (CLAUDE.md, "code
> is the final decision"). Today the done-cascade is a manual SIX-step dance —
> approve decisions, draft/update the theme ADR, render it, `move_spec`, move the
> physical folder, rewrite the frontmatter, rebuild `architecture.md`. Steps get
> skipped; the three state representations drift. This spec collapses the cascade
> into one verb: `workflow.finish_spec(spec_id, approver)`.

## Why
The repo-development workflow (Spec 353–360) keeps a spec's lifecycle state in
THREE places that `scripts/check-drift` gates for agreement: the physical
`Plan/<state>/` folder, the `state:` frontmatter, and the `SpecLifecycle` graph
node. `workflow.move_spec` writes only the NODE — it does NOT move the folder or
rewrite the frontmatter, so finishing a spec by hand means remembering all three
plus the ADR steps. A missed step is silent drift the next check-drift run
flags. The cascade is deterministic and owner-triggered; it should be one call.

## Design
`workflow.finish_spec(spec_id, approver="", root="Plan", rebuild_architecture=True)`
— role `effect`. The **folder is authoritative** ("folder is the final
decision"); the node + ADR steps are **best-effort** so a not-yet-ingested spec
(empty graph, no `Document`/`Decision` nodes) still finishes cleanly:

1. **Locate** the spec folder by `<spec_id>-…` dir name under a non-terminal
   state (`draft`/`open`/`inprogress`). Not found → typed error (no mutation).
2. **Approve** the spec's ADR decisions via `adr.spec_decisions_ready` +
   `adr.approve(approver, override=True)` — only when `approver` is given (owner
   authority; an agent never self-approves). Best-effort: empty graph → 0 approved.
3. **Sync** the `SpecLifecycle` node to `done` — walk the `spec` machine's legal
   transitions (`draft→open→inprogress→done`) with `override=True`. Best-effort:
   no node → skipped.
4. **Move** the physical folder to `Plan/done/` (`shutil.move`) and reconcile the
   `state:` / `status:` frontmatter to `done` (regex). This is the authoritative
   state change — keeps folder == frontmatter. Target exists → typed error.
5. **Rebuild** `architecture.md` via `adr.architecture(apply=True)` (DERIVED,
   Spec 360). Best-effort; gated by `rebuild_architecture`.

Returns `{spec_id, moved, from_state, folder, decisions_approved, node_synced,
architecture_rebuilt}` or `{spec_id, moved: False, error}`.

## Acceptance
- `finish_spec` on a draft spec in an isolated Plan tree moves it to `/done`
  across folder + frontmatter (source folder gone, frontmatter reconciled).
- `finish_spec` on an unknown spec id returns a typed error and mutates nothing.
- The node/ADR/architecture steps never raise on an un-ingested spec (best-effort).

## Slices (TDD)
1. The file-move core + typed errors (folder + frontmatter), isolated temp tree.
2. (future) Surface in the `develop-spec` workflow's `done` phase as the writer.

## Followup — Implementation Status (2026-06-23)

**Slice 1 — SHIPPED.** `workflow.finish_spec` (`agency/capabilities/workflow/_main.py`)
implements the five-step cascade; folder + frontmatter are authoritative, the
node/ADR/architecture steps are best-effort (try/except, empty-graph safe).
Tests: `tests/acceptance/features/spec_done_cascade.feature` +
`test_spec_done_cascade.py` — (1) finishing a draft spec in an isolated `tmp_path`
Plan tree moves it to `/done` with frontmatter reconciled + the source folder
gone; (2) an unknown spec id returns a typed error. 2/2 green; install regen +
check-drift clean. Used to close the 370-program (371–378) into `/done`.

**Renumber note:** opened as 379, renumbered to 388 on a naming collision with
the already-shipped `379-brooks-lint-port` (CLAUDE.md rule 4 — renumber only after
a collision on merge).
