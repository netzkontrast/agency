---
spec_id: "003"
slug: "skill-phase-objects"
status: draft
owner: "@agency"
depends_on: ["001"]
affects:
  - agency/skill.py
  - agency/ontology.py
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

# Spec 003 — First-Class `Skill` and `Phase` Objects

## Why

The skill walker (`agency/skill.py`) is the engine's implementation of "real
micro-step skills": progressive disclosure (`current()` returns only the current
phase), strict per-phase validation (`submit()` rejects a phase missing required
outputs), the hard-gate elicit pause, and provenance (every phase recorded as a
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

This spec makes `Skill` and `Phase` first-class typed objects with **dynamic
validation at construction time**, while preserving the existing dict authoring
form (capabilities still write dict literals — the engine parses them into typed
objects once, at extension-merge time, and validates them then, not at walk time).
"Code-mode IS the contract": the walker is internal, so this is a pure
internal-typing refactor — no change to the `search`/`get_schema`/`execute`
surface.

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
      precise message when: `phases` missing/empty; a phase lacks `index`/`name`/
      `produces`; `produces` is empty; phase `index` values are not the contiguous
      sequence `1..N`; a phase has `invoke` but the named capability/verb is
      unresolvable **(see Open Q3 — whether to resolve against a registry here)**;
      `gate` is set to anything other than `"hard"` **(see Open Q2)**.
- [ ] `SkillRun.__init__` accepts EITHER a `Skill` object OR a raw `dict` (it calls
      `Skill.from_schema` on a dict) — backwards compatible with the 9 existing
      `SkillRun(e.memory, iid, e.ontology.skill("..."))` call sites in
      `tests/test_agency.py`.
- [ ] `SkillRun.current()` returns a `Phase` object's `.spec()` dict that is
      **field-identical** to today's output (`index`, `name`, `produces` list,
      `inputs` list, `gate`) — existing assertions
      (`run.current()["name"] == "gather"`, `run.current()["gate"] == "hard"`) pass
      unchanged. **(See Open Q1: return `Phase` directly vs `.spec()` dict.)**
- [ ] `SkillRun.submit()` delegates validation to `Phase.missing()` and the
      invokable/gate branches to `Phase.is_invokable()`/`Phase.is_gate()`; behaviour
      (raise on missing, `input-required` on unconfirmed hard gate, `working`/
      `completed` status, identical provenance edges) is byte-for-byte preserved.
- [ ] The engine validates every capability's skill schemas at merge time:
      `Ontology.extend` (`agency/ontology.py:104`) calls `Skill.from_schema` on each
      entry of `ext.skills` so a malformed skill in a capability fails at
      registration, not at walk time. **(See Open Q4: where validation lives —
      ontology vs engine bootstrap.)**
- [ ] All 56 existing tests still pass; new tests cover: a well-formed dict parses to
      a `Skill`; a phase missing `produces` raises `SkillSchemaError`; non-contiguous
      indices raise; `current()` output is field-identical to the pre-refactor dict;
      an invokable phase still runs its real verb; the hard gate still pauses.

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
    index: int
    name: str
    produces: tuple[str, ...]
    inputs: tuple[str, ...] = ()
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
        if gate is not None and gate != "hard":          # Open Q2
            raise SkillSchemaError(f"phase {d['name']!r}: unknown gate {gate!r} (only 'hard')")
        inv = PhaseInvoke.from_dict(d["invoke"]) if "invoke" in d else None
        return cls(index=int(d["index"]), name=d["name"], produces=produces,
                   inputs=tuple(d.get("inputs", ())), gate=gate, invoke=inv)

    def is_gate(self) -> bool:
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
        raw = schema.get("phases")
        if not raw:
            raise SkillSchemaError(f"skill {schema.get('name')!r} has no phases")
        phases = tuple(Phase.from_dict(p) for p in raw)
        expected = list(range(1, len(phases) + 1))           # contiguous 1..N
        if [p.index for p in phases] != expected:
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

### `agency/ontology.py` — validate skills at merge time

```python
# in Ontology.extend, replacing the bare assignment in the skills loop (line ~114):
from .skill import Skill, SkillSchemaError          # local import avoids a cycle
for name, sk in ext.skills.items():
    if name in self.skills:
        raise ValueError(f"{owner!r}: skill {name!r} already defined")
    try:
        Skill.from_schema(sk)                        # fail at registration, not at walk
    except SkillSchemaError as e:
        raise ValueError(f"{owner!r}: skill {name!r} is malformed: {e}") from e
    self.skills[name] = sk                            # keep storing the dict (Open Q5)
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
  - `agency/ontology.py` — `Ontology.extend` validates each skill via
    `Skill.from_schema` (local import of `agency.skill` to avoid the import cycle;
    `skill.py` already imports `memory`, not `ontology`, so the cycle is one-way —
    confirm during implementation, see Open Q4).
  - `tests/test_agency.py` — add the new typed-object tests; existing 9 `SkillRun`
    call sites must remain green unchanged (they already pass dicts and ontology
    skills).
- **Create**: none (typed objects live in the existing `agency/skill.py`).
- **Move / Delete**: none.

## Open Questions / Needs Research

1. **`current()` return type — dict vs `Phase`.** The research wants
   `current() -> Phase` (`PROPOSAL.md:122`), but 3 existing tests subscript the
   result (`run.current()["name"]`, `["gate"]`, `["produces"]`). Options: (a) return
   `p.spec()` dict now (zero test churn, defer the typed return), (b) return a
   `Phase` and give it `__getitem__` for back-compat, (c) return `Phase` and update
   the tests. **Recommend (a) for this wave; park (c) as a follow-up.** Maintainer
   to confirm whether the typed return is in-scope here or a later spec.
2. **Is `gate` ever non-`"hard"`?** Every shipped skill uses `gate: "hard"` only.
   The research's `Phase.gate` is `Optional[Callable[..., bool]]` (a predicate), not
   a string tag. Should `Phase.gate` stay the string `"hard"` (matches the live
   walker + `Memory`/elicit semantics) or become a callable gate (bigger change,
   overlaps the `gate` capability)? **Recommend keeping the string tag**; flag the
   callable form as future work. Need maintainer ruling before widening the type.
3. **Should `Skill.from_schema` resolve `invoke` capability/verb against a live
   registry?** Validating that `{"capability": "delegate", "verb": "fan_out"}`
   actually resolves requires the registry, which is not available at
   `Ontology.extend` time (capabilities may not all be registered yet). Options:
   structural-only validation now (keys present), or a second-pass resolution check
   in the engine after all capabilities register. Needs the engine bootstrap order
   confirmed (`agency/engine.py`).
4. **Where does merge-time validation live — `Ontology.extend` or engine
   bootstrap?** Putting `Skill.from_schema` in `Ontology.extend` creates an
   `ontology → skill` import. `skill.py` imports `memory`; `memory.py` imports
   `ontology`. So `ontology → skill → memory → ontology` is a cycle. The local
   (function-scope) import in `extend` breaks it, but the cleaner alternative is to
   validate in the engine after `extend`. Maintainer to pick; affects whether
   `agency/engine.py` enters `affects:`.
5. **Store typed `Skill` or keep the dict in `Ontology.skills`?** `extend` currently
   stores the raw dict; `SkillRun` re-parses. Storing the parsed `Skill` avoids
   re-parsing but changes `Ontology.skill(name)` callers
   (`e.ontology.skill("skill-creation")` is passed straight into `SkillRun`, which
   now accepts both — so storing typed is safe). Decide for one canonical form.
6. **snake_case `produces` slots vs kebab-case artefact `kind`s.** See the Design
   note. `Phase` does not reconcile these, but spec 004 must. Is the snake/kebab
   split intentional (phase-slot namespace ≠ artefact-kind namespace) or an
   accident to be normalised? This is the same naming ambiguity flagged in 004 Open
   Q. Needs one ruling that both specs cite.

## Evidence

- `agency/skill.py:25,29,32` — `SkillRun.__init__` indexes raw `schema["phases"]`,
  `schema["name"]`, `schema["kind"]` with no validation.
- `agency/skill.py:40-46` — `current()` builds a dict by raw-indexing a phase dict.
- `agency/skill.py:48-85` — `submit()` re-reads `p["invoke"]`, `p["produces"][0]`,
  `p.get("inputs")`, `p.get("gate")` ad-hoc each call.
- `agency/ontology.py:84,114` — `OntologyExtension.skills` holds raw dict schemas;
  `Ontology.extend` stores them with a name-collision check but NO shape check.
- `research/oo-architecture/PROPOSAL.md` §3 — the `Phase`/`Skill` sketch and the
  `current() -> Phase` before/after at `agency/skill.py:40`, migration cost High.
- `agency/capabilities/develop.py:28-80` — `DEV_SKILLS`, the dict skill schemas.
- `agency/capabilities/plugin.py:134-171` — `SKILL_CREATION_SKILL`,
  `PLUGIN_DEV_SKILL`, including the `invoke`/`inputs` phases and snake_case
  `produces` slot names.
- `tests/test_agency.py:406-468` — `_WALKER_SKILL` fixture and the 9 `SkillRun`
  call sites + the assertions on `current()` shape and gate behaviour the refactor
  must preserve.
