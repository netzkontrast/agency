<!-- agency-node: adr-theme-lifecycle -->
---
kind: adr-theme
layer: lifecycle
title: "Lifecycle — decisions"
scope: "how stateful entities transition, with provenance"
status: proposed
---

# Lifecycle — decisions

> how stateful entities transition, with provenance

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Lifecycle — decisions | lifecycle | proposed | 2 live · 0 superseded |

## ctx.lifecycle.move is the sole state writer; domain code never writes state directly

| Decision ID | Status | Proposed By |
|---|---|---|
| LIFECYCLE-01 | proposed | agent |

**In the context of** a Lifecycle node's state changing only through a legal, provenance-stamped transition,  
**facing** domain verbs tempted to set a status field directly,  
**we decided for** ctx.lifecycle.move is the sole state writer; domain code never writes state directly,  
**and neglected** direct property writes, or per-capability transition helpers,  
**to achieve** one guarded bi-temporal writer, illegal transitions rejected centrally, and a single writer check-drift can enforce,  
**accepting that** an extra indirection for a simple status change and a guard that must know every machine.

**Source:** [`Plan/inprogress/339-lifecycle-capability-write-frame/spec.md`](../../Plan/inprogress/339-lifecycle-capability-write-frame/spec.md) — "Spec 338 §Architecture calls for a `lifecycle` capability that owns the CORE.md §3 verb frame"

## lifecycle machines are data (machines.json), not code

| Decision ID | Status | Proposed By |
|---|---|---|
| LIFECYCLE-02 | proposed | agent |

**In the context of** each new stateful concept — spec-state, decision-status, loop — needing a state machine,  
**facing** an engine code edit for every new machine,  
**we decided for** lifecycle machines are data (machines.json), not code,  
**and neglected** hard-coded Python transition tables, or a per-capability state enum,  
**to achieve** adding a machine is a data entry and its states widen the shared enum automatically,  
**accepting that** transition legality is validated at runtime from data rather than checked by the type system.

**Source:** [`Plan/inprogress/340-lifecycle-state-machine-transitions/spec.md`](../../Plan/inprogress/340-lifecycle-state-machine-transitions/spec.md) — "`ontology.py:58 LifecycleState` constrains the *value* of `state`, but Spec 338 §Why item 2 documents the real defect — no transition is enforced"

