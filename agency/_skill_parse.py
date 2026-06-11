"""Spec 152 Slice 1 — typed Skill/Phase parse boundary.

A single parse + validate point for skill / phase dicts so the walker
(Spec 018), SkillDoc derive (Spec 081), and graph-promotion (Spec 026)
all consume the same typed shape — no more ad-hoc `phase.get("gate")`
scattered across the codebase.

Slice 1 surface (this module):
- `Phase` / `Skill` frozen dataclasses with a `variant` discriminator
  (`"hard_gate"` / `"verb_bound"` / `"step"`).
- `parse_phase(dict) -> ParseResult[Phase]`,
  `parse_skill(dict) -> ParseResult[Skill]`.
- Typed failure codes on `Codes`: `SKILL_PARSE_INVALID`,
  `PHASE_MISSING_FIELD`, `PHASE_UNKNOWN_KIND`.
- Round-trip — `parse_clean(s).to_dict() == s` for any well-formed input.

The keyword path the walker takes today still works (ad-hoc dict reads in
`disclosure.render_phase`); Slice 2 routes those through `parse_phase`
and lights up a `_check_ad_hoc_phase_parse` grep_ast gate (Spec 151
family) so the count is monotone-decreasing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ── result envelope (Spec 059-style) ───────────────────────────────────────
@dataclass(frozen=True)
class ParseResult:
    """Typed result envelope. `ok=True` carries `value`; `ok=False`
    carries (`code`, `message`). Slice 1 stays free of generics; Slice 2
    may upgrade to `Generic[T]`."""

    ok: bool
    value: Any = None
    code: str = ""
    message: str = ""

    @classmethod
    def success(cls, value: Any) -> "ParseResult":
        return cls(ok=True, value=value)

    @classmethod
    def failure(cls, code: str, message: str) -> "ParseResult":
        return cls(ok=False, code=code, message=message)


# ── Phase variants ─────────────────────────────────────────────────────────
_KNOWN_GATES = frozenset({"hard"})
_KNOWN_VARIANTS = frozenset({"step", "hard_gate", "verb_bound"})


@dataclass(frozen=True)
class Phase:
    """Typed walkable-skill phase. `variant` discriminator drives walker
    dispatch — no more reading `phase["gate"]` at every callsite."""

    name: str
    variant: str                                                   # "step" | "hard_gate" | "verb_bound"
    produces: tuple[str, ...] = ()
    cue: str = ""
    gate: str = ""                                                 # "" | "hard"
    invoke: Optional[tuple[str, str]] = None                       # (capability, verb) for verb_bound
    reference: str = ""

    def to_dict(self) -> dict:
        """Round-trip back to the source dict shape. Keys absent on the
        source dict (because they were defaults) stay absent here so the
        round-trip invariant holds for cheap hand-written skills."""
        out: dict[str, Any] = {"name": self.name}
        if self.produces:
            out["produces"] = list(self.produces)
        if self.cue:
            out["cue"] = self.cue
        if self.gate:
            out["gate"] = self.gate
        if self.invoke is not None:
            out["invoke"] = {"capability": self.invoke[0], "verb": self.invoke[1]}
        if self.reference:
            out["reference"] = self.reference
        return out


@dataclass(frozen=True)
class Skill:
    name: str
    phases: tuple[Phase, ...] = ()

    def to_dict(self) -> dict:
        return {"name": self.name,
                "phases": [p.to_dict() for p in self.phases]}


# ── parse_phase ────────────────────────────────────────────────────────────
def parse_phase(d: dict) -> ParseResult:
    """Validate + lift a phase dict to a `Phase`. Returns
    `ParseResult.success(Phase)` or `ParseResult.failure(code, message)`."""
    from .toolresult import Codes
    if not isinstance(d, dict):
        return ParseResult.failure(Codes.PHASE_MISSING_FIELD,
                                   f"phase must be a dict, got {type(d).__name__}")
    name = d.get("name")
    if not isinstance(name, str) or not name:
        return ParseResult.failure(Codes.PHASE_MISSING_FIELD,
                                   "phase is missing required field `name`")
    gate = d.get("gate", "") or ""
    if gate and gate not in _KNOWN_GATES:
        return ParseResult.failure(
            Codes.PHASE_UNKNOWN_KIND,
            f"phase `{name}` has unknown gate {gate!r} "
            f"(documented gates: {sorted(_KNOWN_GATES)})")
    invoke_raw = d.get("invoke")
    invoke: Optional[tuple[str, str]] = None
    if invoke_raw is not None:
        if not isinstance(invoke_raw, dict):
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` invoke must be a dict")
        cap = invoke_raw.get("capability")
        verb = invoke_raw.get("verb")
        if not isinstance(cap, str) or not cap or \
           not isinstance(verb, str) or not verb:
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` invoke missing required "
                f"{'capability' if not cap else 'verb'}")
        invoke = (cap, verb)
    produces_raw = d.get("produces") or []
    if not isinstance(produces_raw, list):
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` produces must be a list, "
            f"got {type(produces_raw).__name__}")
    variant = _derive_variant(gate=gate, invoke=invoke)
    return ParseResult.success(Phase(
        name=name,
        variant=variant,
        produces=tuple(produces_raw),
        cue=d.get("cue") or "",
        gate=gate,
        invoke=invoke,
        reference=d.get("reference") or "",
    ))


def _derive_variant(*, gate: str, invoke: Optional[tuple[str, str]]) -> str:
    """The discriminator rule. `invoke` wins over `gate` when both are
    present (verb-bound phases delegate to the verb's own gate semantics)."""
    if invoke is not None:
        return "verb_bound"
    if gate == "hard":
        return "hard_gate"
    return "step"


# ── parse_skill ────────────────────────────────────────────────────────────
def parse_skill(d: dict) -> ParseResult:
    from .toolresult import Codes
    if not isinstance(d, dict):
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill must be a dict, got {type(d).__name__}")
    name = d.get("name")
    if not isinstance(name, str) or not name:
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            "skill is missing required field `name`")
    phases_raw = d.get("phases") or []
    if not isinstance(phases_raw, list):
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` phases must be a list, "
            f"got {type(phases_raw).__name__}")
    phases: list[Phase] = []
    for i, pd in enumerate(phases_raw):
        sub = parse_phase(pd)
        if not sub.ok:
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"skill `{name}` phases[{i}]: {sub.message}")
        phases.append(sub.value)
    return ParseResult.success(Skill(name=name, phases=tuple(phases)))
