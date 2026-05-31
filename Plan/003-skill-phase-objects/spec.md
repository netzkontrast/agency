---
spec_id: "003"
slug: "skill-phase-objects"
status: draft
owner: "@agency"
depends_on: ["001"]
affects:
  - agency/skill.py
  - agency/ontology.py
  - agency/engine.py
  - agency/capabilities/develop.py
  - agency/capabilities/plugin.py
  - tests/test_agency.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 2
domain: core
wave: 1
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting** (if present). Confidence ≥ 0.90,
> TDD Red-Green-Refactor, Evidence pasted under `## Evidence`, Self-Review answered.
> Only modify paths under `affects:`. If anything is ambiguous, open a draft PR labelled
> `[BLOCKED: clarification]` and stop — do not guess. Several decisions are parked in
> `## Open Questions / Needs Research`; get them answered before writing code.

# Spec 003 — Typed `Skill` / `Phase` Boundary over the Dict Walker

## Why

> **Framing (canon, read first).** `Skill`/`Phase` are NOT a new concept. They are
> a typed **parse/validate boundary** over the dict skill schemas that Memory
> already stores. A skill stays a **Lifecycle template** — a graph of atomic
> Capability steps + Gates (CORE.md:47-54) — recorded as ordinary Memory nodes
> (CORE.md:64-66, "Dropped" §82-89); `Ontology.skills` keeps storing dicts and
> `SkillRun` re-parses them. Each `Phase` is one atomic step that discloses only
> its own `spec()`. A `Phase` with `gate == "hard"` is the canon's **elicit
> hard-gate** (CORE.md:56-62): `submit()` pauses the Lifecycle at `input-required`
> and resumes on `confirmed=True`. The role-tag (`act`/`transform`/`effect`,
> CORE.md:26-28) stays on the Invocation the phase's verb records — never on the
> `Phase`. Nothing about the four concepts, the public surface (`search` /
> `get_schema` / `execute`), or the provenance edges changes; only the dict-poking
> does. "First-class" here means *typed at the boundary*, not *promoted to a stored
> concept*.

The skill walker (`agency/skill.py`) is the engine's implementation of "real
micro-step skills": progressive disclosure (`current()` returns only the current
phase), strict per-phase validation (`submit()` rejects a phase missing required
outputs), the elicit hard-gate pause (`gate == "hard"` → Lifecycle pauses at
`input-required`, CORE.md:56-62), and provenance (every phase recorded as a
`Phase` node edged `HAS_PHASE`/`SERVES`/`PRECEDES`). All of that logic is sound —
but it walks **raw, untyped dicts**:

- `SkillRun.__init__` (`agency/skill.py:25`) takes `schema: dict` and immediately
  reaches into `schema["phases"]`, `schema["name"]`, `schema["kind"]` with no
  validation that the schema is well-formed.
- `current()` (`agency/skill.py:40`) returns a hand-assembled dict
  (`{"index": ..., "name": ..., "produces": [...], "inputs": [...], "gate": ...}`)
  by indexing `p["index"]`, `p["produces"]`, `p.get("inputs", [])`, `p.get("gate")`
  on a raw phase dict — a typo in a capability's skill schema (`"produce"` instead
  of `"produces"`) surfaces only as a `KeyError` deep inside `submit()`, at walk
  time, not at registration time.
- `submit()` (`agency/skill.py:48`) re-reads `p["invoke"]`, `p["produces"][0]`,
  `p.get("inputs", [])` ad-hoc on every call; the "executable phase vs document
  phase" branch and the hard-gate branch are inlined string/dict pokes.

The OO-architecture research (`research/oo-architecture/PROPOSAL.md` §3 "First-Class
`Phase` / `Skill` Objects") names this exact gap and sketches the target:

```python
@dataclass
class Phase:
    name: str
    required_outputs: List[str]
    gate: Optional[Callable[..., bool]] = None
    def validate(self, context: dict) -> bool:
        return all(req in context for req in self.required_outputs)

class Skill:
    def __init__(self, name: str, phases: List[Phase]): ...
    def current(self) -> Phase: ...
```

— and flags the before/after at `agency/skill.py:40`: `current()` should return a
strong `Phase` object, not a raw dict. Migration cost is rated **High** in the
research because every skill schema (the `dict`s in `develop.py:DEV_SKILLS`,
`plugin.py:SKILL_CREATION_SKILL`/`PLUGIN_DEV_SKILL`) is authored as a dict literal
and stored in `OntologyExtension.skills` (`agency/ontology.py:84`).

This spec adds a typed `Skill`/`Phase` **parse/validate boundary** with **dynamic
validation at construction time**, while preserving the existing dict authoring
*and storage* form (capabilities still write dict literals; `Ontology.skills`
still holds raw dicts — the engine parses them into typed objects, validates them
at registration time, and `SkillRun` re-parses on construction; the typed objects
are never the canonical storage). Skills stay Lifecycle artefacts/templates owned
by the contributing capability (CORE.md:131-133) — this boundary does NOT promote
`Skill` to a new stored concept. This split — keep authoring/storage as dicts,
validate shape at the boundary — is the same model the real harness uses:
`the-agency-system/Plan/harness/design.md:286` defers the required-field contract
to a separate `test_skill_schema.py` while `dispatch_skill` (design.md:188,193)
returns the parsed frontmatter as a plain dict and callers tolerate optional
fields with `.get(...)` — which is exactly why `Phase.inputs`/`gate`/`invoke` are
`Optional` with defaults below.

"Code-mode IS the contract": the walker is internal, so this is a pure
internal-typing refactor — no change to the `search`/`get_schema`/`execute`
surface. **Two validations it adds are genuinely NEW behaviour, not preserved**
(the live walker never enforced them): the contiguous-`1..N` `index` check
(the walker walks by list position `self.i`, never reads `index` for control
flow — `agency/skill.py:44,58,84`) and the single-`produces` guard on `invoke`
phases. Both hold for every shipped skill; they are guards, but the spec labels
them as additions rather than hiding them under "no behaviour change".

## Done When

- [ ] `agency/skill.py` defines a `@dataclass(frozen=True) Phase` with typed fields
      (`index: int`, `name: str`, `produces: tuple[str, ...]`, `inputs: tuple[str, ...]`,
      `gate: Optional[str]`, `invoke: Optional[PhaseInvoke]`) and the methods
      `is_gate()`, `is_invokable()`, `missing(outputs: dict) -> list[str]`,
      `spec() -> dict` (the progressive-disclosure delta `current()` returns).
- [ ] `agency/skill.py` defines a `Skill` dataclass (`name`, `kind`, `phases:
      tuple[Phase, ...]`) with `Skill.from_schema(schema: dict) -> Skill` that
      parses + **validates** a raw dict skill schema (used to be hidden in `SkillRun`).
- [ ] `Skill.from_schema` raises `SkillSchemaError` (a new typed error) with a
      precise message when: the `phases` **key is missing** (a present-but-empty
      `[]` is a LEGAL degenerate skill — see below); a phase lacks `index`/`name`/
      `produces`; `produces` is empty; phase `index` values are not the contiguous
      sequence `1..N` **(NEW invariant — the walker walks by position, never reads
      `index`; see Open Q resolution)**; an `invoke` phase declares ≠1 `produces`
      **(NEW guard — `submit()` only fills `produces[0]`)**; `invoke` is structurally
      malformed (missing `capability`/`verb` keys — structural-only, NOT resolved
      against a registry, see Open Q3); `gate` is set to anything other than
      `"hard"` (see Open Q2, resolved: string tag).
- [ ] `Skill.from_schema` does **NOT** raise on an empty `phases` list. A skill
      with `"phases": []` parses to a `Skill` with `phases == ()` — a no-op walker
      (`done` is `True` at `i=0`). This is REQUIRED to keep
      `test_ontology_collisions_and_enum_widening` (`tests/test_agency.py:750,752`)
      green: those fixtures register `{"name": "s", "kind": "x", "phases": []}` to
      exercise the duplicate-name **collision** path in `Ontology.extend`, which
      must be reached, not pre-empted by a phases check.
- [ ] `SkillRun.__init__` accepts EITHER a `Skill` object OR a raw `dict` (it calls
      `Skill.from_schema` on a dict) — backwards compatible with the 9 existing
      `SkillRun(e.memory, iid, e.ontology.skill("..."))` call sites in
      `tests/test_agency.py`.
- [ ] `SkillRun.current()` returns a `Phase` object's `.spec()` dict that is
      **field-identical** to today's output (`index`, `name`, `produces` list,
      `inputs` list, `gate`) — the 6 subscripting assertions
      (`run.current()["name"]`/`["produces"]`/`["gate"]` at
      `tests/test_agency.py:423,429,449,453,458,465`) pass unchanged. **(Open Q1
      RESOLVED: return the `.spec()` dict; `Phase` gets NO `__getitem__` — adding
      one would re-introduce the stringly-typed access this refactor exists to kill.
      The typed `current() -> Phase` return is deferred to a follow-up spec.)**
- [ ] `SkillRun.submit()` delegates validation to `Phase.missing()` and the
      invokable/gate branches to `Phase.is_invokable()`/`Phase.is_gate()`; behaviour
      (raise on missing, `input-required` on unconfirmed hard gate, `working`/
      `completed` status, identical provenance edges) is byte-for-byte preserved.
- [ ] **`Phase` carries NO role tag (invariant).** The `act`/`transform`/`effect`
      role (CORE.md:26-28) stays on the **Invocation** that `registry.invoke`
      records for an `invoke` phase (`ontology.py:34,49`); `Phase`/`PhaseInvoke`
      only forward `capability`/`verb` and never set, read, or strip a role. A test
      asserts the invoked verb's role lands on the recorded Invocation, not on the
      `Phase` node (pairs with the "invokable phase still runs its real verb" test).
- [ ] **The elicit hard-gate is modelled, with two PRESERVED gaps named (not
      introduced here).** `gate == "hard"` faithfully models the canon's elicit
      hard-gate pause (CORE.md:56-62; `submit()` → `input-required`, resume on
      `confirmed=True`). Two halves of the canon pair are NOT modelled and are
      *preserved pre-existing gaps* deferred to a follow-up spec, NOT regressions:
      (a) the **advisory gate** (warn-and-never-block, skills-and-gates.md:45) has
      no representation — only `"hard"` is valid; (b) the walker records **no
      `Gate` node on the pause path** (skills-and-gates.md:43) — it returns
      `input-required` and records the `Phase` only once confirmed. The `Phase`
      docstrings must say so explicitly so a reader does not mistake `is_gate()`
      for a full model of the canon's `Gate`-node outcome.
- [ ] The engine validates every capability's skill schemas at **registration
      time** — but in `Engine.__init__`, AFTER the extend loop, NOT inside
      `Ontology.extend`. **(Open Q4 RESOLVED → engine bootstrap.)** `Ontology.extend`
      stays a pure dict merge (no `agency.skill` import), avoiding the real
      `ontology → skill → memory → ontology` import cycle (`memory.py:17`
      `from . import ontology`; `skill.py:21` `from .memory import Memory`).
      `Engine.__init__` iterates `self.ontology.skills` after the loop at
      `agency/engine.py:48-50` (before `Memory` is constructed at `:57`) and calls
      `Skill.from_schema` on each, raising on the first malformed skill — the natural
      "all capabilities now registered" point. Hence `agency/engine.py` is in
      `affects:`.
- [ ] `Ontology.skills` keeps storing the **raw dict** (Open Q5 RESOLVED → store
      dict): `develop.checklist` (`agency/capabilities/develop.py:122-123`) and the
      tests at `tests/test_agency.py` subscript the stored value (`sk["phases"]`,
      `p["index"]`, `p["produces"]`). The implementer must NOT convert storage to
      typed `Skill`. `SkillRun` re-parses the dict on construction (cheap; validation
      already happened at bootstrap).
- [ ] All 56 existing tests still pass; new tests cover: a well-formed dict parses to
      a `Skill`; a present-but-empty `"phases": []` parses to a valid no-op `Skill`
      (NOT a raise); a phase missing `produces` raises `SkillSchemaError`;
      non-contiguous indices raise (the NEW invariant); an `invoke` phase with ≠1
      `produces` raises; `current()` output is field-identical to the pre-refactor
      dict; an invokable phase still runs its real verb (with a registry); an
      `invoke` phase walked WITHOUT a registry degrades to a document phase; the hard
      gate still pauses; an invoked verb's `act`/`transform`/`effect` role is
      recorded on the **Invocation**, not on the `Phase` node (the role-tag
      invariant); **and the headline registration-time test — a capability /
      `OntologyExtension` carrying a malformed skill raises at `Engine(...)`
      bootstrap, not at walk time.**

## Design

### `agency/skill.py` — typed objects (NEW)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


class SkillSchemaError(ValueError):
    """A capability authored a malformed skill schema. Raised at parse/merge time
    (Skill.from_schema), never deep inside a walk — so a bad skill fails loudly at
    registration, not when an agent is three phases into it."""


@dataclass(frozen=True)
class PhaseInvoke:
    capability: str
    verb: str

    @classmethod
    def from_dict(cls, d: dict) -> "PhaseInvoke":
        if "capability" not in d or "verb" not in d:
            raise SkillSchemaError(f"invoke must have 'capability' and 'verb': {d!r}")
        return cls(capability=d["capability"], verb=d["verb"])


@dataclass(frozen=True)
class Phase:
    """One atomic Capability step in a Lifecycle-template step-graph (CORE.md:47-54).

    Carries NO role tag: the act/transform/effect role (CORE.md:26-28) lives on the
    Invocation that `registry.invoke` records for an `invoke` phase, never here.
    `Phase` is a parse/validate boundary over a stored dict — not a new concept.
    """
    index: int
    name: str
    produces: tuple[str, ...]
    inputs: tuple[str, ...] = ()
    # Canon: the elicit hard-gate (CORE.md:56-62). `gate == "hard"` => submit()
    # pauses the Lifecycle at `input-required` and resumes on confirmed=True.
    # PRESERVED PRE-EXISTING GAPS (not introduced here, deferred to a follow-up):
    #   - the advisory-gate half of the canon pair (warn-never-block,
    #     skills-and-gates.md:45) is NOT modelled — only "hard" is valid (Open Q2);
    #   - no `Gate` node is recorded on the pause path (skills-and-gates.md:43) —
    #     the walker records the `Phase` only once confirmed.
    gate: Optional[str] = None              # only "hard" today (Open Q2)
    invoke: Optional[PhaseInvoke] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Phase":
        for req in ("index", "name", "produces"):
            if req not in d:
                raise SkillSchemaError(f"phase missing required key {req!r}: {d!r}")
        produces = tuple(d["produces"])
        if not produces:
            raise SkillSchemaError(f"phase {d['name']!r} must declare at least one 'produces'")
        gate = d.get("gate")
        if gate is not None and gate != "hard":          # Open Q2 (resolved: string tag)
            raise SkillSchemaError(f"phase {d['name']!r}: unknown gate {gate!r} (only 'hard')")
        inv = PhaseInvoke.from_dict(d["invoke"]) if "invoke" in d else None
        if inv is not None and len(produces) != 1:        # NEW guard: submit() fills produces[0] only
            raise SkillSchemaError(
                f"phase {d['name']!r}: an invoke phase must declare exactly one "
                f"'produces' (got {list(produces)}) — submit() only fills produces[0]")
        return cls(index=int(d["index"]), name=d["name"], produces=produces,
                   inputs=tuple(d.get("inputs", ())), gate=gate, invoke=inv)

    def is_gate(self) -> bool:
        """True iff this is the canon's elicit HARD gate (CORE.md:56-62): submit()
        pauses the Lifecycle at `input-required`, a later submit(confirmed=True)
        resumes it. NOTE: this models only the hard half of the canon's hard/advisory
        pair, and does NOT record a `Gate` node on pause (skills-and-gates.md:43,45)
        — both are PRESERVED pre-existing gaps, deferred to a follow-up spec."""
        return self.gate == "hard"

    def is_invokable(self) -> bool:
        return self.invoke is not None

    def missing(self, outputs: dict) -> list[str]:
        """The required produces this phase has not yet satisfied (empty/None count as missing)."""
        return [f for f in self.produces if outputs.get(f) in (None, "")]

    def spec(self) -> dict:
        """Progressive-disclosure delta — field-identical to the legacy current() dict."""
        return {"index": self.index, "name": self.name, "produces": list(self.produces),
                "inputs": list(self.inputs), "gate": self.gate}


@dataclass(frozen=True)
class Skill:
    name: str
    kind: str
    phases: tuple[Phase, ...]

    @classmethod
    def from_schema(cls, schema: dict) -> "Skill":
        if "name" not in schema or "kind" not in schema:
            raise SkillSchemaError(f"skill schema needs 'name' and 'kind': {schema!r}")
        if "phases" not in schema:                           # MISSING key only — see below
            raise SkillSchemaError(f"skill {schema.get('name')!r} has no 'phases' key")
        # IMPORTANT: an empty list is LEGAL. `{"phases": []}` parses to a no-op walker
        # (done at i=0). The collision-path fixtures at tests/test_agency.py:750,752
        # register empty-phase skills; rejecting `[]` here breaks 2 of the 56 tests.
        phases = tuple(Phase.from_dict(p) for p in schema["phases"])
        expected = list(range(1, len(phases) + 1))           # contiguous 1..N (NEW invariant)
        if [p.index for p in phases] != expected:            # holds vacuously for []
            raise SkillSchemaError(
                f"skill {schema['name']!r}: phase indices "
                f"{[p.index for p in phases]} must be the contiguous sequence {expected}")
        return cls(name=schema["name"], kind=schema["kind"], phases=phases)

    def phase_at(self, i: int) -> Phase:
        return self.phases[i]
```

### `agency/skill.py` — `SkillRun` BEFORE / AFTER

**Before** (`agency/skill.py:25-46`):

```python
class SkillRun:
    def __init__(self, memory, intent_id, schema: dict, registry=None):
        self.schema = schema
        self.phases = schema["phases"]            # raw list of dicts
        ...
        self.skill_id = memory.record("Skill", {"name": schema["name"], "kind": schema["kind"]})

    def current(self) -> Optional[dict]:
        if self.done:
            return None
        p = self.phases[self.i]                   # raw dict
        return {"index": p["index"], "name": p["name"], "produces": list(p["produces"]),
                "inputs": list(p.get("inputs", [])), "gate": p.get("gate")}
```

**After**:

```python
class SkillRun:
    def __init__(self, memory, intent_id, skill, registry=None):
        # accept either a typed Skill OR a raw dict (parsed + validated here)
        self.skill: Skill = skill if isinstance(skill, Skill) else Skill.from_schema(skill)
        self.phases = self.skill.phases           # tuple[Phase, ...]
        ...
        self.skill_id = memory.record("Skill", {"name": self.skill.name, "kind": self.skill.kind})

    def current(self) -> Optional[dict]:
        if self.done:
            return None
        return self.phases[self.i].spec()         # Open Q1: dict (compat) vs Phase
```

**`submit()` after** — the validation/branch logic delegates to `Phase`:

```python
def submit(self, outputs=None, confirmed=False) -> dict:
    if self.done:
        raise RuntimeError("skill run already complete")
    p: Phase = self.phases[self.i]
    outputs = dict(outputs or {})
    inv_id = None
    if p.is_invokable() and self.registry is not None:
        args = {k: outputs[k] for k in p.inputs if k in outputs}
        # registry.invoke records the role-tagged Invocation (act/transform/effect,
        # CORE.md:26-28). The role lives on that Invocation — NOT on the Phase.
        result, inv_id = self.registry.invoke(
            self.memory, self.intent_id, p.invoke.capability, p.invoke.verb, **args)
        val = result.get("result", result) if isinstance(result, dict) else result
        outputs[p.produces[0]] = val
    missing = p.missing(outputs)
    if missing:
        raise ValueError(f"phase {p.name!r} missing required outputs: {missing}")
    if p.is_gate() and not confirmed:
        return {"status": "input-required", "phase": p.name, "gate": "hard"}
    phase_id = self.memory.record("Phase", {
        "skill": self.skill.name, "index": p.index, "name": p.name,
        "produces": ",".join(p.produces)})
    # ... HAS_PHASE / SERVES / PRECEDES edges unchanged ...
    self.i += 1
    return {"status": "completed" if self.done else "working", "phase": p.name}
```

### `agency/ontology.py` — UNCHANGED (no `agency.skill` import)

`Ontology.extend` stays a pure dict merge. The skills loop keeps its existing
name-collision check and stores the **raw dict** verbatim (Open Q5 RESOLVED → store
dict): `develop.checklist` (`agency/capabilities/develop.py:122-123`) and several
tests subscript `Ontology.skills[name]["phases"]`, so the stored value MUST remain
a dict. Adding `from .skill import Skill` here would also create the real
`ontology → skill → memory → ontology` import cycle (`memory.py:17`,
`skill.py:21`). Validation does NOT live here.

### `agency/engine.py` — validate skills at registration time (Open Q4 RESOLVED)

Validation lives in `Engine.__init__`, AFTER the extend loop and BEFORE `Memory`
is built — the natural "all capabilities now registered" point, with no import
cycle (top-level `from .skill import Skill, SkillSchemaError` in `engine.py` is
clean: `engine.py` already imports `memory`, `ontology`, capabilities).

```python
# agency/engine.py, in Engine.__init__, right after the extend loop (currently :48-50):
for cap in list(discover()) + list(extra_capabilities or []):
    self.registry.register(cap)
    self.ontology.extend(cap.ontology, cap.name)
# NEW: every registered skill is well-formed — fail at bootstrap, not at walk time.
for name, sk in self.ontology.skills.items():
    try:
        Skill.from_schema(sk)
    except SkillSchemaError as e:
        raise ValueError(f"capability skill {name!r} is malformed: {e}") from e
self.registry.ontology = self.ontology
...
self.memory = Memory(path, ont=self.ontology)
```

**Note on a real authoring inconsistency this surfaces (cite for the maintainer):**
the `produces` slot names in the skill schemas are snake_case
(`skill_md`, `command_md`, `user_confirmed`, `rationalization_table`, `red_flags`)
while the artefact `kind` literals the same verbs record are kebab-case
(`skill-md`, `command-md`). `produces` slots are *phase output names*, not artefact
kinds — but the catalogue in spec 004 conflates them. `Phase` does NOT need to
reconcile this (it only checks presence of the named slot in `outputs`), but the
discrepancy is load-bearing for spec 004 and is flagged there. This spec must not
silently "fix" the names. **(See Open Q6.)**

## Files

- **Modify**:
  - `agency/skill.py` — add `SkillSchemaError`, `PhaseInvoke`, `Phase`, `Skill`;
    rewrite `SkillRun.__init__`/`current()`/`submit()` to use them. Keep the module
    docstring's contract description accurate.
  - `agency/engine.py` — `Engine.__init__` validates each registered skill via
    `Skill.from_schema` after the extend loop, before `Memory` is built (top-level
    import of `agency.skill`; no cycle — see Design). This is where Open Q4 lands.
  - `agency/ontology.py` — **UNCHANGED behaviour**: `Ontology.extend` keeps storing
    the raw dict and its name-collision check. Do NOT import `agency.skill` here and
    do NOT validate here (avoids the import cycle; the empty-`[]` collision fixtures
    at `tests/test_agency.py:750,752` must still reach the collision raise).
  - `agency/capabilities/develop.py` — listed in `affects:` because it is the
    **10th raw-dict consumer** (`develop.py:122-123` subscripts `sk["phases"]`,
    `p["index"]`, `p["produces"]`, `p.get("gate")`). It is left FUNCTIONALLY
    unchanged precisely BECAUSE `Ontology.skills` keeps storing dicts; the spec names
    it so the implementer does not convert storage to typed `Skill` and break
    `checklist` + `test_checklist_returns_steps_and_handles_unknown`.
  - `tests/test_agency.py` — add the new typed-object + registration-time tests;
    existing 9 `SkillRun` call sites must remain green unchanged (they already pass
    dicts and ontology skills).
- **Create**: none (typed objects live in the existing `agency/skill.py`).
- **Move / Delete**: none.

## Open Questions / Needs Research

The spec-panel review (`REVIEW.md`) resolved Q1–Q5; their resolutions are now
baked into Done-When/Design above and recorded here for the trail. Only Q6 stays
open (and it is correctly out of scope for 003 — a Spec 004 decision).

1. **`current()` return type — dict vs `Phase`. — RESOLVED (dict).** Return
   `p.spec()` dict. The 6 subscripting assertions
   (`tests/test_agency.py:423,429,449,453,458,465`) stay green with zero churn.
   `Phase` gets **no** `__getitem__` (rejected: it would re-introduce the
   stringly-typed access this refactor kills). The typed `current() -> Phase`
   return the research wants (`PROPOSAL.md:122`) is deferred to a follow-up spec.
2. **Is `gate` ever non-`"hard"`? — RESOLVED (string tag `"hard"`).** Every shipped
   skill (`develop.py`, `plugin.py`, `examples/music.py`) uses only `gate: "hard"`,
   and the live walker reads it as a string (`agency/skill.py:71`). The research's
   `Optional[Callable[..., bool]]` predicate has no prior-art support in the walker
   or harness; the programmatic predicate gate already exists as the separate `gate`
   **capability**. So `Phase.gate: Optional[str]` constrained to `"hard"` is the
   faithful model. The callable form is explicit future work. **Canon trail:**
   `gate == "hard"` is the elicit hard-gate (CORE.md:56-62). Two halves of the canon
   pair stay UNMODELLED as *preserved* pre-existing gaps deferred to a follow-up: the
   **advisory gate** (warn-never-block, skills-and-gates.md:45) and recording a
   **`Gate` node on the pause path** (skills-and-gates.md:43). Neither is introduced
   or regressed here — the walker already behaved this way.
3. **Resolve `invoke` against a live registry? — RESOLVED (structural-only).** The
   registry is not populated when validation runs (capabilities register in a loop;
   order is not guaranteed). Validate structure only: `capability`/`verb` keys
   present and exactly one `produces`. A registry-resolution second pass (now
   feasible since validation runs in `Engine.__init__` after all caps register) is a
   separate spec.
4. **Where does registration-time validation live? — RESOLVED (engine bootstrap).**
   In `Engine.__init__` after the extend loop, NOT in `Ontology.extend`. This avoids
   the real `ontology → skill → memory → ontology` import cycle with no local import,
   and is the natural "all capabilities registered" point. `agency/engine.py` is now
   in `affects:`.
5. **Store typed `Skill` or the dict in `Ontology.skills`? — RESOLVED (store
   dict).** Keep the raw dict. `develop.checklist` (`develop.py:122-123`) and tests
   (`sk["phases"]`) subscript the stored value; storing typed `Skill` breaks them.
   `SkillRun` re-parses on construction (cheap — validation already happened at
   bootstrap).
6. **snake_case `produces` slots vs kebab-case artefact `kind`s. — STILL OPEN (not
   blocking 003).** See the Design note. `Phase` does not reconcile these (it only
   checks slot presence, never artefact kind), so this is genuinely a Spec 004
   decision. Is the snake/kebab split intentional (phase-slot namespace ≠
   artefact-kind namespace) or an accident to be normalised? Needs one ruling that
   both specs cite. This spec must NOT silently normalise the names.

## Evidence

- `agency/skill.py:25,29,32` — `SkillRun.__init__` indexes raw `schema["phases"]`,
  `schema["name"]`, `schema["kind"]` with no validation.
- `agency/skill.py:40-46` — `current()` builds a dict by raw-indexing a phase dict.
- `agency/skill.py:48-85` — `submit()` re-reads `p["invoke"]`, `p["produces"][0]`,
  `p.get("inputs")`, `p.get("gate")` ad-hoc each call.
- `agency/ontology.py:84,114-117` — `OntologyExtension.skills` holds raw dict
  schemas; `Ontology.extend` stores them with a name-collision check but NO shape
  check. This stays as-is (validation moves to the engine).
- `agency/engine.py:48-50,57` — the extend loop, then `Memory(...)`. The new
  `Skill.from_schema` validation pass goes between them (Q4).
- `agency/capabilities/develop.py:122-123` — `checklist` subscripts `sk["phases"]`,
  `p["index"]`, `p["produces"]`, `p.get("gate")` over the stored dict: the **10th
  raw-dict consumer**, the reason `Ontology.skills` must keep storing dicts.
- `research/oo-architecture/PROPOSAL.md` §3 — the `Phase`/`Skill` sketch and the
  `current() -> Phase` before/after at `agency/skill.py:40`, migration cost High.
- `the-agency-system/Plan/harness/design.md:188,193,286` — prior art: `dispatch_skill`
  returns the parsed frontmatter as a dict; callers use `.get(...)`; a separate
  `test_skill_schema.py` owns the required-field contract. Same split this spec makes.
- `agency/capabilities/develop.py:28-80` — `DEV_SKILLS`, the dict skill schemas
  (all indices 1..N; the `review` `dispatch` phase is the one `invoke` phase, with
  exactly one `produces` `["findings"]`).
- `agency/capabilities/plugin.py:134-171` — `SKILL_CREATION_SKILL`,
  `PLUGIN_DEV_SKILL`, including the `invoke`/`inputs` phases (each one `produces`)
  and snake_case `produces` slot names.
- `tests/test_agency.py:406-468` — `_WALKER_SKILL` fixture and the 9 `SkillRun`
  call sites + the 6 `current()`-subscript / gate assertions the refactor preserves.
- `tests/test_agency.py:750,752` — `test_ontology_collisions_and_enum_widening`
  registers `{"name": "s", "kind": "x", "phases": []}` twice to test the
  duplicate-name collision; the BLOCKER is that `from_schema` must NOT reject the
  empty `phases` list, or these break before the collision raise is reached.

## Followup — Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Not started

### Done
- Nothing from this spec is implemented. `agency/skill.py` has no `SkillSchemaError`, `PhaseInvoke`, `Phase`, or `Skill` classes. `SkillRun.__init__` still takes `schema: dict` and directly indexes `schema["phases"]` (`skill.py:25,29`). `SkillRun.current()` returns a hand-assembled dict by raw-indexing phase dicts (`skill.py:40-46`). No registration-time validation exists in `Engine.__init__`.

### Still to implement
- `SkillSchemaError(ValueError)` typed error in `agency/skill.py`.
- `@dataclass(frozen=True) PhaseInvoke(capability, verb)` with `from_dict`.
- `@dataclass(frozen=True) Phase(index, name, produces, inputs, gate, invoke)` with `from_dict`, `is_gate()`, `is_invokable()`, `missing()`, `spec()`.
- `@dataclass(frozen=True) Skill(name, kind, phases)` with `from_schema()` validation (contiguous-index check, invoke-single-produces guard, structural invoke validation, empty-phases-ok).
- `SkillRun.__init__` accepting `Skill | dict`.
- `SkillRun.current()` returning `phase.spec()` dict (field-identical output).
- `SkillRun.submit()` delegating to `Phase.missing()`, `Phase.is_invokable()`, `Phase.is_gate()`.
- `Engine.__init__` validates all registered skills via `Skill.from_schema` after the extend loop.
- Tests: registration-time malformed-skill raise, contiguous-index guard, invoke-≠1-produces guard, empty-phases no-raise, role-tag-on-Invocation (not on Phase).

### Refinement needed (given later specs)
- Spec 004 (`template-schema-coverage`) references the snake_case `produces` slot vs kebab-case artefact-kind discrepancy (Open Q6 of Spec 003). This is unresolved and load-bearing for both specs. Coordinate before implementing either.
- Plan/000-overview.md:56 places Spec 003 in the Wave-1 backlog; no active revival. Spec 016 (`capability-authoring-doctrine`) will define folder-per-capability form, which may affect where skill schemas live — review before implementing 003.

### Evidence
- code: `agency/skill.py:24-85` (SkillRun walks raw dicts, no typed Phase/Skill); `agency/ontology.py:84,114-117` (stores raw dicts, no shape check); `agency/engine.py:48-57` (extend loop, no Skill.from_schema call)
- tests: none covering typed Phase/Skill objects or registration-time validation
- commits/notes: frontmatter `status: draft`; Plan/000-overview.md:56 lists in Wave-1 backlog.
