---
name: manage
description: "The write/read management surface that completes the Memory pillar: a single, capability-AGNOSTIC CRUD over EVERY ontology label, so every aspect of the graph — Document, Intent, Track, Novel, Reflection, Session, … — has Create, Read, Update, Amend and Retract without per-capability code. Use when an agent must directly create / read / update / amend / soft-delete a"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# manage capability

The write/read management surface that completes the Memory pillar: a single, capability-AGNOSTIC CRUD over EVERY ontology label, so every aspect of the graph — Document, Intent, Track, Novel, Reflection, Session, … — has Create, Read, Update, Amend and Retract without per-capability code. Complements the read-only Spec 290 read-API; this is the write half the four pillars need.

## When to use

- A node's state must change but no domain verb covers it
- A typed entity must be created or queried generically
- An obsolete node must be retracted without destroying history

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `amend` | effect | AMEND append-only — close the old version, create a new one linked ``SUPERSEDED_BY`` (Spec 293). | [details](references/amend.md) |
| `artefacts` | act | ARTEFACTS produced under an intent + their source invocations (Spec 290, Memory pillar). | [details](#artefacts) |
| `create` | effect | CREATE a node of any ontology ``label``; SERVES the intent (Spec 293). | [details](references/create.md) |
| `list` | act | LIST nodes of a ``label``, optionally filtered by exact-match ``where`` (Spec 293). | [details](references/list.md) |
| `open_intents` | act | OPEN-INTENTS — live intents + acceptance + SERVES subtree size, busiest first (Spec 290, Intent pillar). | [details](#open_intents) |
| `read` | act | READ a node by id — its current properties + a ``live`` flag (False once retracted; Spec 293). | [details](references/read.md) |
| `retract` | effect | RETRACT — bi-temporal SOFT delete: close the node's valid window so current reads drop it, history retained (Spec 293). | [details](references/retract.md) |
| `state` | act | STATE rollup — the "where are we" dashboard (Spec 290, on manage). | [details](#state) |
| `timeline` | act | TIMELINE — the ordered Event + Invocation history for an intent (Spec 290, Lifecycle · Memory). | [details](#timeline) |
| `update` | effect | UPDATE a node in place — a bi-temporal revision, stable id (Spec 293). | [details](references/update.md) |

## Example

```bash
await call_tool('capability_manage_amend', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-writing `ctx.memory.g.query` in a verb → use manage.list / manage.read
- Destructively deleting a node → use manage.retract (bi-temporal soft delete)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`manage-usage`** (usage): use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'manage-usage', 'inputs': {}, 'intent_id': '…'})`

## artefacts

ARTEFACTS produced under an intent + their source invocations (Spec 290, Memory pillar).

Parameters: `(for_intent_id: 'str')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/artefacts.md.)_

## open_intents

OPEN-INTENTS — live intents + acceptance + SERVES subtree size, busiest first (Spec 290, Intent pillar).

Parameters: `(top: 'int' = 20)`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/open_intents.md.)_

## state

STATE rollup — the "where are we" dashboard (Spec 290, on manage).

Parameters: `(for_intent_id: 'str' = '')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/state.md.)_

## timeline

TIMELINE — the ordered Event + Invocation history for an intent (Spec 290, Lifecycle · Memory).

Parameters: `(for_intent_id: 'str', limit: 'int' = 100)`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/timeline.md.)_
