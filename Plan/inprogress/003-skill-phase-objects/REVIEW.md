# Spec-Panel Review — Spec 003: First-Class `Skill` and `Phase` Objects

Reviewers convened (spec-panel mode): **API-Compatibility** (back-compat of the 9
call sites), **Domain-Modeler** (Phase/gate semantics vs harness prior art),
**Validation-Architect** (registration-time validation soundness), **Test
Engineer** (the 56-test green guarantee). Verdict is a panel synthesis grounded in
the actual source, cited `path:line`.

---

## Verdict

**APPROVE WITH MUST-FIX (changes required before code).** The typing model is
sound and the `current()`/`submit()` rewrites are byte-faithful — but the spec as
written **breaks two of the 56 tests it promises to keep green**, because its
registration-time validation rejects empty-phase skills that `tests/test_agency.py`
deliberately registers. That contradiction (Done-When line 115 "All 56 existing
tests still pass" vs the `from_schema` contract in Done-When line 89 / Design
line 199) is a blocking defect, not a nuance. Fix the empty-phases handling and the
spec is ready.

The design is otherwise faithful: `Phase.spec()` (spec.md:182-185) reproduces the
legacy `current()` dict (`agency/skill.py:44-46`) field-for-field, and the
`submit()` rewrite (spec.md:253-275) preserves the invoke→missing→gate→record
ordering and all four provenance edges from `agency/skill.py:58-85`.

---

## Source-Grounded Corrections (path:line)

1. **BLOCKER — empty `phases` is a legal, tested input; `from_schema` must not
   reject it.** Spec Design `Skill.from_schema` does `raw = schema.get("phases"); if
   not raw: raise SkillSchemaError("...has no phases")` (spec.md:198-200), and
   Done-When line 92 lists "`phases` missing/empty" as a raise condition. But
   `tests/test_agency.py:750` and `:752` register a skill with `"phases": []` to
   exercise the **duplicate-name collision** path in `Ontology.extend`:
   ```python
   o.extend(OntologyExtension(skills={"s": {"name": "s", "kind": "x", "phases": []}}), "a")
   ```
   The spec also wires `Skill.from_schema` into `Ontology.extend` (Done-When
   line 110-114, Design spec.md:283-290). So with the spec as written, `extend`
   raises `SkillSchemaError("skill 's' has no phases")` **before** reaching the
   collision check at `agency/ontology.py:115` — `test_ontology_collisions_and_enum_widening`
   fails on the first `extend`, not the second. **Two tests break.** Done-When line
   115 ("All 56 existing tests still pass") is therefore unsatisfiable as specified.
   Fix: either (a) allow empty `phases` (validate shape of each phase, but treat
   `[]` as a degenerate-but-valid skill), or (b) change those two fixtures — but (b)
   modifies test intent and is out of `affects:` scope justification, so (a) is the
   correct fix. Recommend: drop "empty" from the raise condition; only raise on
   *missing* `phases` key. An empty phase list is a no-op walker (`done` is True at
   `i=0`), which is harmless.

2. **Contiguity check is stricter than the live engine and unproven against
   shipped skills.** Done-When line 92 and Design spec.md:202-206 require phase
   `index` to be exactly `1..N`. Today's walker (`agency/skill.py`) never reads
   `index` for control flow — it walks by list position `self.i` (`:44`, `:58`,
   `:84`) and only *records* `index` into the `Phase` node (`:74`). So contiguity is
   a NEW invariant, not preserved behaviour. It happens to hold for every shipped
   skill (`develop.py:28-80` 1..N, `plugin.py:134-171` 1..5, `examples/music.py:25-42`
   1..7), so it will not break existing tests — but it is a behaviour *addition*
   the "pure internal-typing refactor, no change to behaviour" framing (spec.md:78-79)
   understates. Keep it (it is a good guard), but the spec should explicitly label
   it a NEW validation, and add the negative test it already promises (Done-When
   line 116 "non-contiguous indices raise") — that test does not exist yet.

3. **`current()` return type: dict is correct, and the spec's own recommendation
   is right.** Three assertions subscript the result:
   `tests/test_agency.py:423` (`["name"]`, `["produces"]`), `:429`/`:465`/`:553`/`:667`/`:821`
   (`["gate"]`). `examples`/`develop.checklist` do not call `current()`. Returning
   `Phase.spec()` (spec.md:247) keeps all of these green with zero churn. Open Q1
   option (a) is the correct call. **Do NOT add `__getitem__` to `Phase` (option
   b)** — it re-introduces the stringly-typed access this refactor exists to kill,
   for a return value that is already a dict. See recommendation below.

4. **`develop.checklist` is a 10th raw-dict consumer the spec's Evidence omits —
   but it is correctly left alone.** `agency/capabilities/develop.py:122-123` does
   `p["index"], p["name"], p["produces"], p.get("gate")` over `sk["phases"]`,
   reading the same raw `DEV_SKILLS` dicts. The spec only enumerates "9 `SkillRun`
   call sites" (Done-When line 99, Evidence spec.md:373-376). Because Open Q5's
   recommendation keeps the **raw dict** in `Ontology.skills` (spec.md:290,
   spec.md:348-352), `checklist` keeps working unchanged — which is the right
   outcome. But the spec should name this consumer so the implementer does not
   "helpfully" convert `Ontology.skills` to typed `Skill` objects (Open Q5 option),
   which **would** break `checklist`'s subscripting and `test_develop_capability_ships_walkable_dev_skills`
   (`:659`) + `test_checklist_returns_steps_and_handles_unknown` (`:704-711`). Pin
   Open Q5 to "store the dict" and cite this consumer as the reason.

5. **Import-cycle claim is accurate.** Verified: `agency/memory.py:17`
   `from . import ontology`; `agency/skill.py:21` `from .memory import Memory`. So
   `ontology → skill → memory → ontology` is a real cycle (Open Q4, spec.md:344-347).
   The function-scope import inside `extend` (spec.md:282) breaks it correctly. The
   alternative — validating in `Engine.__init__` after the `extend` loop
   (`agency/engine.py:48-50`) — is cleaner and avoids the cycle entirely without a
   local import. Both are sound; see Open-Q triage.

6. **`Phase.missing()` is byte-faithful.** `agency/skill.py:68`
   `[f for f in p["produces"] if outputs.get(f) in (None, "")]` ≡ spec.md:178-180.
   Identical empty/None semantics. Good.

7. **Provenance `produces` join preserved.** `agency/skill.py:75`
   `",".join(p["produces"])` over a list ≡ spec.md:271-272 over a tuple — `join`
   is sequence-agnostic, so the recorded `Phase.produces` string is identical. Good.

---

## Missing Depth

- **No test for the `Ontology.extend` validation path itself.** Done-When line 110
  adds `Skill.from_schema` to `extend`, but the only new tests listed (line 115-118)
  exercise `Skill.from_schema` *directly*. There is no test that a malformed skill
  *in a capability* fails at `Engine(...)` bootstrap / `extend` time. That is the
  headline value of the spec ("fail at registration, not at walk time",
  spec.md:74-76) and it is untested. Add: a capability/extension with a bad skill
  raises at `extend`.

- **`invoke.produces[0]` single-slot assumption is undocumented.** `submit()`
  writes the verb result to `p.produces[0]` only (`agency/skill.py:67`,
  spec.md:264). Every invoke phase happens to declare exactly one `produces`
  (`plugin.py:140`/`:144`/`:157-167`, `develop.py:67` `["findings"]`). The spec
  preserves this but never states the latent invariant: an invoke phase with
  multiple `produces` would leave slots `[1:]` unsatisfied → the `missing()` check
  raises. Worth a `SkillSchemaError` guard (invoke phase must declare exactly one
  `produces`) or at least a documented note. Currently silent.

- **`registry=None` degrade path for invoke phases is untested in the new tests.**
  The module docstring (`agency/skill.py:50-55`) promises an invoke phase "degrades
  to a plain document phase" without a registry, and `submit()` only invokes when
  `self.registry is not None` (`:61`, spec.md:259). The new test list (line 116)
  covers "an invokable phase still runs its real verb" but not the no-registry
  degrade. `test_develop_capability_ships_walkable_dev_skills` (`:662`, no registry)
  walks `tdd` which has no invoke phases — so the degrade of an *invoke* phase is
  unexercised. Minor, but it is load-bearing behaviour the refactor must not drop.

- **Faithfulness to harness prior art — partially addressed, should be cited.** The
  real system (`the-agency-system/Plan/harness/design.md:188,286,193`) models a
  parsed skill as a **dict** (`dispatch_skill` returns the full parsed frontmatter
  dict; callers use `frontmatter.get(...)`, tolerating optional fields) and defers a
  *required-field contract* to a separate `test_skill_schema.py` (design.md:286).
  That is the same split this spec makes: keep authoring/storage as dicts, validate
  shape separately. The spec's choice to keep dict storage (Open Q5) and validate at
  the boundary is **consistent with the harness**, and the harness's "tolerate
  optional fields with `.get()`" is exactly why `Phase.inputs`/`gate`/`invoke` are
  `Optional` with defaults (spec.md:153-155). This faithfulness is real but
  unstated; cite design.md:286 in the Why.

- **`gate` callable form vs string — prior art confirms the string is right.** The
  harness's only first-class gate semantics are the A2A lifecycle states
  (`agency/ontology.py:35-38` `LIFECYCLE_STATES` incl. `input-required`) and the
  string `gate: "hard"` tag the walker reads (`agency/skill.py:71`). The
  research's `Optional[Callable]` predicate (spec.md:332-333) has NO prior-art
  support in the live walker or the harness; the *programmatic* predicate gate
  already exists as the separate `gate` **capability** (CLAUDE.md table). So
  `Phase.gate: Optional[str]` constrained to `"hard"` (spec.md:154,166-167,172-173)
  is the faithful model. Open Q2's recommendation is correct.

---

## Open-Questions Triage

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | `current()` → dict vs `Phase` | **RESOLVED** | Return `Phase.spec()` dict (option a). Faithful to 6 subscripting assertions; defer typed return to a follow-up. Reject `__getitem__` (option b). |
| Q2 | Is `gate` ever non-`"hard"`? | **RESOLVED** | Keep the string tag `"hard"`. No shipped skill (`develop.py`, `plugin.py`, `music.py`) uses anything else; the callable gate is the `gate` capability's job. Predicate form = explicit future work. |
| Q3 | `from_schema` resolve `invoke` against a registry? | **RESOLVED (structural-only)** | Registry is not populated at `extend` time (`engine.py:48-50` registers and extends in the same loop, order non-deterministic across capabilities). Validate structure only (keys present, exactly one `produces` — see Missing Depth). A registry-resolution second pass is a separate spec. |
| Q4 | Validation in `Ontology.extend` vs engine bootstrap | **RESOLVED → engine bootstrap preferred** | Both work; the cycle is real (correction 5). Prefer validating in `Engine.__init__` immediately after the `extend` loop (`engine.py:50`): no local import, no cycle, and it is the natural "all capabilities now registered" point — also enabling a future Q3 resolution pass. If kept in `extend`, the function-scope import is mandatory. **This decides whether `agency/engine.py` enters `affects:` — currently it is NOT listed (spec.md:8-12); if bootstrap is chosen, add it.** |
| Q5 | Store typed `Skill` or dict in `Ontology.skills`? | **RESOLVED → store dict** | Keep the raw dict (spec.md:290). `develop.checklist` (`develop.py:122-123`) and `test_*` (`:807` `sk["phases"]`, `:679` `schema["phases"]`) subscript the stored value. Storing typed `Skill` breaks them. `SkillRun` re-parses on construction — cheap, and the validation already happened at `extend`. |
| Q6 | snake_case `produces` vs kebab-case artefact `kind` | **NOT BLOCKING for 003** | Correctly out of scope (`Phase` checks slot presence only, never artefact kind). Genuinely a Spec 004 decision. Leave the flag; do not normalise here. |

**Blocking before code:** Q4 (decide the validation site, and amend `affects:`
accordingly). All others are resolved with the recommendations above.

---

## Must-Fix List

1. **[BLOCKER] Do not reject empty `phases`.** Remove "empty" from the
   `from_schema` raise condition (Done-When line 92, Design spec.md:199-200). Raise
   only when the `phases` key is *missing*. An empty list is a valid degenerate
   skill. This is what keeps `test_ontology_collisions_and_enum_widening`
   (`tests/test_agency.py:750-752`) green — without it, 2 of 56 tests fail and the
   spec's central promise (Done-When line 115) is false. (Correction 1.)

2. **[BLOCKER] Decide Q4 and reconcile `affects:`.** Pick engine-bootstrap
   validation (recommended) over `Ontology.extend`, OR commit to the function-scope
   import in `extend`. If bootstrap, add `agency/engine.py` to `affects:`
   (spec.md:7-12). Ship the validation-at-registration test that proves a malformed
   capability skill fails at `Engine(...)` — currently missing. (Correction 5,
   Missing Depth #1, Q4.)

3. **[REQUIRED] Pin Q5 to "store the dict" in the spec body and name the
   `develop.checklist` consumer.** State explicitly that `Ontology.skills` keeps raw
   dicts and that `develop.py:122-123` subscripts them, so the implementer does not
   convert storage to typed `Skill` and silently break `checklist` +
   `test_checklist_returns_steps_and_handles_unknown` (`:704-711`). (Correction 4.)

4. **[REQUIRED] Label contiguity as a NEW invariant and add the negative test.**
   The walker never used `index` for control flow (`agency/skill.py:44,58,84`);
   contiguity `1..N` is an addition. Keep it, but drop the "no behaviour change"
   framing for it and ship the promised non-contiguous-raises test. (Correction 2.)

5. **[SHOULD] Guard the invoke single-`produces` invariant.** Add a
   `SkillSchemaError` when an `invoke` phase declares ≠1 `produces`, since `submit()`
   only fills `produces[0]` (`agency/skill.py:67`, spec.md:264). Today silent;
   tomorrow a foot-gun. (Missing Depth #2.)

6. **[SHOULD] Add the no-registry invoke-degrade test.** Prove an `invoke` phase
   walked without a `registry` degrades to a document phase (docstring promise,
   `agency/skill.py:50-55`). Not covered by the new test list. (Missing Depth #3.)

7. **[NICE] Cite harness prior art** (`the-agency-system/Plan/harness/design.md:286`)
   in the Why — the dict-storage + separate-shape-validation split this spec makes
   is exactly the harness's `dispatch_skill` model, strengthening the faithfulness
   argument. (Missing Depth #4.)
