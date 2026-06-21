# Vision-Alignment Review — Spec 011 (Agentic Capabilities)

**Reviewer:** vision-alignment panel (spec-panel critique mode)
**Date:** 2026-05-27
**Spec:** `/home/user/agency/Plan/inprogress/011-agentic-capabilities/spec.md`
**Canon:** `docs/vision/CORE.md`, `docs/vision/CAPABILITY-CLUSTERS.md`

---

## Alignment verdict: NEEDS-MAJOR-REFRAME

The spec is *engineering-sound* and scrupulous about composition (it does not
re-derive `delegate`/`subagent`/`gate`, and it correctly kills the phantom
`core.py` edit). But it commits the one sin the canon is most explicit about:
**it adds two net-new top-level Capabilities (`agentic`, `pressure`) for a surface
the canon already routed to middleware, to a Lifecycle facet, and to a skill
composition.** Per `CAPABILITY-CLUSTERS.md:26-36`, the only sanctioned net-new
primitives were `delegate` (built) and `research` (a composition, *not* a
primitive). The verdict line — "Multiplying concepts would re-introduce bloat"
(`CLUSTERS:31`) — applies almost verbatim here.

The *content* of this spec mostly belongs in Agency. The *packaging* (two new
`home="lifecycle"` capabilities, each with its own ontology extension) is the
misalignment. Almost every verb has a canon-sanctioned home that is **not** a
new capability.

---

## Canon citations (load-bearing)

- **`CORE.md:16-18` (CRITICAL):** *"Cross-cutting guards (quality-score,
  **loop-detection**, compaction, `Slot`/quota) are engine middleware, **not**
  concepts."* — Loop-detection is named, in the canon, by the exact term the spec
  uses, and classified as **middleware, not a concept/capability.** A capability
  verb `agentic.detect_loop` directly contradicts this sentence.
- **`CORE.md:33-35`:** *"an agent-session is a lifecycle whose
  transitions/observers differ (a remote async agent inserts `verify`;
  `COMPLETED ≠ done`)."* — Structural checks over an agent-session
  (depth-bound, no-orphans) are **Lifecycle observation** (`check`/`watch`,
  `CORE.md:31`), already the home of `verify`. This is where `verify_invariants`
  belongs, not a new `agentic` capability.
- **`CLUSTERS:18`:** *"`gate` … a stateless precondition/quality predicate …
  recording evidence — **facet of Lifecycle.**"* — `confidence_check` and
  `spec_validate` are predicates over a phase; they are `gate` payloads, not a
  new capability.
- **`CLUSTERS:22, 36`:** *"`research` … **composition** (delegate + craft +
  gate) … to ship as a **skill template** rather than a primitive."* — The
  pressure-test (load → run-a-worker → score → gate) is structurally identical:
  a composition. By the `research` precedent it ships as a **skill**, not a
  capability.
- **`CLUSTERS:26-31`:** *"Most clusters are **facets of the four concepts**, not
  new top-level primitives … Multiplying concepts would re-introduce bloat."*
- **`CLUSTERS:54` (token-budget/loop-depth middleware, catalogue row 24):** the
  spec itself (migration row, `spec.md:254`) maps this to "assert against the
  engine's existing `MAX_DEPTH` guard … rather than adding middleware" — correct
  instinct, wrong container (it puts the assertion in a new capability instead of
  a Lifecycle `check`).

---

## Per-verb ruling: middleware / facet-of-gate / Lifecycle-observation / skill

| Spec verb | Spec home | **Canon home** | Ruling |
|---|---|---|---|
| `agentic.detect_loop` | new `agentic` cap | **engine MIDDLEWARE** | **MIDDLEWARE.** `CORE.md:17` names "loop-detection" as middleware, *not a concept.* It must not be a capability verb. The pure Jaccard signal is a middleware helper the engine runs in a future hooks layer — exactly where the spec already (correctly) defers its hook/throttle/source. Ship the *algorithm* as an internal engine util, not a discoverable verb. |
| `agentic.verify_invariants` | new `agentic` cap | **Lifecycle `check`/`watch`** | **LIFECYCLE OBSERVATION (partly redundant).** Depth-bound is already enforced by `ctx.spawn` (`capability.py:52-53`); a "quota respected" check is tautological (the spec already drops it, OQ#2). The *one* genuine invariant — no orphaned `working` children — is a Lifecycle read-projection (`check`), the same family as `delegate.join`'s state tally (`delegate.py:72-77`) and `verify`. It records a `gate.check` already, so it is a *Lifecycle observe + gate*, not a new capability. **See duplication note vs `COMPLETED ≠ done` below.** |
| `agentic.spec_validate` | new `agentic` cap | **facet of `gate` / `develop`** | **FACET.** A decidable predicate over spec text (RFC-2119 + Gherkin presence). This is precisely a `gate` payload, and `develop` already owns `spec-panel` (`CLUSTERS:13`, `develop.py`). It is a gate predicate feeding `develop`'s spec discipline — not a new capability. |
| `agentic.confidence_check` | new `agentic` cap | **facet of `gate` (Lifecycle)** | **FACET-of-gate.** `CLUSTERS:18` — a stateless precondition predicate with a go-threshold (`≥0.9`) that blocks a phase **is the definition of `gate`.** It should be a `gate`-recorded confidence predicate, not its own verb in a new capability. |
| `pressure.load_scenario` | new `pressure` cap | **skill data / `transform`** | **SKILL composition.** Pure scenario validation is the input-shaping step of the pressure-test skill template (the open `transform` set, `CLUSTERS:20`). Not a top-level capability. |
| `pressure.score_transcript` | new `pressure` cap | **skill data / `transform`** | **SKILL composition.** Pure rubric → verdict. Same as above: a `transform` step inside the pressure-test skill, recorded via `gate`. |
| `pressure.run` | new `pressure` cap (effect) | **skill = composition (delegate→worker→gate)** | **SKILL composition (the `research` precedent).** `run` = dispatch-or-take-a-transcript → score → record a gated `PressureRun`. This is *structurally `research`* (`CLUSTERS:22,36`): delegate + transform + gate, shipped as a **skill template, not a primitive.** The spec even admits the wet path is just `delegate.fan_out` + a driver. It is a composition by its own description. |

**Summary of the ruling:**
- **MIDDLEWARE (1):** `detect_loop` — canon names it middleware (`CORE.md:17`).
- **LIFECYCLE-OBSERVATION + gate (1):** `verify_invariants` — a `check` that
  records via `gate`; partly redundant with the depth guard and `verify`.
- **FACET-of-gate (2):** `confidence_check`, `spec_validate`.
- **SKILL-COMPOSITION (3):** the entire `pressure` cluster — the `research`
  precedent makes it a skill template, not a primitive.

**Net:** zero of the seven verbs justify a *new top-level capability.* The work
distributes cleanly across existing homes: engine middleware (1), `gate` (3, incl.
the gate-recorded `verify_invariants`), Lifecycle observation (1), and one
skill-template composition (`pressure` as a skill, mirroring `research`).

---

## Misalignments (specific)

1. **M1 — `agentic` capability invents a concept the canon explicitly demotes.**
   `CORE.md:17` lists loop-detection as middleware. Wrapping it (plus three
   predicates) in a `home="lifecycle"` capability is "multiplying concepts"
   (`CLUSTERS:31`). The spec acknowledges Agency has no hook layer yet defers only
   the *hook*, while still surfacing the *signal as a discoverable verb* — the verb
   is the canon violation, not the deferred hook.

2. **M2 — `pressure` capability is a composition masquerading as a primitive.**
   By `CLUSTERS:22/36`, a delegate→worker→gate flow ships as a **skill template**
   (the `research` ruling). `pressure.run`'s own design (`spec.md:98-109,
   130-131`) is delegate + score + gate. Two new node types (`Scenario`,
   `PressureRun`) and an enum are added for what should be a Lifecycle-template
   skill walking existing `delegate`/`gate` verbs.

3. **M3 — `verify_invariants` partially duplicates `COMPLETED ≠ done`/`verify`.**
   `CORE.md:33-35` makes agent-session verification (`COMPLETED ≠ done`) a
   Lifecycle observer that a remote agent *inserts* (`verify`). The depth-bound
   half is already the `ctx.spawn` backstop (`capability.py:52-53`); the
   quota half is tautological (spec drops it). The residue — "no orphaned `working`
   children" — is real but is a **Lifecycle `check`** in the `verify`/`join`
   family, not a new capability's `act`.

4. **M4 — Two ontology extensions for non-primitives.** `LoopSignal`, `Scenario`,
   `PressureRun` extend the ontology for clusters the canon does not treat as
   concepts. Skill templates and gate payloads do not need bespoke node labels;
   `Scenario`/`PressureRun` are skill-walk artefacts (reuse `Artefact`/`Gate`),
   and `LoopSignal` is a middleware emission, not a graph concept.

5. **M5 — `home="lifecycle"` is a tell, not a justification.** Both capabilities
   declare `home="lifecycle"`, conceding their work *is* Lifecycle. That is the
   canon's argument *against* them being separate capabilities: if the home is
   Lifecycle, the verbs are Lifecycle facets (`gate`/`check`/`watch`), not a new
   top-level primitive.

---

## Recommended aligned framing

Keep every piece of useful behaviour; relocate it to its canon home. Concretely:

1. **`detect_loop` → engine middleware util.** Land the pure Jaccard-shingle
   function as an internal helper (e.g. `agency/_middleware/loop.py` or a private
   module the future hooks layer imports). It is *not* a discoverable verb. This
   directly honours `CORE.md:17`. Defer the consumer (hook/throttle/source) exactly
   as the spec already does — but defer the *whole thing as middleware*, not as a
   verb-now/hook-later split.

2. **`confidence_check` + `spec_validate` → `gate` predicates (+ `develop`).**
   Express both as decidable predicates recorded through `gate.check`
   (`gate.py:28`). `spec_validate` plugs into `develop`'s `spec-panel`/`plan`
   disciplines; `confidence_check` is a go/no-go `gate` with the `≥0.9` threshold.
   No new capability, no new node types.

3. **`verify_invariants` → a Lifecycle `check` recorded via `gate`.** If a verb is
   wanted, add it to the existing **Lifecycle/`gate` surface** as a post-hoc
   structural `check` (no-orphaned-`working`-children), recording a `Gate`. Frame it
   as the auditable companion to the `ctx.spawn` depth backstop and the
   `COMPLETED ≠ done` `verify` family — *not* as a new `agentic` capability.

4. **`pressure` → a skill template (the `research` model).** Ship pressure-testing
   as a **Lifecycle-template skill** (`skills/agentic-pressure-test/`) that walks
   `delegate.fan_out` (worker) → a `transform` rubric step → `gate.check`. The pure
   `load_scenario`/`score_transcript` functions live as module helpers the skill
   calls (the open `transform` set, `CLUSTERS:20`), recorded via existing nodes
   (`Artefact`/`Gate`). This is exactly how `CLUSTERS:36` says `research` must
   ship. The doctrine cross-link to `develop.py:86-94` is preserved.

5. **Drop both new top-level capabilities and both ontology extensions.** No
   `AgenticCapability`, no `PressureCapability`, no `LoopSignal`/`Scenario`/
   `PressureRun` labels. The net-new-primitive budget per `CLUSTERS:32-36` is spent
   (`delegate` built; `research` is a composition). This spec adds *zero* new
   primitives — it adds middleware, gate predicates, a Lifecycle check, and one
   skill.

---

## Must-change list

- [ ] **MC1 (CRITICAL, `CORE.md:16-18`):** Remove `detect_loop` from any capability
      surface. Land the Jaccard algorithm as engine **middleware**; it is named
      middleware-not-a-concept in the canon. No discoverable verb.
- [ ] **MC2 (CRITICAL, `CLUSTERS:26-36`):** Delete the two new top-level
      capabilities (`AgenticCapability`, `PressureCapability`). The canon's
      net-new-primitive budget is `delegate` + `research`; this spec adds none.
- [ ] **MC3 (HIGH, `CLUSTERS:22,36`):** Reframe `pressure` as a **skill template**
      (delegate→transform→gate), the `research` precedent — not a capability.
      `load_scenario`/`score_transcript` become module-level `transform` helpers.
- [ ] **MC4 (HIGH, `CLUSTERS:18`):** Express `confidence_check` and `spec_validate`
      as **`gate` predicates** (recorded via `gate.check`), feeding `develop`'s
      disciplines — not standalone verbs in a new capability.
- [ ] **MC5 (MEDIUM, `CORE.md:31-35`):** Reframe `verify_invariants` as a Lifecycle
      `check` recorded through `gate`, scoped to the one non-redundant invariant
      (no orphaned `working` children). Note its overlap with the `ctx.spawn` depth
      guard and the `COMPLETED ≠ done` `verify` family; do not duplicate them.
- [ ] **MC6 (MEDIUM, `CLUSTERS:31`):** Drop the `LoopSignal`, `Scenario`, and
      `PressureRun` ontology extensions; reuse core `Artefact`/`Gate` for the
      skill-walk and middleware emissions.
- [ ] **MC7 (LOW):** Keep and preserve the genuinely-aligned decisions already in
      the spec: no `core.py` edit (correct — it does not exist), LLM-out-of-the-verb
      dry-run pattern, single canonical doctrine via cross-link to `develop.py:86-94`,
      and the deferral of hook/wet-path. These survive the reframe unchanged.
