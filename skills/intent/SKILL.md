---
name: intent
description: "Use when examining a goal before committing to an approach — decomposing it, surfacing its assumptions, stress-testing it with a premortem, or weighing trade-offs."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# intent capability

Intent is the reasoning capability: it turns the human-owned goal into structured critical-thinking scaffolds — decomposition, assumption-surfacing, premortem, first-principles, inversion, steelman, second-order, and trade-off analysis — each a deterministic method an agent fills in against the current intent.

## When to use

- A goal whose approach is unclear and needs structured decomposition
- A plan resting on unstated assumptions worth surfacing
- A decision between options that needs an explicit trade-off pass
- A risky course where a premortem would expose failure modes early

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `assumptions` | transform | Surface + classify the implicit assumptions a goal rests on (load-bearing vs not). | [details](references/assumptions.md) |
| `brooks_lint` | transform | BROOKS-LINT — the 9th critical-thinking method: a conceptual-integrity pass grounded in Fred Brooks (*Mythical Man-Month* / *No Silver Bullet*). | [details](references/brooks_lint.md) |
| `decompose` | transform | Decompose a goal into MECE sub-problems — the structured break-down method. | [details](references/decompose.md) |
| `first_principles` | transform | Strip a goal to fundamental truths and rebuild — bypassing inherited assumptions. | [details](references/first_principles.md) |
| `inversion` | transform | Invert the goal — ask what would GUARANTEE failure, then avoid exactly that. | [details](references/inversion.md) |
| `premortem` | transform | Premortem — assume the goal FAILED, reason backward to causes + mitigations. | [details](references/premortem.md) |
| `second_order` | transform | Trace second- and third-order consequences — 'and then what?' past the first effect. | [details](references/second_order.md) |
| `steelman` | transform | Build the STRONGEST version of the opposing or alternative position. | [details](references/steelman.md) |
| `suggests` | transform | Project the serving intent + the last verb's state to the next applicable skill (Spec 026 Part B — Intent owns the intent→skill projection; a RECOMMENDATION, not a dispatch). | [details](references/suggests.md) |
| `tradeoffs` | transform | Build an explicit trade-off matrix — options × criteria — for a decision. | [details](references/tradeoffs.md) |
| `triage` | act | Triage a Finding — the intent's stance on it (Spec 381 §4). | [details](references/triage.md) |

## Example

```bash
await call_tool('capability_intent_assumptions', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Committing to an approach without surfacing assumptions → capability_intent_assumptions
- Shipping a risky plan unexamined → run capability_intent_premortem first

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`critical-thinking`** (discipline): frame → surface → stress-test → weigh → decide
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'critical-thinking', 'inputs': {}, 'intent_id': '…'})`
  1. **frame** — State the problem precisely before reasoning about it.
     Decompose the intent into a sharp problem statement — what's actually being decided, and why now. A fuzzy frame produces fuzzy thinking.
  2. **surface** — Surface the load-bearing assumptions.
     List the assumptions the approach rests on — the ones that, if wrong, change the decision. Name them explicitly so they can be tested.
  3. **stress-test** — Stress-test the approach against failure.
     Pre-mortem it (how does it fail?), invert it (what must NOT happen?), and brooks-lint it (essential vs accidental complexity). Collect the failure modes the methods surface.
  4. **weigh** — Weigh the tradeoffs and second-order effects.
     For each viable option, state its tradeoff and its second-order consequence. The best first-order choice often loses on the second order.
  5. **decide** — Commit to an approach with its rationale.
     Choose, and state WHY this option beats the alternatives given the assumptions + tradeoffs. Confirm this gate only with a decision, not a shortlist.

## The Intent pillar (concept)

Intent is the first of agency's four concepts (Intent · Capability · Lifecycle ·
Memory) and the spine the other three ride. Every session SERVES an intent: a
typed record of purpose (WHY), deliverable (WHAT), and acceptance (how you will
KNOW it is done). No verb runs unanchored — each Invocation links back to the
intent it serves and each Artefact to the intent it produces, which is what turns
a session's work into queryable provenance rather than a one-shot transcript. The
provenance moat IS the moat; an unanchored action is lost the moment the session
ends.

The clarity gate is three steps. `intent.bootstrap` (or `capture`) mints the
intent from purpose/deliverable/acceptance. `intent.clarify` surfaces the
ambiguities a vague request hides — the questions whose answers would change the
plan. `intent.confirm` flips the intent to `confirmed`, the state every
downstream verb checks before it will run. The discipline: sharpen a vague intent
BEFORE work, not mid-flight.

Critical-thinking methods (Spec 091) pressure-test an intent: `intent.assumptions`
lists the load-bearing assumptions a plan rests on; `intent.socratic` asks the
questions that expose gaps; the rest of the eight methods stress different
failure modes. Reach for one before a risky or large change — the cheapest place
to catch a wrong plan is before any code is written.
