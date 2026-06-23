---
name: doctrine
description: "Use when a decision must be grounded in a stated principle/rule, or two"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# doctrine capability

Closes the SuperClaude/superpowers port audit: PRINCIPLES + RULES were the only unported aspect of that doctrine. Agency already *expresses* them as prose (CLAUDE.md), skill Red flags, persona approaches and `mode` behaviors; doctrine makes them **machine-queryable + citable**. Decidable (like `mode`/`panel`, no LLM): a roster of engineering principles, priority-ranked behavioral rules, a conflict-resolution hierarchy (the highest-leverage part — safety > correctness > maintainability > speed), and a `DoctrineCitation` recording that a principle *drove* an action (auditable provenance, the same way `mode` records a posture).

## When to use

- Two rules/concerns conflict and you need the priority-ranked winner
- An action was taken *because of* a principle and should be cited (provenance)
- You need the behavioral rules for a situation, filtered by priority

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `cite` | effect | Record that a principle or rule DROVE an action — a DoctrineCitation SERVING the intent (auditable provenance, Spec 303). | [details](references/cite.md) |
| `principles` | act | The engineering-principles roster — name · statement (Spec 303). | [details](references/principles.md) |
| `resolve` | act | Adjudicate two conflicting concerns by the conflict hierarchy (safety > correctness > maintainability > speed) — read-only (Spec 303). | [details](references/resolve.md) |
| `rules` | act | The behavioral rules, optionally filtered by priority (Spec 303). | [details](references/rules.md) |

## Example

```bash
await call_tool('capability_doctrine_cite', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Guessing which concern wins a safety-vs-speed tradeoff → doctrine.resolve
- Asserting "best practice" with no cited principle → doctrine.cite

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`doctrine-usage`** (usage): use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'doctrine-usage', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_doctrine_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_doctrine_cite", {"intent_id": iid})
await call_tool("capability_doctrine_principles", {"intent_id": iid})
await call_tool("capability_doctrine_resolve", {"intent_id": iid})
await call_tool("capability_doctrine_rules", {"intent_id": iid})
```
