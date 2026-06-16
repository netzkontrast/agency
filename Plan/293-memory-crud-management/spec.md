---
spec: 293
title: memory-crud-management
status: Partial (Slice 1 shipped)
depends_on: [048, 286, 290]
clusters: [memory, navigate]
vision_goals: [2, 4]
---

# Spec 293 — `manage`: generic CRUD over every graph node type

> User directive (2026-06-16): *"for every capability — the Memory part of
> agency needs read and write calls — a complete CRUD for every aspect."*

## Premise

Spec 290 specs the Memory **read-API** (`role=transform`, read-only). The user
directive extends it: every aspect of the graph needs **write** too — a
complete **C**reate/**R**ead/**U**pdate/**D**elete surface. Rather than add
per-capability CRUD verbs (21× duplication), ship ONE capability-agnostic
surface over EVERY ontology label — the elegant reading of "complete CRUD for
every aspect" (CORE.md §"one management API over all graph nodes").

## Design — the `manage` capability

A drop-in capability (`agency/capabilities/manage/`) with six verbs, generic
over any ontology `label`. Bi-temporal + append-only is preserved — nothing is
ever destructively deleted.

| Verb | Op | Mechanism |
|---|---|---|
| `manage.create(label, props)` | **C** | `record_and_serve` — ontology-validated; SERVES the intent. Names the violation on reject. |
| `manage.read(node_id)` | **R** | `recall` → `{labels, live, props}` (`live=False` once retracted). |
| `manage.list(label, where, live_only)` | **R** | `query_nodes` exact-match filter; drops closed versions by default. |
| `manage.update(node_id, props)` | **U** | in-place bi-temporal revision (stable id). |
| `manage.amend(node_id, changes)` | **U** | append-only `supersede` — old version kept, `SUPERSEDED_BY` the new id. |
| `manage.retract(node_id)` | **D** | bi-temporal **soft delete** — close the valid window (`vto=now`); history retained, current reads drop it. |

## Substrate additions

- `Memory.retract(node_id)` — close a node's valid window (soft delete).
- `CapabilityContext.supersede` / `.retract` — the write-side twins of
  `update`, delegating to `Memory` (raw graph writes stay in `memory.py`).

## Done-When

- [x] `create` mints any ontology label + SERVES the intent; rejects violations
  by naming the missing fields.
- [x] `read` returns props + a `live` flag.
- [x] `update` revises in place; `amend` supersedes append-only (new id).
- [x] `retract` soft-deletes bi-temporally; `read` flips `live=False`; `list`
  excludes it.
- [x] Auto-registers (drop-in); 5 acceptance scenarios green; substrate naming /
  welcome / capability-set invariants still green.
- [ ] **Follow-up:** wire `manage.list`/`read` through `project(query, budget)`
  for token-budgeted reads on large labels (Goal 1).
- [ ] **Follow-up:** fold Spec 290's read-API verbs (`state`, `open_intents`,
  `timeline`, …) onto `manage` so read + write share one capability.

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/manage/` (`create`/`read`/`list`/`update`/
`amend`/`retract`); `Memory.retract` + `ctx.supersede`/`ctx.retract`. 5
acceptance scenarios; 54 substrate-invariant tests still green.

**Still.** Token-budgeted projection wiring + folding the Spec 290 read verbs in.
