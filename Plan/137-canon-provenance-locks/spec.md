---
spec_id: "137"
slug: canon-provenance-locks
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "017"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_canon_locks.py
domain: novel / canon / provenance
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/02_begriffe-und-konzepte.md (§16 Provenienz-Marker, Quellen-Hierarchie, Steinbruch)"
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§12 Master-Index aller Locks, §13.4 Hard-Stops)"
---

# Spec 137 — Canon provenance markers & locks

## Why

The Kohärenz Protokoll project runs on a strict source-of-truth discipline
that the agency cap has no first-class surface for. Every canon fact carries
a **provenance marker** — `[K]` kanonisch/gelockt · `[V]` Vorschlag (proposal,
validation-pending) · `[S]` Steinbruch (quarry — deprecated material reusable
as raw stock) · `[L]` Lücke (gap, still to set). Decisions get **locked** with
a date + source; a Master-Index of all Locks is checked before any contested
drafting decision. Conflicts resolve by a **source-hierarchy** (newer wins;
Story-First: an existing draft beats theory).

Agency has the provenance *moat* (graph edges record who did what) but no way
to say "this world-axiom is `[K]` locked 2026-05-30, source: Entscheidungs-Log"
vs "this is `[V]`, pending Dramatica-engine validation" vs "this is `[S]`
quarry — usable but not canon". Without it, an agent re-writing a scene can't
tell canon from proposal from deprecated stock, and silently canonizes
speculation — exactly the failure the KP discipline forbids ("Niemals stilles
Kanonisieren spekulativer Inhalte").

## Done When

- [ ] **`CANON_STATUS` enum** = `{canonical, proposal, quarry, gap}` (the
      `[K]`/`[V]`/`[S]`/`[L]` markers). Stored as an optional `canon_status`
      property readable on ANY novel-domain node (World, Storyform,
      CodexEntry, Character, etc.) — a cross-cutting marker, not a new node
      type.
- [ ] **`Lock` node** `{novel, topic, content, locked_on, source, supersedes?}`
      — a canonized decision. `locked_on` is a date string; `source` names the
      originating document/log; `supersedes` optionally points at an earlier
      Lock it overrides (newer-wins chain).
- [ ] **`LOCKS` edge**: Lock → (target node) — the node a lock governs
      (optional; a lock can be free-standing policy or bound to a node).
- [ ] **Verbs**:
      - `set_canon_status(node_id, status)` — stamp any node with a marker.
        Rejects unknown status.
      - `record_lock(novel_id, topic, content, source, supersedes="")` —
        mints a Lock; when `supersedes` is set, the superseded lock gets a
        `superseded_by` flag (audit trail, never deleted).
      - `lock_index(novel_id, topic="")` — the Master-Index: all active locks
        (superseded ones excluded by default), optionally filtered by topic.
        Sorted by `locked_on` descending (newest first = highest authority).
      - `resolve_canon_conflict(node_ids, source_dates)` — given competing
        facts with source dates, returns which wins by newer-wins +
        flags `[S]` quarry entries as losing to any `[K]`/`[V]`.
      - `quarry_filter(novel_id)` — lists all `quarry`-status nodes (the
        Steinbruch): deprecated material an author may still mine, never
        auto-canon. Companion `promote_from_quarry(node_id, source)` flips a
        quarry node to `proposal` with a lock recording the promotion.
      - `canon_audit(novel_id)` — census: count of nodes per canon_status +
        list of `gap` (`[L]`) nodes still needing resolution (the open-work
        surface). Flags any node with NO canon_status as "unmarked — decide".
- [ ] **`develop.skill_walk` integration**: a `canon-gate` predicate that a
      drafting skill can chain — refuses to treat a `proposal`/`quarry` node
      as fact without an explicit author override (mirrors the KP "Story-First
      / check master-index first" hard-stop).
- [ ] TODO row + drift clean.

## Design notes

- **Marker, not node.** `canon_status` rides on existing nodes as a property
  (open-set substrate — extra fields ride along untouched per Spec 001). Only
  `Lock` is a new node, because a lock has its own lifecycle (date, source,
  supersession chain) independent of any single node.
- **Newer-wins is the only conflict rule.** The KP source-hierarchy
  ("Kapitel-Kompendium 2026-05-31 > Entscheidungs-Logs 2026-05-30 > …") is
  just date-descending. `resolve_canon_conflict` encodes it once; everything
  else reads it.
- **Story-First is a documented exception**, not a code rule: a verb can't
  know whether a draft beats theory, but `lock_index` surfaces the locks an
  author consults to decide.
- This is the substrate Spec 136 (dual-storyform) and 138 (plural-character)
  hang their `[K]`/`[V]`/`[L]` status on — almost every KP fact is marked.

## Open questions

1. Should `canon_status` default to `proposal` on node creation, forcing an
   explicit promotion to `canonical`? **Recommend**: no default (unmarked) +
   `canon_audit` flags unmarked — forcing a default would mislabel the
   thousands of incidental nodes that aren't canon claims.
2. Lock granularity — one Lock per decision, or batched "lock-sets"?
   **Recommend**: one per decision; `lock_index` groups by topic for reading.

## Followup

(Populated when the PR ships.)
