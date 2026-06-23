---
name: workflow
description: "Use when a spec must move through its development stages (draft → open →"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# workflow capability



## When to use

- A new spec needs a state machine → open_spec
- A spec advances a stage and the transition must be guarded + recorded → move_spec
- "What's in /inprogress?" → board, answered from the graph

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `approve_decisions` | effect | APPROVE_DECISIONS — phase 11: run `adr.approve` over every decision that `REFINES` the spec (the ADR hinge's human step). | [details](references/approve_decisions.md) |
| `begin_impl` | effect | BEGIN_IMPL — phase 12: the guarded ``open→inprogress`` move (BLOCKED by the ADR hinge until every decision is approved — `spec_decisions_ready`), then load the approved decisions' `adr.hints` into the build context. | [details](references/begin_impl.md) |
| `board` | transform | BOARD — the graph-native spec board: live SpecLifecycles grouped by their ``spec``-machine state (optionally filtered to one ``state``). | [details](references/board.md) |
| `index` | transform | INDEX — the "alle Specs sind indiziert, korrekte Frontmatter" guarantee (Spec 357). | [details](references/index.md) |
| `mark_done` | effect | MARK_DONE — phase 14, the owner's done-cascade. | [details](references/mark_done.md) |
| `move_spec` | effect | MOVE_SPEC — advance the spec's Lifecycle to ``to_state`` via ``ctx.lifecycle.move`` (the SOLE state writer — Spec 339; an illegal edge is rejected by the ``spec`` machine's transition table). | [details](references/move_spec.md) |
| `open_spec` | act | OPEN_SPEC — mint a SpecLifecycle (machine ``spec``, state ``draft``) for a spec ``Document``, ``TRACKS``-bound to it and SERVING the intent. | [details](references/open_spec.md) |
| `to_open` | effect | TO_OPEN — phase 10: move the spec ``draft→open`` and extract its decisions into ``proposed`` drafts (`adr.extract_decisions apply=True`). | [details](references/to_open.md) |

## Example

```bash
await call_tool('capability_workflow_approve_decisions', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-editing a spec's ``status:`` / folder without advancing the Lifecycle → drift
- Moving open→inprogress before its ADR decisions are approved → the gate refuses
- Writing ``Lifecycle.state`` directly → only ``ctx.lifecycle.move`` may (Spec 339)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`develop-spec`** (discipline): intent → triage → brainstorm → research → acceptance → spec → spec-panel → brooks-lint → improve → open → adr-approve → inprogress → build → lint → done
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'develop-spec', 'inputs': {}, 'intent_id': '…'})`
  1. **intent** — Capture the intent the spec serves.
     intent.capture the purpose / deliverable / acceptance — every spec serves a confirmed intent.
  2. **triage** — Triage the rough scope.
     Interview + clarify to bound what's in and out before any design — a vague scope produces a vague spec.
  3. **brainstorm** — Brainstorm the design.
     Walk develop.brainstorm — explore options, present tradeoffs, land a direction. Design before code.
  4. **research** — Research prior art + what already exists.
     codegraph_explore over the existing code AND research external prior art. Most of the design is already half-built somewhere.
  5. **acceptance** — Write the acceptance criteria.
     State the decidable acceptance checks — how you'll KNOW it's done. Acceptance is the contract the build phase satisfies.
  6. **spec** — Write the spec into Plan/draft/.
     develop.write_spec the design + acceptance into a Plan/draft/ spec — the why, the slices, the acceptance.
  7. **spec-panel** — Run the expert spec panel.
     Convene the panel over the draft — steelman, assumptions, premortem — and capture the findings to fold back in.
  8. **brooks-lint** — Brooks-lint for conceptual integrity.
     intent.brooks_lint — the 9th critical-thinking method: essential-vs-accidental complexity, conceptual integrity, second-system effect.
  9. **improve** — The design gate — loop until no blocker.
     Loop the improve pass until no `block` finding remains AND the owner confirms. Confirm this gate only when the design is genuinely sound, not merely written.
  10. **open** — Move to /open and extract the ADR decisions.
     workflow.move_spec to /open, then adr.extract_decisions pulls the key decisions into proposed WH(Y) Decision drafts.
  11. **adr-approve** — The ADR hinge — owner approves the decisions.
     The spec cannot advance until EVERY decision is approved (owner-only — an agent never self-approves). Confirm this gate only on the owner's approval.
  12. **inprogress** — Move to /inprogress and load the ADR hints.
     workflow.move_spec to /inprogress, then adr.hints re-loads the code + architecture hints into context as the build begins.
  13. **build** — Build it TDD, one slice at a time.
     Walk develop.tdd / plan-execute — RED → GREEN → green suite → commit → push, slice by slice. The tests are the contract.
  14. **lint** — Lint the implementation (brooks Iron Law).
     Run the review chain over the implementation — correctness first, then the Iron Law (over-engineering, duplication). Advisory: findings feed the done verification.
  15. **done** — Verify and move to /done — COMPLETED != done.
     develop.verify the acceptance, run the headless analyze.review CI gate, then workflow.move_spec to /done. Confirm this gate ONLY on green evidence — COMPLETED is not done.
