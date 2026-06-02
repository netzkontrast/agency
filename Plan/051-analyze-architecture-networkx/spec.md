---
spec_id: "051"
slug: analyze-architecture-networkx
status: draft
last_updated: 2026-06-03
owner: "@agency"
depends_on: [042, 050]
informs: [044, 048]
affects:
  - pyproject.toml                                         # [analyze] extra adds networkx
  - agency/capabilities/analyze/_architecture.py           # refactor cycle + add A004/A005 metrics
  - agency/capabilities/analyze/_main.py                   # potentially new act verb
  - tests/test_analyze_architecture.py                     # extended fixtures
  - tests/test_analyze_architecture_networkx.py            # NEW for the metrics
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 051 — analyze.architecture deep upgrade (networkx)

## Why

Spec 042 v1's `analyze.architecture` ships three rules (A001 cycle,
A002 large file, A003 medium file). The cycle-detection code is a
**hand-rolled Tarjan's SCC** (~40 LOC). networkx provides:

- `nx.simple_cycles(G)` — the canonical cycle enumerator (returns
  every elementary cycle, not just SCCs).
- `nx.strongly_connected_components(G)` — same as my Tarjan but
  battle-tested.
- `G.in_degree(node)` / `G.out_degree(node)` — fan-in/fan-out for
  package-level metrics (A004/A005).
- `nx.shortest_path(G, src, dst)` — for cycle-explanation rendering
  (show the user the SHORTEST cycle path, not the SCC dump).

Same Spec 050 pattern: optional dep, silent fallback to the
hand-rolled implementation. When networkx is installed, the
metrics get more comprehensive AND the code path delegates to a
proven library.

## Done When

### A001 cycle refactor

- [ ] `agency/capabilities/analyze/_architecture.py::_scc_cycles`
  refactored to use `networkx.simple_cycles` when networkx is
  available; falls back to Tarjan when missing.
- [ ] Each cycle finding now reports the SHORTEST cycle path (a
  → b → c → a), not just the SCC node set. UX win for the
  caller.

### A004 fan-out (NEW rule)

- [ ] `A004` (warn) — a module's fan-out (number of intra-tree
  modules it imports) exceeds 8. Suggests refactoring into smaller
  cohesive units.
- [ ] Severity pinned: warn when fan_out ≥ 8; fail at ≥ 15.

### A005 fan-in (NEW rule)

- [ ] `A005` (info) — a module's fan-in (number of intra-tree
  modules importing it) exceeds 10. NOT a problem per se — high
  fan-in means the module is a core utility — but worth surfacing
  so the agency-doctor or the briefing knows.

### A006 god-module (NEW rule)

- [ ] `A006` (warn) — fan-in ≥ 10 AND fan-out ≥ 8 AND LOC ≥ 400.
  Trifecta-of-smell: imports lots, imported by lots, and big.

### agency_doctor reporting

- [ ] `agency_doctor.analyze_extras` already added by Spec 050;
  extend the per-tool version check to include networkx.

### Tests

- [ ] `tests/test_analyze_architecture.py` — extend the existing
  cycle test to verify the SHORTEST path is reported (when
  networkx is present).
- [ ] `tests/test_analyze_architecture_networkx.py` — fixtures for
  A004 (a module with 9 sibling imports), A005 (a module imported
  by 11 others), A006 (one fixture combining all three).

## Design

### Why networkx as optional

networkx is ~4MB installed; it's not zero-dep-friendly. The agency
core stays light by making it `[analyze]` extra (already declared
in Spec 050). Without networkx, A001 still ships (Tarjan); A004/
A005/A006 don't fire — they require a graph library for cheap
degree counting.

### Why fan-out/fan-in matter

Spec 047 §C13 (Plugin) calls out "Folder-per-capability when Spec
016 lands". Folder-form capabilities NATURALLY keep fan-out low.
A004 surfaces capabilities that grew past the folder pattern and
should be split.

### Open Questions

1. **Thresholds.** A004 at 8 / A005 at 10 / A006 trifecta — these
   need measurement against the agency repo + a SuperClaude-sized
   project before pinning. v1 uses heuristic defaults; v2 measures.
2. **Should we add A007 maintainability-trend** — couple gitpython
   (Spec 052) to surface "this file's MI has been declining" —
   v3 candidate.

## Files

- **Add:**
  - `tests/test_analyze_architecture_networkx.py`
- **Modify:**
  - `pyproject.toml` — add `networkx>=3.2` to `[analyze]`.
  - `agency/capabilities/analyze/_architecture.py` — cycle refactor
    + A004/A005/A006 implementations.
  - `tests/test_analyze_architecture.py` — extend cycle test.
- **Do not modify:**
  - The Spec 042 Finding contract (rule, severity, file, line,
    message, evidence stays).
  - The Spec 050 wrapper pattern (no new wrapper module — networkx
    is used INSIDE _architecture.py for cycle + metrics, not as a
    separate subprocess).

## Cluster-coherence (Spec 047)

- C04 Quality (it IS — extends the architecture axis).
- C13 Plugin (A004 enforces folder-per-capability discipline).

## Followup — Implementation Status (2026-06-03)

**Verdict:** Not started — drafted as part of user's deps-extension
push.
