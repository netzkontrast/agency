<!-- agency-node: adr-theme-workflow -->
---
kind: adr-theme
layer: workflow
title: "Workflow — decisions"
scope: "the ADR-centred repo-development lifecycle (Spec 353 reconciliations)"
status: proposed
last_updated: 2026-06-21
---

# Workflow — decisions

> the ADR-centred repo-development lifecycle (Spec 353 reconciliations)

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Workflow — decisions | workflow | proposed | 3 live · 0 superseded |

## thematic, living ADRs — a Document per architecture layer, extended inline

| Decision ID | Status | Proposed By |
|---|---|---|
| decision:1b66bc25 | proposed | agent |

**In the context of** the owner wanting a handful of ADRs organised by layer rather than one file per decision,  
**facing** classic ADR's one-immutable-file-per-decision sprawl,  
**we decided for** thematic, living ADRs — a Document per architecture layer, extended inline,  
**and neglected** one file per decision, or a flat append-only ADR log,  
**to achieve** a handful of files while full decision history lives in the graph, immutability preserved at the node grain via SUPERSEDES,  
**accepting that** a theme file can become a dumping ground without the MIN-rule validators and the file is a render of the graph rather than its source.

| Relationship | ID | Notes |
|---|---|---|
| Part Of | document:5fb9723a | Workflow — decisions |

## specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both)

| Decision ID | Status | Proposed By |
|---|---|---|
| decision:a3200f65 | proposed | agent |

**In the context of** spec state living only in frontmatter and TODO.md with nothing enforcing agreement,  
**facing** silent drift between status frontmatter, the TODO.md roll-up and reality,  
**we decided for** specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both),  
**and neglected** graph-only state, frontmatter-only state, or mass-moving the legacy tree eagerly,  
**to achieve** a queryable board, enforced folder-frontmatter-node agreement, and the transition guard the ADR gate needs,  
**accepting that** moving a spec churns links and git history and three surfaces must be kept in agreement by a drift gate.

| Relationship | ID | Notes |
|---|---|---|
| Part Of | document:5fb9723a | Workflow — decisions |

## the ADR hinge — open to inprogress is blocked until the spec's decisions are approved

| Decision ID | Status | Proposed By |
|---|---|---|
| decision:ffa28143 | proposed | agent |

**In the context of** the WH(Y) decision record being the missing artefact between a spec and its code,  
**facing** implementation starting before the key decisions are captured and approved,  
**we decided for** the ADR hinge — open to inprogress is blocked until the spec's decisions are approved,  
**and neglected** no gate, an advisory-only ADR step, or letting an agent self-approve,  
**to achieve** decisions are captured and owner-approved before code begins, with hints re-loaded into context at implementation start,  
**accepting that** a hard gate can deadlock a spec — mitigated by a provenance-stamped owner override — and adds a human step.

| Relationship | ID | Notes |
|---|---|---|
| Part Of | document:5fb9723a | Workflow — decisions |

