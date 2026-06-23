<!-- agency-node: adr-theme-capabilities -->
---
kind: adr-theme
layer: capabilities
title: "Capabilities — decisions"
scope: "how capabilities are authored, discovered and bounded"
status: proposed
---

# Capabilities — decisions

> how capabilities are authored, discovered and bounded

| Master ADR | Layer | Aggregate Status | Decisions |
|---|---|---|---|
| Capabilities — decisions | capabilities | in-progress | 5 live · 0 superseded |

## a capability is a self-registering folder under agency/capabilities/ (the drop-in bar)

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-01 | proposed | agent |

**In the context of** agency needing to grow its capability surface without central wiring edits,  
**facing** registering each capability by hand in an engine manifest, the CLI and the MCP wiring,  
**we decided for** a capability is a self-registering folder under agency/capabilities/ (the drop-in bar),  
**and neglected** a central registry list, or explicit per-capability install wiring,  
**to achieve** adding a folder gains a discoverable, walkable, CLI-exposed and MCP-wired capability for free,  
**accepting that** auto-discovery hides load order and a malformed folder can fail registration at import time.

**Source:** [`Plan/inprogress/016-capability-authoring-doctrine/spec.md`](../../Plan/inprogress/016-capability-authoring-doctrine/spec.md) — "The Core canon (`docs/vision/CORE.md`) defines WHAT a capability is — an invokable action with role-tagged verbs, owning an ontology fragment, exposed isomorphically over MCP / Skills / bash CLI"

## keep manage as capability-agnostic generic CRUD; domain verbs live in their own capability

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-02 | proposed | agent |

**In the context of** ADR needing WH(Y)-validate, supersede-with-forward-ref and aggregate-status verbs,  
**facing** the pull to add ADR-specific verbs onto the generic manage surface,  
**we decided for** keep manage as capability-agnostic generic CRUD; domain verbs live in their own capability,  
**and neglected** ADR verbs on manage, or a single god-capability,  
**to achieve** manage keeps a clean generic charter while the adr capability owns its domain,  
**accepting that** two surfaces to learn (generic CRUD versus domain) and some duplicated create/read ergonomics.

**Source:** [`Plan/done/290-management-capability/spec.md`](../../Plan/done/290-management-capability/spec.md) — "(evidence + doctrine) An agent today cannot ask *"what is the current state — open intents, lifecycle status, research, artefacts — across the whole graph?"* without either raw Cypher…"

## a capability's skill data derives from its docstring; an authored skill.yaml is the A6 override, not a committed file per capability

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-03 | approved | agent |

**In the context of** every capability needing v2 skill data while already carrying a module docstring that is its single source of judgment,  
**facing** hand-authoring and committing a `skill.yaml` per capability (the literal pre-375 plan) that would duplicate every docstring,  
**we decided for** skills DERIVING from the capability's docstring SkillDoc by default (`owner=auto`); a capability that ships `<cap>/skill.yaml` overrides it (`owner=capability`, A6) — the same v2 schema validates both,  
**and neglected** a committed-`skill.yaml`-per-capability mandate (duplicates docstrings; violates derive-don't-duplicate),  
**to achieve** every capability resolving to a valid v2 Skill with zero authored files, richer skill data being an opt-in override,  
**accepting that** the derived shim is minimal — the docstring is its ceiling until a capability authors more.

**Source:** [`Plan/done/378-capability-skill-migration/spec.md`](../../Plan/done/378-capability-skill-migration/spec.md)

## one per-type renderer renders every skill from its type template — no second render path

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-04 | approved | agent |

**In the context of** skills of different types needing different shapes, rendered deterministically at install (A7),  
**facing** a single generic template for everything plus a divergent second author path (the C2 coherence risk),  
**we decided for** one `render_typed_skill` that selects `render/skill/<type>.md` by `Skill.type` and inlines the schema-driven self-contained body, with pillars converged onto it,  
**and neglected** a template per capability, or parallel render functions per type,  
**to achieve** every skill type rendering its required sections from one deterministic renderer; the apologetic Tier-B stub replaced by a lint finding,  
**accepting that** a capability's SKILL.md still composes its verb table around the per-type body (its capability-specific concern).

**Source:** [`Plan/done/373-per-type-templates-renderer/spec.md`](../../Plan/done/373-per-type-templates-renderer/spec.md)

## the skill surface is bounded by a schema lint and a repo-wide self-containment discipline gate

| Decision ID | Status | Proposed By |
|---|---|---|
| CAPABILITIES-05 | approved | agent |

**In the context of** a typed skill schema being inert unless something enforces it across the open capability set,  
**facing** schema-valid-but-empty skills (phases with no instructions) shipping unnoticed,  
**we decided for** `lint_skill_schema` validating every skill against the v2 schema and a repo-wide discipline gate blocking any discipline whose phases are not self-contained (A1),  
**and neglected** trusting authors, or a permanent warn-only gate (kept only as the migration ramp),  
**to achieve** a new skill or discipline being unable to ship marker-less or content-less — the gate fails `check-drift`,  
**accepting that** every discipline must carry real phase instructions before it lands.

**Source:** [`Plan/done/377-skill-lint-enforcement/spec.md`](../../Plan/done/377-skill-lint-enforcement/spec.md)

