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
| Lifecycle — decisions | lifecycle | in-progress | 5 live · 0 superseded |

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

## a skill is a typed phase-graph — six types with a per-type required core, and a phase is a first-class object with inline content

| Decision ID | Status | Proposed By |
|---|---|---|
| LIFECYCLE-03 | approved | agent |

**In the context of** skills being agency's Lifecycle templates that a fresh agent walks one phase at a time,  
**facing** a flat `{name, description, body}` skill and a structure-only `{index, name, produces}` phase that could hold no instructions,  
**we decided for** a typed, layered Phase + Skill schema (`type ∈ pillar|capability|technique|pattern|reference|discipline`; a phase carries goal / instructions / example / done_when / freedom) with a small required CORE per type,  
**and neglected** one universal skill shape, or a gold-plated all-fields-required schema,  
**to achieve** a skill rich enough to express the R1–A7 best-practices, validated at parse with typed codes, while staying frugal (only the per-type core is required),  
**accepting that** two orthogonal axes — `kind` (walk-shape) and `type` (classification) — the author must understand.

**Source:** [`Plan/done/371-phase-skill-schema/spec.md`](../../Plan/done/371-phase-skill-schema/spec.md)

## the phase graph is the single source — the walk and the rendered file read one phase

| Decision ID | Status | Proposed By |
|---|---|---|
| LIFECYCLE-04 | approved | agent |

**In the context of** a walking agent and a reader of the rendered SKILL.md needing identical phase instructions,  
**facing** the walk surfacing only `{index, name, produces, gate}` while the file rendered phase NAMES only — the content lived nowhere both could read,  
**we decided for** `SkillRun.current()` surfacing the phase's goal / instructions / example / freedom AND the renderer inlining the same fields from that one source (A2 parity),  
**and neglected** a separate authored walk-script, or duplicating the instructions in the file,  
**to achieve** walk content == rendered content for every phase, enforced by a parity test,  
**accepting that** the single source must carry enough content to serve both surfaces.

**Source:** [`Plan/done/372-phase-single-source/spec.md`](../../Plan/done/372-phase-single-source/spec.md)

## the four concepts each ship a committed pillar skill

| Decision ID | Status | Proposed By |
|---|---|---|
| LIFECYCLE-05 | approved | agent |

**In the context of** Intent · Capability · Lifecycle · Memory being agency's load-bearing concepts a fresh agent must grasp,  
**facing** the concepts living only in prose canon docs, not as discoverable, listable skills,  
**we decided for** each concept shipping a committed `type=pillar` skill rendered via the per-type pillar template,  
**and neglected** leaving the concepts as canon docs only, or deriving them from a capability docstring,  
**to achieve** the concepts being first-class in the skill registry (`agency_welcome` + `skills.find` list them),  
**accepting that** a pillar whose name collides with a capability (intent) augments that cap's skill rather than owning the file.

**Source:** [`Plan/done/375-pillar-skills/spec.md`](../../Plan/done/375-pillar-skills/spec.md)

