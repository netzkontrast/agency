---
spec_id: "356"
slug: loop-council
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3, 8]
depends_on: ["002", "040", "271", "285", "294", "297", "353"]
parent_spec: "353"
domain: loop / delegation
wave: looper-port
---

# Spec 356 — Loop council (cross-model reviewer / judge)

> Child of Spec 353. Ports looper's **council stage** +
> `references/council-rubric.md` + §6 (model detection/selection). This is
> looper's defining wedge: **a reviewer or judge from a *different* model family
> than the host** — closing the blind spot of a model grading its own homework.
> Agency already has the convening primitives (`panel`, `persona`) and the
> cross-model dispatch primitives (`delegate`, `jules`). 356 binds them into a
> loop council.

## Why

Looper's council members each carry a role, a CLI/model, an invoke argv, a
timeout, and a scope:

```yaml
council:
  - id: reviewer-1
    role: judge            # reviewer (notes only) | judge (verdict)
    cli: claude
    model: opus-4.8-high
    invoke: ["claude", "-p"]
    timeout_sec: 600
    scope: [plan, delivery]
```

Two hard rules looper settled (v0.1 ambiguity removed):

1. **reviewer vs judge are distinct.** A *reviewer* emits notes; the host revises
   against them; it casts no verdict. A *judge* emits a **structured verdict** that
   gates progression.
2. **`revise_until_clean` requires a `verdict_source`** — a judge member or
   `human`. A gate with only reviewers (nothing can declare "clean") may use
   `fixed_passes` (apply notes N times, then proceed) but **not**
   `revise_until_clean`.

And the cultural default: **recommend a different model family than the host** and
explain why (self-review by the same family is the blind spot the council exists
to close).

Agency's pieces:
- **`panel`** (Spec 294) convenes multiple expert voices over an artefact.
- **`persona`** (Spec 297) is a named specialist reviewer.
- **`delegate`** (Spec 040) + **`jules`** (Spec 271) dispatch to other models /
  drivers, recording provenance.
- **`ctx.host`** (Spec 285) is the in-session host LLM (sampling) when the host
  role runs natively.

356 expresses a council member as **a persona bound to a model driver**, and
`convene` as a scoped `panel` over the gated artefact.

## Design

### `CouncilMember` = persona + driver + role

```python
@verb(role="effect")
def add_member(self, ctx, loop_id: str, role: str, *, model: str = "",
               cli: str = "", family: str = "", scope: list[str] | None = None,
               local: bool = False, timeout_sec: int = 600, mid: str = "") -> dict:
    """Add a council member to a loop.

    role ∈ {reviewer, judge}: a reviewer emits notes; a judge emits a verdict.
    `model`/`cli`/`family` resolve to a driver invocation (delegate/jules) via
    the registry (360). `scope` ⊆ {plan, delivery} limits which gates it serves.
    `local=True` flags a no-egress member (e.g. ollama). Returns
    {member_id, role, family, local}. chain_next: loop.recommend_council to
    check cross-family hygiene; gates (357) reference members by id.
    """
```

A member is a **persona** (Spec 297) — its review voice — bound to a **driver**
(`delegate`/`jules`, resolved by 360). `family` (anthropic / openai / google /
local) is what the cross-family rule reasons over.

### `convene` — a scoped panel that returns role-correct output

```python
@verb(role="transform")
def convene(self, ctx, loop_id: str, gate: str, artefact: str,
            members: list[str]) -> dict:
    """Convene a loop's council over a gated artefact.

    Reviewers (role=reviewer) → notes only (panel voices, no verdict).
    Judges (role=judge)       → a structured verdict {verdict, blocking_issues,
                                 confidence, notes}, parsed leniently.
    Returns {notes:[…], verdict?:{…}, member_verdicts:[…]}. The verdict is
    present only if a judge member is in `members`. chain_next: the machine
    (357) applies revise_until_clean using verdict.verdict.
    """
```

Implemented over `panel.convene` (multi-voice) + `persona` for each member's
frame. Reviewer voices append to `notes`; judge voices run the **structured
verdict prompt** and are parsed by:

```python
def parse_verdict(text: str) -> dict:
    """Looper-parity lenient parse: prefer a fenced ```json block; on any
    parse failure or a verdict not in {pass, revise}, degrade to
    {verdict:"revise", blocking_issues:[…], confidence:0.0, warning:"unparseable_judge_output"}.
    Never raises."""
```

This is looper's `parse_judge_output`, ported. The structured verdict shape
(`verdict / blocking_issues / confidence / notes`) is the contract 355 and 357
consume.

### The reviewer-only rule is enforced, not just documented

```python
@verb(role="transform")
def recommend_council(self, ctx, loop_id: str, host_family: str = "") -> dict:
    """Coach a loop's council against council-rubric.md. Returns:
      - cross_family_ok: are any members a DIFFERENT family than the host?
      - verdict_source_ok per gate: does every revise_until_clean gate name a
        judge member or 'human'? (the v0.1 ambiguity, enforced)
      - scope coverage: is every gated stage covered by ≥1 member?
    Returns {findings:[{rubric_ref, severity, message, fix}]}. A
    revise_until_clean gate with only reviewers is an ERROR finding (the
    machine, 357, refuses to open such a loop).
    """
```

The **`verdict_source` invariant** is the one hard rule: 357's `open_loop` calls
into this check and **refuses** a loop whose `revise_until_clean` gate lacks a
judge/human verdict source. Everything else (cross-family, scope) is advisory
coaching surfaced by the wizard (358).

### Cross-model = a different driver/family (not a different vendor of magic)

"Cross-model" is mechanically "the member's `family` ≠ the host's `family`." The
member's actual invocation is a **driver** (`delegate`/`jules`, Spec 040/271) —
the same dispatch substrate agency already uses, which records provenance and
honours the dispatch-decision heuristic. Looper's "codex→claude / claude→codex
bridge" is just two members with different families. Local members (`ollama`) set
`local=True` and skip egress (360).

## Acceptance (Gherkin)

```gherkin
Scenario: a reviewer emits notes, a judge emits a verdict
  Given a loop with a reviewer member and a judge member
  When I convene over a plan artefact
  Then the reviewer contributes notes with no verdict
  And the judge returns a structured verdict {verdict, blocking_issues, confidence, notes}

Scenario: an unparseable judge verdict degrades to revise
  Given a judge member whose driver returns prose, not JSON
  When I convene
  Then the verdict is revise with warning "unparseable_judge_output" and it does not raise

Scenario: revise_until_clean requires a verdict source (the reviewer-only rule)
  Given a plan gate with verdict_policy revise_until_clean and only reviewer members
  When I recommend_council
  Then it returns an ERROR finding citing council-rubric.md
  And open_loop (357) refuses to open the loop

Scenario: a reviewer-only gate may use fixed_passes
  Given a plan gate with only reviewers and verdict_policy fixed_passes
  When I recommend_council
  Then verdict_source_ok is true (no judge required for fixed_passes)

Scenario: cross-family hygiene is coached, not forced
  Given a host family "anthropic" and a single judge member also "anthropic"
  When I recommend_council with host_family anthropic
  Then cross_family_ok is false with an advisory finding to add a different family
  But the loop may still open (override recorded as provenance)

Scenario: a scoped member only serves its scope
  Given a judge member with scope [plan]
  When I convene the delivery gate
  Then that member is not consulted for delivery
```

## Done When

- [ ] `loop.add_member` records `CouncilMember` (persona + driver + role + family + scope + local).
- [ ] `loop.convene` returns role-correct output (reviewer notes / judge verdict) over `panel`+`persona`.
- [ ] `parse_verdict` ports looper's lenient JSON parse (degrade to revise + warn; never raises).
- [ ] `loop.recommend_council` enforces the `verdict_source` invariant (ERROR) and coaches cross-family + scope (advisory).
- [ ] `open_loop` (357) refuses a `revise_until_clean` gate with no verdict source.
- [ ] `council-rubric.md` ships verbatim under `data/rubrics/`.
- [ ] `tests/acceptance/test_loop_council.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 353 wave. Council members as
personas (297) bound to drivers (040/271), convened via `panel` (294);
reviewer/judge distinction + the `revise_until_clean` verdict-source invariant
enforced at `open_loop`. Lenient judge parse ported from looper. Foundation
sibling consumed by 355 (judge path), 357 (gate application), 358 (wizard), 360
(driver/egress resolution).
