---
name: subagent
description: "Use when a unit of work should be composed as subagent-driven development — isolating a task to a dispatched subagent that returns a verified result."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# subagent capability

Subagent composes subagent-driven development: a self-contained task is dispatched into a clean context and its verified result returns to the orchestrator.

## When to use

- A self-contained task suited to a dispatched subagent
- Work whose context is heavy enough to isolate from the main thread

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `develop` | effect | Dispatch a worker child and gate it through spec-review then quality-review (effect). | [details](references/develop.md) |

## Example

```bash
await call_tool('capability_subagent_develop', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- (none documented)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`subagent-driven-development`** (discipline): write-spec → dispatch → spec-review → code-review
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'subagent-driven-development', 'inputs': {}, 'intent_id': '…'})`
  1. **write-spec** — Write a self-contained task spec for the subagent.
     Spell out the task so a fresh subagent succeeds with NO parent context — goal, acceptance, the files in scope, and what NOT to touch. A vague spec yields a vague implementation.
  2. **dispatch** — Dispatch the subagent to implement the spec.
     subagent.develop the spec as a child run; the subagent returns an implementation, not a conversation. Only the result crosses back.
  3. **spec-review** — Check the implementation against the spec.
     Verify the implementation does what the SPEC asked — scope, acceptance. A soft gate: note gaps, but the code-review gate is the hard one.
  4. **code-review** — Review the code for correctness + the Iron Law.
     Review for correctness first, then over-engineering / duplication (the Iron Law). Confirm this hard gate only when the code is genuinely mergeable.

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_subagent_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_subagent_develop", {"intent_id": iid})
```
