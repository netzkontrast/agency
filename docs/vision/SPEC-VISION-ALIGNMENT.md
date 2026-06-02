# Spec ↔ Vision/GOALS.md Alignment Matrix

> **Purpose.** Every spec answers ONE or more of the eight Vision goals.
> This matrix surfaces where the goals are SOLID, where they have GAPS,
> and which specs are most urgent to ship next.
>
> **Source of truth.** [`GOALS.md`](GOALS.md) is the doctrine; specs
> deliver against it.
>
> **Last reviewed.** 2026-06-03 (after Specs 040, 042, 043, 044, 045,
> 048 shipped on this branch).

## The eight goals

| # | Goal | Status |
|---|---|---|
| **1** | Token-efficient agentic loops | ✅ strong (040, 043, partial 023) |
| **2** | Provenance as a free byproduct | ✅ strong (020, extended by 048) |
| **3** | Agent-uniform lifecycle | ⚠️ partial (010 hard-gate works; 022 not started) |
| **4** | Open set of capabilities | ✅ strong (016 + folder-form Specs 042/043/044) |
| **5** | Code-mode IS the contract | ✅ strong (029 + 039 E2E verifies) |
| **6** | Doctrine evolves through dogfooding | 🔴 **GAP** (014 not started; 017 not started) |
| **7** | Graph is the store, files render | ⚠️ partial (043 closed render-side; 017 write-side STILL OPEN) |
| **8** | Harness-in-harness composition | ✅ strong (012 + 040 S11 + 022 partial) |

## Matrix — every spec mapped to a goal

| Spec | Status | Goal(s) served | Coverage strength |
|---|---|---|---|
| 001 toolresult-and-typed-errors | Partial | 5 | thin (Codes/to_dict absent) |
| 002 boundary-driver-protocol | Not started | 4, 8 | gap — Spec 044's web boundary IS one manifestation |
| 010 novel-domain | Not started | 3 | gap |
| 011 agentic-capabilities | Not started | 3 | gap |
| 012 jules-complete-lifecycle | **Shipped** | 3, 8 | strong |
| 013 jules-skills-and-improvements | **Shipped** | 3, 8 | strong |
| 014 observation-to-amendment | Not started | **6** | **🔴 critical Goal-6 gap** |
| 015 architecture-review | **Shipped** | (process, not goal) | n/a |
| 016 capability-authoring-doctrine | Partial | 4 | thin (Hint #7 sweep) |
| 017 graph-native-dogfood-ledgers | Not started | **7** | **🔴 critical Goal-7 gap** |
| 018 cli-token-efficiency | Partial | 1 | thin |
| 019 engine-result-envelope | Not started | 1 | small |
| 020 central-graph-db | Partial | 2, 7 | one verb away from done |
| 021 engine-monitor-channel | Not started | 3, 6 | hard-blocks 011 + 022 |
| 022 jules-monitor-capability | Not started | 3, 8 | depends on 021 |
| 023 adaptive-disclosure | Partial | 1 | docstring sweep |
| 024 capability-authoring-discipline | Partial | 4 | scaffold marker sweep |
| 025 skill-first-discovery | Partial | 1, 5 | refinement |
| 026 skills-as-core-capability | Not started | 4 | medium |
| 028 jules-folder-migration | Not started | 4 | small |
| 029 mcp-bootstrap-self-explain | **Shipped** | 5 | strong |
| 030 jules-key-doctor-stateful-welcome | **Shipped** | 3, 5 | strong |
| 031 skills-progressive-disclosure | Partial | 1, 4 | active on main |
| 032 templates-schemas-oop-extensions | Partial | 4 | active on main |
| 039 distribution-and-e2e-hardening | **Shipped** | 5 | strong |
| 040 subagent-decision-heuristics | **Shipped** | 1, 8 | strong (11 signals + S11 Jules) |
| 041 implementation-discipline-skills | Not started | 4, 6 | medium |
| 042 analyze-capability | **Shipped** | 4 | strong |
| 043 document-capability | **Shipped** | 1, 7 | strong (94% reduction + render-side of 7) |
| 044 research-capability | **Shipped** | 1, 4, 7 | strong |
| 045 reflect-semantic-recall | **Shipped** | 2 | strong |
| 046 micro-extensions-bundle | Not started | various | medium |
| 047 cluster-integration | **Shipped** | (process, not goal) | strong meta |
| 048 intent-chain-and-owners | **Shipped** | 2 | strong (extends provenance) |
| 049 naming-and-token-economy | Not started | 1 | audit-only spec |

## Three biggest GAPS relative to Vision

### 🔴 Goal 6 — Doctrine evolves through dogfooding

**Currently missing:** the **closing of the loop**. Reflections accumulate
(Spec 045 enables semantic recall) but there is no **automated path from
"observed pattern" → "spec amendment proposal"**. Spec 014 was drafted
for exactly this. **NOT STARTED.**

**Concrete deliverable:** a `dogfood.parse_amendment` verb that reads
recent Reflections, classifies them (observation / proposal / refinement),
and emits a structured JSON-ops payload the human can apply to a spec.
Per Spec 014, this is the substrate that makes the dogfood loop genuine.

### 🔴 Goal 7 — Graph is the store, files render

**Currently missing:** the **write-side fix**. Today `agency/install.py`
writes files DIRECTLY. Spec 017 documented the fix: record a Reflection
node for each generated artefact, then render the file. Spec 043 shipped
the render side. **Spec 017 still NOT started.**

**Concrete deliverable:** `agency/install.py` refactor to record-then-
render. ~50 LOC change + tests. The doctrine-violation Jules's
Spec 015 review identified is finally closed.

### ⚠️ Goal 1 + 6 — `dogfood.collect` is anti-pattern

**Currently:** `agency/capabilities/dogfood.py::collect` parses
markdown files and writes nodes — which is exactly the **graph-as-
store violation Spec 017 fixes**. Spec 039 noted this in scope-cut;
Spec 017 will close it.

## The autonomous Vision-alignment audit recommendation

Order to maximize Goal coverage:

1. **Spec 020 finish** (one verb — `dogfood.export`). ✅ small. Unblocks
   17 directly. Goal 2/7.
2. **Spec 017** (graph-native dogfood ledgers). 🔴 critical Goal-7 gap.
   Closes the write-side of the graph-as-store doctrine. ~150 LOC.
3. **Spec 014** (observation-to-amendment). 🔴 critical Goal-6 gap.
   Composes Spec 017 (Reflections) + Spec 045 (semantic recall) into
   the doctrine-evolution path. ~200 LOC.

After those three, Vision is fully covered except Goal 3 marginal
gaps (Spec 011 + 022, both depend on Spec 021).

## How this matrix is maintained

This file IS itself a Goal-7 manifestation — it's a rendered view of
the spec landscape. The source of truth is each spec's own
`## Followup — Implementation Status` section. This matrix rolls
up. When a spec ships, both update in the same commit.
