---
name: persona
description: "Use when a task needs a specific engineering specialist's lens — architecture,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# persona capability

A native reimplementation of SuperClaude's specialist agents (architects, engineers, analysts, mentors) as a built-in, dispatchable persona registry — NOT ingested prompt files. Decidable: a task is matched to the right specialist by domain, and a dispatch brief (role + focus + approach + task) is composed and recorded as provenance. Pairs with `panel` (business experts) and `subagent` (the dispatch machinery).

## When to use

- A task that maps to a named specialist (architect, security, performance, QA)
- An ambiguous task that should be routed to the right expert first
- Composing a focused subagent dispatch from a specialist role

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `list` | act | The specialist-persona roster — name · focus · approach. | [details](references/list.md) |
| `recommend` | act | Recommend the specialist persona(s) best matched to a ``task`` by decidable domain overlap (read-only). | [details](references/recommend.md) |
| `summon` | effect | Summon a specialist — compose a dispatch brief + record provenance (Spec 297). | [details](references/summon.md) |

## Example

```bash
await call_tool('capability_persona_list', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Generic dispatch for a security-critical task → summon the security-engineer
- Building before requirements are concrete → summon the requirements-analyst

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`specialist-dispatch`** (discipline): match → brief → dispatch → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'specialist-dispatch', 'inputs': {}, 'intent_id': '…'})`
  1. **match** — Match the task to a specialist persona.
     Pick the persona whose expertise fits the task (backend, security, frontend, …). The match is the leverage — a mismatched specialist wastes the dispatch.
  2. **brief** — Write a self-contained brief for the persona.
     Brief the specialist so it succeeds with NO parent context — the task, the acceptance, the scope. A persona is only as good as its brief.
  3. **dispatch** — Dispatch the specialist as a child run.
     Dispatch the persona as a child Lifecycle + Invocation; only the result crosses back. Walk dispatch-decision first if unsure it beats inline.
  4. **verify** — Verify the specialist's output.
     Check the returned work against the brief's acceptance — a specialist's output is a proposal until verified. Confirm only on a genuine match.

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_persona_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_persona_list", {"intent_id": iid})
await call_tool("capability_persona_recommend", {"intent_id": iid})
await call_tool("capability_persona_summon", {"intent_id": iid})
```
