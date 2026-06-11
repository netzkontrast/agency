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

Live-skill compatibility (Codex review on PR #127):
- `gate` accepts `"hard"` / `"soft"` / `"computed"` (the gates the live
  registry already uses; see `agency/capabilities/music/ontology.py`,
  `agency/capabilities/subagent/_main.py`, `agency/capabilities/skills.py`).
- Top-level `kind` (e.g. `"usage"`, `"conceptualizer"`, `"gate"`,
  `"workflow"`) is preserved on `Skill`; the round-trip emits it.
- Phase-level optional fields the live registry uses — `index`, `verbs`,
  `gate_verb` — are first-class fields on `Phase` (preserved through
  the round trip; `derive_usage_skill()` emits them; `disclosure.render_phase`
  reads them).
- Strict validation — non-list `phases`, non-list `produces`, non-string
  `cue`/`reference`, non-string `produces` element values all fail
  with typed Codes rather than slipping past `or []` truthy coercion.

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


# Live-tree gate vocabulary. Sourced from a sweep of the registered
# skill schemas in `agency/capabilities/*` so the audit can satisfy
# its advertised "every registered skill parses clean" invariant.
_KNOWN_GATES = frozenset({"hard", "soft", "computed"})
_KNOWN_VARIANTS = frozenset({"step", "hard_gate", "soft_gate",
                             "computed_gate", "verb_bound"})


@dataclass(frozen=True)
class Phase:
    """Typed walkable-skill phase. `variant` discriminator drives walker
    dispatch — no more reading `phase["gate"]` at every callsite."""

    name: str
    variant: str                                                   # one of _KNOWN_VARIANTS
    produces: tuple[str, ...] = ()
    cue: str = ""
    gate: str = ""                                                 # "" | "hard" | "soft" | "computed"
    invoke: Optional[tuple[str, str]] = None                       # (capability, verb) for verb_bound
    reference: str = ""
    # Live-schema fields the existing registry already emits. Spec 152
    # Slice 1 carries them so the round-trip stays lossless against the
    # live capability code (Codex review on PR #127).
    index: Optional[int] = None
    verbs: tuple[str, ...] = ()
    gate_verb: str = ""

    def to_dict(self) -> dict:
        """Round-trip back to the source dict shape. Keys absent on the
        source dict (because they were defaults) stay absent here so the
        round-trip invariant holds for cheap hand-written skills."""
        out: dict[str, Any] = {}
        if self.index is not None:
            out["index"] = self.index                              # ordering convention: first
        out["name"] = self.name
        if self.produces:
            out["produces"] = list(self.produces)
        if self.verbs:
            out["verbs"] = list(self.verbs)
        if self.cue:
            out["cue"] = self.cue
        if self.gate:
            out["gate"] = self.gate
        if self.gate_verb:
            out["gate_verb"] = self.gate_verb
        if self.invoke is not None:
            out["invoke"] = {"capability": self.invoke[0], "verb": self.invoke[1]}
        if self.reference:
            out["reference"] = self.reference
        return out


@dataclass(frozen=True)
class Skill:
    name: str
    phases: tuple[Phase, ...] = ()
    kind: str = ""                                                 # "" | "usage" | "discipline" | "gate" | "workflow" | "conceptualizer" | …

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"name": self.name}
        if self.kind:
            out["kind"] = self.kind
        out["phases"] = [p.to_dict() for p in self.phases]
        return out


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
    gate_raw = d.get("gate", "")
    if not isinstance(gate_raw, str):
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` gate must be a string, "
            f"got {type(gate_raw).__name__}")
    gate = gate_raw or ""
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
    produces, err = _parse_string_list(d, "produces", parent=f"phase `{name}`")
    if err:
        return err
    cue, err = _parse_optional_string(d, "cue", parent=f"phase `{name}`")
    if err:
        return err
    reference, err = _parse_optional_string(d, "reference", parent=f"phase `{name}`")
    if err:
        return err
    gate_verb, err = _parse_optional_string(d, "gate_verb", parent=f"phase `{name}`")
    if err:
        return err
    verbs, err = _parse_string_list(d, "verbs", parent=f"phase `{name}`")
    if err:
        return err
    index_raw = d.get("index")
    index: Optional[int] = None
    if index_raw is not None:
        if not isinstance(index_raw, int) or isinstance(index_raw, bool):
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` index must be an int, "
                f"got {type(index_raw).__name__}")
        index = index_raw
    # Computed gates require a gate_verb (Codex finding); reject when missing.
    if gate == "computed" and not gate_verb:
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` has gate='computed' but is missing `gate_verb` "
            f"(computed gates dispatch through a verb)")
    variant = _derive_variant(gate=gate, invoke=invoke)
    return ParseResult.success(Phase(
        name=name,
        variant=variant,
        produces=produces,
        cue=cue,
        gate=gate,
        invoke=invoke,
        reference=reference,
        index=index,
        verbs=verbs,
        gate_verb=gate_verb,
    ))


def _parse_string_list(
    d: dict, key: str, *, parent: str,
) -> tuple[tuple[str, ...], Optional[ParseResult]]:
    """Validate `d[key]` is a list of strings (or absent). Returns the
    tuple + an optional failure ParseResult. No `or []` truthy coercion
    — a non-list value is a typed PHASE_MISSING_FIELD per Codex review."""
    from .toolresult import Codes
    if key not in d or d[key] is None:
        return (), None
    raw = d[key]
    if not isinstance(raw, list):
        return (), ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"{parent} `{key}` must be a list, "
            f"got {type(raw).__name__}")
    for i, v in enumerate(raw):
        if not isinstance(v, str):
            return (), ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"{parent} `{key}[{i}]` must be a string, "
                f"got {type(v).__name__}")
    return tuple(raw), None


def _parse_optional_string(
    d: dict, key: str, *, parent: str,
) -> tuple[str, Optional[ParseResult]]:
    """Validate `d[key]` is a string (or absent). Returns the string +
    an optional failure ParseResult. Non-string truthy values fail with
    PHASE_MISSING_FIELD instead of slipping past `or ""` coercion."""
    from .toolresult import Codes
    if key not in d or d[key] is None:
        return "", None
    raw = d[key]
    if not isinstance(raw, str):
        return "", ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"{parent} `{key}` must be a string, "
            f"got {type(raw).__name__}")
    return raw, None


def _derive_variant(*, gate: str, invoke: Optional[tuple[str, str]]) -> str:
    """The discriminator rule. `invoke` wins over `gate` when both are
    present (verb-bound phases delegate to the verb's own gate semantics)."""
    if invoke is not None:
        return "verb_bound"
    if gate == "hard":
        return "hard_gate"
    if gate == "soft":
        return "soft_gate"
    if gate == "computed":
        return "computed_gate"
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
    # `phases` is optional (a skill may declare zero phases) but if
    # present it MUST be a list — no `or []` truthy coercion silently
    # erasing a malformed value (Codex review).
    if "phases" in d and d["phases"] is not None:
        phases_raw = d["phases"]
        if not isinstance(phases_raw, list):
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"skill `{name}` phases must be a list, "
                f"got {type(phases_raw).__name__}")
    else:
        phases_raw = []
    kind = d.get("kind", "")
    if kind and not isinstance(kind, str):
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` kind must be a string, "
            f"got {type(kind).__name__}")
    phases: list[Phase] = []
    for i, pd in enumerate(phases_raw):
        sub = parse_phase(pd)
        if not sub.ok:
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"skill `{name}` phases[{i}]: {sub.message}")
        phases.append(sub.value)
    return ParseResult.success(Skill(name=name, phases=tuple(phases), kind=kind or ""))
