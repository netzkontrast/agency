---
name: thinking
description: "Use when structured rigor needed before commit; binding decisions need tradeoff + premortem + red-team; an assumption stack needs surfacing."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# thinking capability

10 method verbs (8 founding + 2 net-new: red_team + socratic) + 1 composite (apply_full_review) + 1 walkable skill (critical-thinking).

## When to use

- About to commit to a decision: run apply_decision_discipline first
- About to merge a complex spec: run apply_full_review
- Suspect a load-bearing assumption is unstated: run assumptions

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `apply_full_review` | act | Run the 8 founding thinking methods in sequence, producing a thinking-analysis artefact (act). | [details](references/apply_full_review.md) |
| `assumptions` | transform | Surface + classify implicit assumptions (load-bearing vs not) (transform). | [details](references/assumptions.md) |
| `decompose` | transform | MECE sub-problem decomposition (transform). | [details](references/decompose.md) |
| `first_principles` | transform | Strip the goal to fundamentals + reconstruct (transform). | [details](references/first_principles.md) |
| `inversion` | transform | Look for what guarantees failure rather than what guarantees success. | [details](references/inversion.md) |
| `premortem` | transform | Prospective failure analysis (transform). | [details](references/premortem.md) |
| `red_team` | transform | Adversarial review — adopt an attacker's stance + find failure paths (transform). | [details](references/red_team.md) |
| `second_order` | transform | Trace consequences N steps downstream (transform). | [details](references/second_order.md) |
| `socratic` | transform | Five-whys-deeper Socratic questioning (transform). | [details](references/socratic.md) |
| `steelman` | transform | Build the strongest possible argument against a position (transform). | [details](references/steelman.md) |
| `tradeoffs` | transform | Multi-criteria option scoring (transform). | [details](references/tradeoffs.md) |

## Example

```bash
await call_tool('capability_thinking_apply_full_review', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling decision rationales without the discipline → call thinking verbs
- Claiming a steelman without testing the inverse → call inversion + steelman

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`critical-thinking-pass`** (workflow): decompose → surface-assumptions → premortem → steelman-and-inversion → synthesize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'critical-thinking-pass', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_thinking_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_thinking_apply_full_review", {"intent_id": iid})
await call_tool("capability_thinking_assumptions", {"intent_id": iid})
await call_tool("capability_thinking_decompose", {"intent_id": iid})
await call_tool("capability_thinking_first_principles", {"intent_id": iid})
await call_tool("capability_thinking_inversion", {"intent_id": iid})
await call_tool("capability_thinking_premortem", {"intent_id": iid})
```

More verbs: `capability_thinking_red_team`, `capability_thinking_second_order`, `capability_thinking_socratic`, `capability_thinking_steelman`, `capability_thinking_tradeoffs`
