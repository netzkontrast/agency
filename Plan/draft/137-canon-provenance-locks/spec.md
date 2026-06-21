---
spec_id: "137"
slug: canon-provenance-locks
status: draft
state: draft
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

## Schema

```text
# Enum (new, on novel ontology)
CANON_STATUS = {"canonical", "proposal", "quarry", "gap"}
                 # [K]          [V]         [S]       [L]

# Cross-cutting property (no schema change required — open-set substrate)
<any-novel-node>.canon_status: str  # optional; one of CANON_STATUS, or absent

# New node
Lock {
  novel:         str   # novel_id (FK)
  topic:         str   # e.g. "kw1-physik", "kael-mc-class", "vortex-kind"
  content:      str   # the locked statement, verbatim
  locked_on:    str   # ISO date "YYYY-MM-DD"
  source:       str   # originating doc/log name
  supersedes:   str   # optional Lock-id this overrides
  superseded_by: str  # set when a newer Lock supersedes this one ("" otherwise)
}

# New edge (optional — a Lock can be free-standing policy)
LOCKS : Lock --→ <any-target-node>   # cardinality 1:N (one Lock can govern many)
```

## Verb signatures

```python
def set_canon_status(node_id: str, status: str) -> dict:
    """Stamp any node with a CANON_STATUS marker.
    Returns: {node_id, canon_status, was: <prior-status-or-empty>}
    Raises: ValueError when status ∉ CANON_STATUS.
    """

def record_lock(
    novel_id: str,
    topic: str,
    content: str,
    source: str,
    locked_on: str = "",      # defaults to today (UTC ISO date)
    supersedes: str = "",
) -> dict:
    """Mint a Lock node. When `supersedes` is set, flips that lock's
    `superseded_by` to the new id (never deletes — audit chain).
    Returns: {lock_id, topic, locked_on, supersedes, supersedes_chain: [ids…]}
    """

def lock_index(novel_id: str, topic: str = "") -> dict:
    """The Master-Index. Active locks only (superseded excluded by default).
    Returns: {locks: [{id, topic, content, locked_on, source}…],
              count, by_topic: {topic: count}}
    Sort: locked_on DESC (newest = highest authority).
    """

def resolve_canon_conflict(
    candidates: list[dict],   # [{node_id, canon_status, source_date}…]
) -> dict:
    """Apply newer-wins + quarry-loses-to-non-quarry.
    Returns: {winner: node_id, losers: [node_id…], reason: str}
    Rule: any `canonical`/`proposal` beats every `quarry`; among non-quarry,
    later `source_date` wins; ties → return all with `tied=True`.
    """

def quarry_filter(novel_id: str, kind: str = "") -> dict:
    """List `quarry`-status nodes for a novel (optionally filtered by node kind).
    Returns: {nodes: [{node_id, kind, name_or_slug, canon_status}…], count}
    """

def promote_from_quarry(
    node_id: str,
    source: str,
    topic: str = "",
) -> dict:
    """Flip a quarry node → proposal; mint a Lock recording the promotion
    (topic defaults to "promote:<node_kind>:<slug>").
    Returns: {node_id, new_status: "proposal", lock_id}
    Raises: ValueError when node's current status is not "quarry".
    """

def canon_audit(novel_id: str) -> dict:
    """Census + open-work surface.
    Returns: {
      counts: {canonical: int, proposal: int, quarry: int, gap: int, unmarked: int},
      gaps:  [{node_id, kind, slug_or_name}…],     # [L] still to set
      unmarked: [{node_id, kind, slug_or_name}…],  # no status set — decide
      latest_locks: [{lock_id, topic, locked_on}…] # 5 newest
    }
    """
```

## skill_walk gate

```text
# Predicate name: canon-gate
# Args: node_id, allow=["canonical"]
# Pass: node.canon_status ∈ allow  OR  override_token present in ctx
# Fail: node.canon_status ∈ {"proposal","quarry","gap"} without override
#       → emits {gate:"canon-gate", node_id, status, advice: "consult lock_index"}
```

## Test scaffold

```text
tests/test_novel_canon_locks.py  (target ≥ 14 tests)
  test_canon_status_enum_registered
  test_set_canon_status_happy_path
  test_set_canon_status_rejects_unknown
  test_record_lock_mints_node_and_locked_on_default
  test_record_lock_supersedes_chain_marks_old
  test_lock_index_excludes_superseded_by_default
  test_lock_index_topic_filter
  test_lock_index_sorted_newest_first
  test_resolve_canon_conflict_newer_wins
  test_resolve_canon_conflict_quarry_always_loses
  test_resolve_canon_conflict_ties
  test_quarry_filter_lists_only_quarry_status
  test_promote_from_quarry_flips_status_and_mints_lock
  test_promote_from_quarry_rejects_non_quarry
  test_canon_audit_counts_and_gaps
  test_canon_audit_lists_unmarked
  test_canon_gate_predicate_blocks_proposal_without_override
  test_canon_gate_predicate_passes_canonical
```

## Open questions

1. Should `canon_status` default to `proposal` on node creation, forcing an
   explicit promotion to `canonical`? **Recommend**: no default (unmarked) +
   `canon_audit` flags unmarked — forcing a default would mislabel the
   thousands of incidental nodes that aren't canon claims.
2. Lock granularity — one Lock per decision, or batched "lock-sets"?
   **Recommend**: one per decision; `lock_index` groups by topic for reading.
3. Should `LOCKS` be bi-directional (target → Lock for "which locks govern me")?
   **Recommend**: yes — store as a single typed edge; query both directions via
   `ctx.neighbors(node_id, "LOCKS", direction="in")` (Spec 125 traversal
   pattern), no duplicate edge needed.

## Followup

(Populated when the PR ships.)
