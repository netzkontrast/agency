<!-- agency-node: adr-theme-workflow -->
---
kind: adr-theme
layer: workflow
title: "Workflow — decisions"
scope: "the ADR-centred repo-development lifecycle (Spec 353 reconciliations)"
status: proposed
---

# Workflow — decisions

> the ADR-centred repo-development lifecycle (Spec 353 reconciliations)

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Workflow — decisions | workflow | proposed | 4 live · 0 superseded |

## specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both)

| Decision ID | Status | Proposed By |
|---|---|---|
| WORKFLOW-01 | proposed | agent |

**In the context of** spec state living only in frontmatter and TODO.md with nothing enforcing agreement,  
**facing** silent drift between status frontmatter, the TODO.md roll-up and reality,  
**we decided for** specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both),  
**and neglected** graph-only state, frontmatter-only state, or mass-moving the legacy tree eagerly,  
**to achieve** a queryable board, enforced folder-frontmatter-node agreement, and the transition guard the ADR gate needs,  
**accepting that** moving a spec churns links and git history and three surfaces must be kept in agreement by a drift gate.

**Source:** [`Plan/inprogress/357-spec-state-lifecycle/spec.md`](../../Plan/inprogress/357-spec-state-lifecycle/spec.md) — "Owner directive: *"Es gibt mehrere Verzeichnisse in Plan, dann neu: `/draft /open /inprogress /superseded /done`"

## the ADR hinge — open to inprogress is blocked until the spec's decisions are approved

| Decision ID | Status | Proposed By |
|---|---|---|
| WORKFLOW-02 | proposed | agent |

**In the context of** the WH(Y) decision record being the missing artefact between a spec and its code,  
**facing** implementation starting before the key decisions are captured and approved,  
**we decided for** the ADR hinge — open to inprogress is blocked until the spec's decisions are approved,  
**and neglected** no gate, an advisory-only ADR step, or letting an agent self-approve,  
**to achieve** decisions are captured and owner-approved before code begins, with hints re-loaded into context at implementation start,  
**accepting that** a hard gate can deadlock a spec — mitigated by a provenance-stamped owner override — and adds a human step.

**Source:** [`Plan/done/358-workflow-capability/spec.md`](../../Plan/done/358-workflow-capability/spec.md) — "Owner directive: *"Ziel ist … einen Lifecycle für die Arbeit am Repo zu erstellen … beginnend mit Intent-Erfassung und Interview-Triage — Brainstorm und ggf"

## thematic, living ADRs — a Document per architecture layer, extended inline

| Decision ID | Status | Proposed By |
|---|---|---|
| WORKFLOW-03 | proposed | agent |

**In the context of** the owner wanting a handful of ADRs organised by layer rather than one file per decision,  
**facing** classic ADR's one-immutable-file-per-decision sprawl,  
**we decided for** thematic, living ADRs — a Document per architecture layer, extended inline,  
**and neglected** one file per decision, or a flat append-only ADR log,  
**to achieve** a handful of files while full decision history lives in the graph, immutability preserved at the node grain via SUPERSEDES,  
**accepting that** a theme file can become a dumping ground without the MIN-rule validators and the file is a render of the graph rather than its source.

**Source:** [`Plan/done/354-adr-ontology-capability/spec.md`](../../Plan/done/354-adr-ontology-capability/spec.md) — "The `adr` repo (`/adr/specs/SPEC-001-A..E`) defines the *enhanced WH(Y) ADR* on paper"

## derive reference-doc fragments from live code via `<!-- derived -->` fences

| Decision ID | Status | Proposed By |
|---|---|---|
| WORKFLOW-04 | approved | agent |

**In the context of** hand-authored reference docs copying facts from code (the substrate-tool roster, a capability's verbs, the driver-boundary set) that rot on every refactor,  
**facing** those hand-typed fragments going silently stale while `check-doc-drift` could only demand a whole-doc re-stamp,  
**we decided for** code-introspection `<!-- derived:<kind> -->` fences that regenerate those fragments from the live engine, with `check-doc-drift` triaging derived-zone drift (auto-fix via `derive_docs --write-docs`) apart from prose drift (hand-review),  
**and neglected** auto-generating whole docs, or leaving every fragment hand-maintained,  
**to achieve** the derivable fragments staying current mechanically while the hand-review surface shrinks to genuine prose,  
**accepting that** authors must wrap a derivable fragment in a fence and a `derive_docs --check-docs` gate runs in `check-drift`.

**Source:** [`Plan/done/389-derived-fence-reference-docs/spec.md`](../../Plan/done/389-derived-fence-reference-docs/spec.md)

