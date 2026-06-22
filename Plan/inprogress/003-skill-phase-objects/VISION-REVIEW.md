# Vision Alignment Review — Spec 003 (First-Class `Skill` / `Phase` Objects)

> Reviewer: vision-alignment panel (spec-panel mode: critique). Canon =
> `docs/vision/CORE.md` (authoritative), `docs/vision/specs/skills-and-gates.md`,
> `docs/vision/specs/lifecycle.md`. Code = `agency/skill.py`, `agency/ontology.py`,
> `agency/engine.py`, `agency/capabilities/develop.py`.

## Verdict

**ALIGNED (strong) — proceed, with three small framing must-changes.**

Spec 003 is a *faithful internal-typing refactor*. It typifies the dict walker
without adding, removing, or renaming any of the four concepts; it preserves the
three canon-load-bearing properties of a skill (progressive disclosure, the
elicit hard-gate pause, and provenance mirroring) byte-for-byte. The few genuinely
new behaviours (contiguous-index check, single-`produces` guard on `invoke`) are
*honestly labelled as additions* (spec.md:88-94, 110-115) rather than smuggled in
under "no behaviour change" — which is itself a canon-respecting discipline. The
misalignments below are all about *wording and the trail*, not mechanism.

## Canon citations

- **CORE.md:47-54** — "a skill is a **Lifecycle template: a graph of atomic
  Capability steps + Gates**, walked step-by-step via code-mode. Each step
  discloses only the *next* instruction … the chain *is* an executable dataflow
  graph, and because every `call_tool` records an Invocation, it mirrors itself
  into the provenance graph."
- **CORE.md:56-62** — "**Gates / intent-verification / human-in-the-loop are
  `elicit` steps.** … A gate that needs a human is just an `elicit` → the
  Lifecycle pauses at `input-required`, the answer resumes it, the outcome is
  recorded as a `Gate`. 'askuser' is therefore not a special case."
- **CORE.md:30-36, lifecycle.md:55-61** — Lifecycle states are A2A-aligned
  (`submitted · working · input-required · completed · failed · canceled`); "Gates
  = `input-required` → Intent re-entry"; a hard gate must pass to `move`, an
  advisory gate never blocks.
- **CORE.md:26-28** — Capability verbs are **role-tagged** `act` / `transform` /
  `effect`.
- **CORE.md:64-80** — Schemas/Templates are "ordinary nodes in **Memory**"; skills
  are not a new concept — they are a Lifecycle template whose record lives in
  Memory.
- **skills-and-gates.md:41-45** — the elicit pause "records the outcome as a `Gate`
  node (`PASSED` or blocked). Hard gates must pass to advance; advisory gates
  surface a warning and never block."

## Alignment analysis (the three questions)

### Q1 — Does the typed `Skill`/`Phase` faithfully model the step-graph (progressive disclosure + provenance), or ossify the walker into something less aligned? → FAITHFUL.

- **Progressive disclosure preserved.** `SkillRun.current()` still returns ONLY the
  current phase (spec.md:128-134, Design `current() -> self.phases[self.i].spec()`).
  Crucially the panel endorses the **Open Q1 resolution**: `current()` returns the
  `.spec()` *dict*, and `Phase` is given **no `__getitem__`**. This is the
  *most* canon-aligned of the available choices — re-introducing stringly-typed
  subscripting on the new object would have re-created the exact "raw dict poke"
  the canon's atomic-step discipline is meant to retire. Returning a flat
  disclosure-delta dict keeps "each step discloses only the next instruction"
  (CORE.md:51-52) literally intact.
- **Provenance mirroring preserved.** The `submit()` after-image (spec.md:303-329)
  keeps the `Phase` node record and the `HAS_PHASE` / `SERVES` / `PRECEDES` edges
  unchanged, and still threads `inv_id` so an `invoke` phase's real Invocation is
  edged under the phase (skill.py:81-82). "The chain mirrors itself into the
  provenance graph" (CORE.md:53-54) is untouched. **Strengthened, not weakened:**
  by failing malformed schemas at `Engine.__init__` (spec.md:341-362) the spec
  guarantees that *only* well-formed step-graphs ever reach the provenance graph —
  a bad skill can no longer write a half-walk of `Phase` nodes before `KeyError`-ing
  three phases deep. That is more faithful to "a skill run IS provenance"
  (skill.py:15), not less.
- **No ossification.** Authoring and storage stay dicts (Open Q5, spec.md:150-155,
  331-339); the typed objects are a parse/validate boundary, never the canonical
  store. Skills remain Memory artefacts owned by the contributing capability
  (CORE.md:131-133); the engine does not promote `Skill` to a stored concept.

### Q2 — Does `Phase.gate` ("hard" → input-required) faithfully model the elicit-gate canon? → FAITHFUL in MECHANISM; one framing gap.

- The mechanism is exact: `Phase.is_gate()` is `gate == "hard"`, and `submit()`
  returns `{"status": "input-required", "phase": ..., "gate": "hard"}` on an
  unconfirmed hard gate (spec.md:223-224, 321-322). That **IS** the canon pause
  point (CORE.md:59-60, lifecycle.md:57-61): the Lifecycle pauses at
  `input-required`, a later `submit(confirmed=True)` resumes, and the phase is then
  recorded as provenance.
- **Open Q2's resolution to keep `gate: Optional[str]` constrained to `"hard"` is
  correct and well-justified** (spec.md:411-417): the live walker reads the string
  (skill.py:71), every shipped skill uses only `"hard"`, and the programmatic
  predicate-gate already exists as the separate `gate` *capability*. The research's
  `Optional[Callable[..., bool]]` would have been LESS aligned — it would have
  re-implemented inside `Phase` a concern the canon already factors out into a
  Capability. Good call.
- **The gap is vocabulary, not behaviour (see M-1).** The canon frames the hard
  gate as *an `elicit` step that records a `Gate` node*. Spec 003's prose calls it
  "the hard-gate elicit pause" (spec.md:34) but the typed model names the *string
  tag* `"hard"` and the predicate `is_gate()`, with no mention of `elicit`, `Gate`-
  node recording, or the advisory/hard distinction the canon draws
  (skills-and-gates.md:45, lifecycle.md:61). The walker today does not record a
  `Gate` node on the hard-gate path either — it returns `input-required` and only
  records the `Phase` once confirmed. That is a *pre-existing* canon gap the spec
  faithfully preserves; the spec should NAME it as preserved-but-incomplete rather
  than leave the reader thinking `is_gate()` fully models the canon's `Gate`-node
  outcome.

### Q3 — Does the typed model keep skills as Memory/Lifecycle artefacts (not a new concept) and preserve role-tags? → YES.

- Skills stay Lifecycle templates recorded in Memory: `Skill`/`Phase` are still
  recorded via `memory.record("Skill", ...)` / `memory.record("Phase", ...)`
  (spec.md:295, 323-325) against the unchanged core ontology
  (ontology.py:28-30). No new node type, no new public surface — `search` /
  `get_schema` / `execute` are untouched (spec.md:87-89, the "Code-mode IS the
  contract" guard, CORE.md:10-13). Correct.
- **Role-tags are untouched and correctly out of scope.** Role-tagging
  (`act`/`transform`/`effect`, CORE.md:26-28) lives on *Invocations*
  (ontology.py:34, 49), set by the Capability verb the `invoke` phase dispatches —
  not on the phase. `Phase` neither carries nor strips a role; it forwards
  `capability`/`verb` to `registry.invoke`, which records the role-tagged
  Invocation (skill.py:64-65, 81-82). So role-tags are preserved *by not being
  touched*, which is the right design — but the spec never states this explicitly,
  leaving a reviewer to verify it from code (see M-3, minor).

## Misalignments (all framing/trail, none mechanical)

| # | Severity | Misalignment | Canon |
|---|----------|--------------|-------|
| M-1 | Major (framing) | The typed gate model (`gate: "hard"`, `is_gate()`) is described only as a string tag / boolean. It does NOT name the canon's framing — a hard gate is an **`elicit` step that pauses at `input-required` and records a `Gate` node**, and is one of a hard/advisory pair. The walker's omission of a `Gate`-node record on the pause path is a *preserved* pre-existing gap, not a closed one. | CORE.md:56-62; skills-and-gates.md:41-45; lifecycle.md:57-61 |
| M-2 | Minor | The spec calls `Phase`/`Skill` "first-class objects" (title, spec.md:27, 74). Against the canon that risks reading as a *new concept*. They are a parse/validate **boundary** over Memory-stored dicts; the spec's own body says so (spec.md:74-80, 150-155) but the headline framing undersells the "skills stay Memory artefacts / not a new concept" canon point. | CORE.md:47-49, 64-66, 82-89 ("Dropped") |
| M-3 | Minor | Role-tags (act/transform/effect) are preserved only implicitly (via the recorded Invocation on `invoke` phases). The spec never asserts "`Phase` carries no role; the role-tag stays on the Invocation the verb records" — so the Q3 guarantee is implicit. | CORE.md:26-28; ontology.py:34,49 |
| M-4 | Note (endorse) | The two NEW invariants (contiguous `1..N` index, single-`produces` on `invoke`) are additions, honestly flagged (spec.md:88-94). They are *aligned* — the canon's "atomic Capability step" wants a deterministic position-walked graph and a verb whose single output fills one slot. No change needed; recorded so the must-change list is not misread as objecting to them. | CORE.md:47-54 |

## Recommended aligned framing

Re-cast the typed objects explicitly as **the typed boundary of a Lifecycle
step-graph**, not as a new first-class concept:

> "`Skill`/`Phase` are the typed parse/validate boundary over the dict skill
> schemas that Memory stores. A `Skill` is a Lifecycle template; each `Phase` is
> one atomic step that discloses only its own `spec()`. A `Phase` with
> `gate == "hard"` is the canon's **elicit hard-gate**: `submit()` pauses the
> Lifecycle at `input-required` (CORE.md:59-60) and resumes on `confirmed=True`.
> The role-tag (`act`/`transform`/`effect`) stays on the Invocation the phase's
> verb records, never on the `Phase`. Nothing about the four concepts, the public
> surface, or the provenance edges changes; only the dict-poking does."

Specifically, in `Phase`/`is_gate()` docstrings, cross-reference the canon: a hard
gate is an `elicit` step that pauses at `input-required`; advisory gates (canon:
warn, never block) are NOT YET modelled and are explicit future work alongside the
`Gate`-node-on-pause recording.

## Must-change list

1. **(M-1) Name the elicit-gate canon and its preserved gap.** In the `Phase` /
   `is_gate()` docstrings and the `## Why` gate sentence, state that `gate=="hard"`
   models the canon's **elicit hard-gate** (CORE.md:56-62): the Lifecycle pauses at
   `input-required` and resumes on confirm. Explicitly record that (a) the
   advisory-gate half of the canon pair (skills-and-gates.md:45) is **not** modelled
   and (b) the walker does **not** record a `Gate` node on the pause path — both are
   *preserved* pre-existing gaps, deferred to a follow-up spec, NOT introduced here.

2. **(M-2) Reframe "first-class objects" as a typed boundary.** Add one line to
   `## Why` (and soften the title's implication) stating that `Skill`/`Phase` are a
   parse/validate boundary over Memory-stored dict schemas — skills remain Lifecycle
   templates/Memory artefacts and are **not** a new concept (CORE.md:47-49, 82-89).
   The body already establishes this (spec.md:74-80); just hoist it so the headline
   cannot be read as concept-inflation.

3. **(M-3) Assert the role-tag invariant explicitly.** Add a Done-When bullet (or a
   Design note) that `Phase` carries no role tag; the `act`/`transform`/`effect`
   role stays on the Invocation that `registry.invoke` records for an `invoke`
   phase (CORE.md:26-28, ontology.py:34,49). This makes the Q3 guarantee testable
   rather than implicit, and pairs naturally with the existing "invokable phase
   still runs its real verb (with a registry)" test (spec.md:160-162).
