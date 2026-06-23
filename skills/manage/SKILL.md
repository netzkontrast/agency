---
name: manage
description: "Use when an agent must directly create / read / update / amend / soft-delete a"
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
| `artefacts` | act | ARTEFACTS produced under an intent + their source invocations (Spec 290, Memory pillar). | [details](references/artefacts.md) |
| `create` | effect | CREATE a node of any ontology ``label`` that SERVES the intent (Spec 293). | [details](references/create.md) |
| `lifecycle` | act | LIFECYCLE READ — the Spec 341 `read` frame: one Lifecycle's full state rolled up in ONE call (state · phase · kind · serving intent · agent · gates), so the agent need not know which surface holds each piece. | [details](references/lifecycle.md) |
| `lifecycle_trail` | act | LIFECYCLE WATCH — the Spec 341 `watch` frame: the ordered Spec 344 `lifecycle_transition` Event trail recorded `OBSERVED_DURING` this lifecycle (what `move` emits), so an observer reads the durable history instead of polling `state`. | [details](references/lifecycle_trail.md) |
| `list` | act | LIST nodes of a ``label``, optionally filtered by exact-match ``where`` (Spec 293). | [details](references/list.md) |
| `open_intents` | act | OPEN-INTENTS — live intents + acceptance + SERVES subtree size, busiest first (Spec 290, Intent pillar). | [details](references/open_intents.md) |
| `project` | act | PROJECT — a query-ranked, token-budgeted slice of a label's live nodes (Spec 290/293: the `project(query, budget)` read primitive, Goal 1). | [details](references/project.md) |
| `provenance` | act | PROVENANCE — the typed cross-concern join (Spec 330/290, Memory · Capability · Lifecycle): every Invocation serving the intent + its Agent + the Artefacts it produced (or that serve the intent) + the Lifecycle states, read through the typed ``IntentStore`` join rather than a Cypher traversal. | [details](references/provenance.md) |
| `read` | act | READ a node by id — its current properties + a ``live`` flag (False once retracted; Spec 293). | [details](references/read.md) |
| `render` | act | RENDER the read-API as a compact markdown dashboard — the "where are we" view, rule-2 graph→markdown on demand (Spec 290 Slice 2). | [details](references/render.md) |
| `research_state` | act | RESEARCH-STATE — open research leads with their claims, citations and verification status, grouped (Spec 290, Memory pillar). | [details](references/research_state.md) |
| `retract` | effect | RETRACT — bi-temporal SOFT delete: close the node's valid window so current reads drop it, history retained (Spec 293). | [details](references/retract.md) |
| `state` | act | STATE rollup — the "where are we" dashboard (Spec 290, on manage). | [details](references/state.md) |
| `subtree` | act | SUBTREE — the ``PARENT_INTENT`` sub-intent tree rooted at an intent (root inclusive), walked over the typed ``parent_intent_id`` FK (Spec 330; makes ``IntentStore.intent_tree`` load-bearing). | [details](references/subtree.md) |
| `timeline` | act | TIMELINE — the ordered Event + Invocation history for an intent (Spec 290, Lifecycle · Memory). | [details](references/timeline.md) |
| `update` | effect | UPDATE a node in place — a bi-temporal revision, stable id (Spec 293). | [details](references/update.md) |
| `whats_next` | act | WHATS-NEXT — blocked items + the next actions against an intent's acceptance (Spec 290, Lifecycle pillar; the navigate core). | [details](references/whats_next.md) |

## Example

```bash
await call_tool('capability_manage_amend', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-writing `ctx.memory.g.query` in a verb → use manage.list / manage.read
- Destructively deleting a node → use manage.retract (bi-temporal soft delete)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`lifecycle-management`** (discipline): survey → triage → unblock → advance → close → report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'lifecycle-management', 'inputs': {}, 'intent_id': '…'})`
  1. **survey** — Survey every in-flight lifecycle's state.
     Read the board — open intents + every Lifecycle by state. Query the live state from the graph, never by eyeballing status fields.
  2. **triage** — Triage what's blocked and what's next.
     Identify which lifecycles are stalled and WHY — the blocker per stuck item. Separate genuinely-blocked from simply not-started.
  3. **unblock** — Clear the blockers you can.
     Resume the lifecycles whose gate now passes; for the rest, name the precise unblock action. Don't force a gate that hasn't met its predicate.
  4. **advance** — Advance the unblocked lifecycles.
     Move each unblocked lifecycle to its next legal state via lifecycle.move (the sole state writer) — illegal transitions are rejected by the machine.
  5. **close** — Close the ones that reached terminal.
     Close lifecycles that genuinely reached a terminal state; verify the closing gate. COMPLETED is not closed until verified.
  6. **report** — Mirror the board to a readable artefact.
     Project the live board state to the lifecycle-board document so the human sees what's in flight without re-querying.
