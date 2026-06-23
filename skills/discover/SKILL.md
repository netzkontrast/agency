---
name: discover
description: "Use when a fresh or vague intent needs guided discovery BEFORE work begins —"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# discover capability



## When to use

- An underspecified ask arrives and the WHY is captured, not discovered
- An intent has no measurable acceptance criteria yet
- Work is about to start against an unconfirmed or ungrounded intent

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `acceptance` | transform | Derive testable, Gherkin-shaped acceptance criteria from the Intent (transform). | [details](references/acceptance.md) |
| `ask` | transform | Build ONE well-formed AskUserQuestion payload from DERIVED options (transform). | [details](references/ask.md) |
| `clarify` | act | Resolve a draft Intent's ambiguities, folding each answer back (act). | [details](references/clarify.md) |
| `clarity` | transform | Score a captured Intent's clarity / readiness (transform, read-only). | [details](references/clarity.md) |
| `clarity_gate` | effect | Composite clarity gate — records outcome via gate.check (effect). | [details](references/clarity_gate.md) |
| `interview` | act | Run the adaptive elicitation interview → a DRAFT Intent (act). | [details](references/interview.md) |
| `scope` | act | Elicit in-/out-of-scope boundaries (act). | [details](references/scope.md) |
| `status` | transform | Smoke verb — report the registered ``discover`` ontology surface. | [details](references/status.md) |

## Example

```bash
await call_tool('capability_discover_acceptance', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Starting work against an unconfirmed intent → run ``discover.interview`` first
- Inventing AskUser options instead of deriving them from evidence → ``discover.ground``
- Treating a one-line seed as a finished intent → walk ``guided-discovery``

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`guided-discovery`** (discipline): elicit → ground → clarify → frame → examine → scope → decide
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'guided-discovery', 'inputs': {}, 'intent_id': '…'})`
  1. **elicit** — Draw out a draft intent through a short interview.
     Interview the user to surface what they actually want — purpose, deliverable, the rough shape. Capture a draft intent; don't demand precision yet, that's later phases.
  2. **ground** — Ground the draft in evidence + a feasibility read.
     Check the draft against reality — cite what exists (code, docs, prior art) and signal whether it's feasible. A grounded intent beats an aspirational one.
  3. **clarify** — Resolve the ambiguities the draft hides.
     Ask the questions whose answers would change the work; resolve each ambiguity before it propagates into the plan.
  4. **frame** — Sharpen the draft into a precise intent.
     Restate the intent as a sharp purpose / deliverable / acceptance triple — the spine every downstream verb serves.
  5. **examine** — Pressure-test the sharpened intent.
     Run a critical-thinking pass over the framed intent — assumptions, failure modes — and capture what it surfaces before committing scope.
  6. **scope** — Draw the scope boundaries + acceptance criteria.
     State what's IN and OUT of scope and the concrete acceptance checks. Boundaries prevent scope creep; acceptance makes 'done' decidable.
  7. **decide** — Confirm the intent through the clarity gate.
     The clarity gate computes whether the intent is confirmable (purpose + deliverable + acceptance all sharp). It passes only when discovery genuinely converged — not on demand.
