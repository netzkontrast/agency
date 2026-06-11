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

# Documented phase-`kind` field (Spec 003 / spec.md `phases=[{"kind":
# "hard-gate", ...}]`). The mapping below records, per declared kind,
# the gate it implies AND the variant it must derive to. The
# kind-vs-derived-variant check uses _PHASE_KIND_TO_VARIANT so a
# `kind: "hard-gate"` combined with an `invoke` block fails fast
# (invoke wins → variant `verb_bound` ≠ declared `hard_gate`) instead
# of silently dispatching as a verb (Codex review on PR #127).
_PHASE_KIND_TO_GATE = {
    "hard-gate": "hard",
    "soft-gate": "soft",
    "computed-gate": "computed",
    "step": "",
    "verb-bound": "",                                              # `invoke` carries the binding
}
_PHASE_KIND_TO_VARIANT = {
    "hard-gate": "hard_gate",
    "soft-gate": "soft_gate",
    "computed-gate": "computed_gate",
    "step": "step",
    "verb-bound": "verb_bound",
}

# Fields the typed Phase pulls out directly. Anything else lands in
# `extras` so the round-trip preserves the live-registry metadata
# (Codex review on PR #127: `applies_when` on the skill, `inputs` on
# Jules phases, future `text` from Spec 003 — all survive untouched).
# `predicate` is consumed by the hard-gate validation in parse_phase
# but ALSO preserved through extras so the round trip is lossless.
_PHASE_KNOWN_KEYS = frozenset({
    "name", "produces", "cue", "gate", "invoke", "reference",
    "index", "verbs", "gate_verb", "kind", "inputs",
})
_SKILL_KNOWN_KEYS = frozenset({"name", "phases", "kind"})


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
    kind: str = ""                                                 # Spec 003 phase-kind shape
    inputs: tuple[str, ...] = ()                                   # walker kwargs for verb-bound dispatch
    # Catch-all for live-registry fields the typed Phase doesn't claim
    # (e.g. `predicate`/`text` from the Spec 003 hard-gate shape).
    # Preserved through the round trip.
    extras: dict = field(default_factory=dict)
    # The set of TYPED-FIELD keys that were present on the source dict.
    # `to_dict()` emits a known-key only when its value is truthy OR
    # the key appeared on the source — that way `verbs: []` round-trips
    # back to `verbs: []` (live registry has this in the scene-writer
    # skill) and a kind-only `gate` doesn't synthesize a `gate: "hard"`
    # field that wasn't in the source. Codex review on PR #127.
    _source_keys: frozenset = field(default_factory=frozenset)

    def to_dict(self) -> dict:
        """Round-trip back to the source dict shape. A key is emitted iff
        its value is truthy OR the key was present on the source dict —
        so `verbs: []` round-trips back to `verbs: []` and a kind-only
        SkillDoc does NOT gain a synthesized `gate: "hard"` field."""
        out: dict[str, Any] = {}
        src = self._source_keys
        if self.index is not None:
            out["index"] = self.index                              # ordering convention: first
        out["name"] = self.name
        if self.kind:
            out["kind"] = self.kind
        if self.produces or "produces" in src:
            out["produces"] = list(self.produces)
        if self.verbs or "verbs" in src:
            out["verbs"] = list(self.verbs)
        if self.inputs or "inputs" in src:
            out["inputs"] = list(self.inputs)
        if self.cue or "cue" in src:
            out["cue"] = self.cue
        if self.gate or "gate" in src:
            out["gate"] = self.gate
        if self.gate_verb or "gate_verb" in src:
            out["gate_verb"] = self.gate_verb
        if self.invoke is not None:
            out["invoke"] = {"capability": self.invoke[0], "verb": self.invoke[1]}
        if self.reference or "reference" in src:
            out["reference"] = self.reference
        # Live-registry extras (preserved unchanged).
        for k, v in self.extras.items():
            out[k] = v
        return out


@dataclass(frozen=True)
class Skill:
    name: str
    phases: tuple[Phase, ...] = ()
    kind: str = ""                                                 # "" | "usage" | "discipline" | "gate" | "workflow" | "conceptualizer" | …
    extras: dict = field(default_factory=dict)                     # applies_when, etc.
    _source_keys: frozenset = field(default_factory=frozenset)

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"name": self.name}
        if self.kind:
            out["kind"] = self.kind
        # Emit `phases` only when source had the key (Codex review on
        # PR #127: a metadata-only `{"name": "x"}` skill must NOT gain
        # `phases: []` on round-trip).
        if self.phases or "phases" in self._source_keys:
            out["phases"] = [p.to_dict() for p in self.phases]
        for k, v in self.extras.items():
            out[k] = v
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
    # Codex review (round 7): `"invoke": null` is NOT the same as absent
    # — a generated SkillDoc that serializes an executable phase with a
    # null invoke must fail fast, not silently be walked as a step.
    invoke: Optional[tuple[str, str]] = None
    if "invoke" in d:
        invoke_raw = d["invoke"]
        if invoke_raw is None:
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` has `invoke: null` — declare a "
                f"{{capability, verb}} dict or remove the key entirely")
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
    # Spec 018 `SkillRun.submit()` iterates `p.get("inputs", [])` to build
    # kwargs for the invoked verb — Codex review on PR #127. Lift +
    # validate as a list of strings (matches `produces` / `verbs`); a
    # string `inputs: "source"` would otherwise split into characters.
    inputs, err = _parse_string_list(d, "inputs", parent=f"phase `{name}`")
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
    # Documented phase-`kind` field (Spec 003): when present, it MUST be
    # a string AND a documented kind. The DERIVED-VARIANT consistency
    # check below validates against the post-derivation variant so
    # `kind: "hard-gate" + invoke: ...` (which `_derive_variant` would
    # classify as `verb_bound`) fails fast with PHASE_UNKNOWN_KIND
    # instead of silently dispatching as a verb.
    kind = ""
    if "kind" in d:
        kind_raw = d["kind"]
        if not isinstance(kind_raw, str):
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` kind must be a string, "
                f"got {type(kind_raw).__name__}")
        if kind_raw not in _PHASE_KIND_TO_GATE:
            return ParseResult.failure(
                Codes.PHASE_UNKNOWN_KIND,
                f"phase `{name}` has unknown kind {kind_raw!r} "
                f"(documented kinds: {sorted(_PHASE_KIND_TO_GATE)})")
        kind = kind_raw
    # `kind: "verb-bound"` requires `invoke` — surfacing the specific
    # missing field is more useful than the generic kind/variant
    # mismatch message that would otherwise fire below.
    if kind == "verb-bound" and invoke is None:
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` kind='verb-bound' requires `invoke` "
            f"({{'capability': ..., 'verb': ...}})")
    # Honor kind-only SkillDocs (spec.md form): `{"kind": "hard-gate",
    # "predicate": "..."}` declares a hard gate WITHOUT a redundant
    # `gate: "hard"` field. Use the effective gate (source gate OR
    # implied from kind) for the variant derivation, but DON'T overwrite
    # `gate` — that would synthesize a `gate: "hard"` field on
    # round-trip (Codex review on PR #127). The Phase carries the
    # SOURCE `gate` value verbatim.
    effective_gate = gate or _PHASE_KIND_TO_GATE.get(kind, "")
    # Derive the variant so the kind/produces/predicate/gate_verb
    # checks below see the post-derivation truth, not just the raw
    # gate-vs-invoke shape (Codex review on PR #127 §"Reject phase kinds
    # that derive a different variant").
    variant = _derive_variant(gate=effective_gate, invoke=invoke)
    # If the author declared `kind`, it MUST agree with the derived
    # variant. `kind: "hard-gate"` + `invoke: ...` → derived variant is
    # `verb_bound`, so the declared kind contradicts how the phase
    # actually walks — fail fast.
    if kind and _PHASE_KIND_TO_VARIANT[kind] != variant:
        return ParseResult.failure(
            Codes.PHASE_UNKNOWN_KIND,
            f"phase `{name}` declared kind={kind!r} but its gate/invoke "
            f"shape derives variant={variant!r} "
            f"(invoke takes precedence over gate; a hard-gate phase must "
            f"not also carry `invoke`)")
    # Per-variant invariants (Codex review rounds 2-4 on PR #127):
    # - ALL parsed phases must declare non-empty `produces`. The walker
    #   (Spec 018 SkillRun.current / submit) reads `p["produces"]`
    #   unconditionally — a phase without it raises KeyError on the
    #   first disclosure step. Reject at the parse boundary.
    # - computed_gate: requires `gate_verb` (the gate dispatches through
    #   a verb). When `invoke` is ALSO present, variant is verb_bound
    #   and this check does NOT apply (invoke wins; the invoked verb's
    #   own gate semantics take over).
    # - hard_gate (kind="hard-gate"): MUST declare a `predicate` field.
    #   The spec.md worked failure case says this exact shape must fail.
    if not produces:
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` is missing required field `produces` "
            f"(the walker reads it unconditionally; ≥ 1 output name "
            f"required per phase)")
    # An invoke phase stores its verb result at `p["produces"][0]` and
    # validates EVERY produced name (Spec 018 SkillRun.submit). >1
    # produces entries means the second+ can never be satisfied by the
    # invoked verb's single return — Spec 003 requires exactly one.
    if invoke is not None and len(produces) != 1:
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` is verb-bound (`invoke` set) so it must "
            f"declare EXACTLY one `produces` entry (got {len(produces)}: "
            f"{list(produces)!r}); the walker stores the verb result at "
            f"`produces[0]` and validates every name")
    if variant == "computed_gate" and not gate_verb:
        return ParseResult.failure(
            Codes.PHASE_MISSING_FIELD,
            f"phase `{name}` has gate='computed' but is missing `gate_verb` "
            f"(computed gates dispatch through a verb)")
    if kind == "hard-gate":
        predicate = d.get("predicate")
        if not isinstance(predicate, str) or not predicate:
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` kind='hard-gate' requires `predicate` "
                f"(the assertion the walker enforces before passing)")
    extras = {k: v for k, v in d.items() if k not in _PHASE_KNOWN_KEYS}
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
        kind=kind,
        inputs=inputs,
        extras=extras,
        _source_keys=frozenset(d.keys()),
    ))


def _parse_string_list(
    d: dict, key: str, *, parent: str, reject_empty_strings: bool = True,
) -> tuple[tuple[str, ...], Optional[ParseResult]]:
    """Validate `d[key]` is a list of strings (or absent). Returns the
    tuple + an optional failure ParseResult. No `or []` truthy coercion
    — a non-list value is a typed PHASE_MISSING_FIELD per Codex review.

    Codex review (round 7): empty-string elements (`produces: [""]`)
    are rejected by default so generated SkillDocs with blank output
    names fail fast at the boundary rather than reaching SkillRun.submit().
    """
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
        if reject_empty_strings and not v:
            return (), ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"{parent} `{key}[{i}]` must be non-empty")
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
    # `phases` is optional (a skill may declare zero phases). Codex
    # review (round 7): when the KEY is present, the value MUST be a
    # list — `"phases": null` is malformed; do not erase it.
    if "phases" in d:
        phases_raw = d["phases"]
        if phases_raw is None:
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"skill `{name}` has `phases: null` — declare a list "
                f"(possibly empty) or remove the key entirely")
        if not isinstance(phases_raw, list):
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"skill `{name}` phases must be a list, "
                f"got {type(phases_raw).__name__}")
    else:
        phases_raw = []
    # `kind` is REQUIRED. The existing walker constructs a SkillRun by
    # reading `schema["kind"]` unconditionally; a skill without `kind`
    # would parse here and then crash on first walk. Spec 003 lists
    # kind as part of the required skill shape (Codex review on PR #127).
    if "kind" not in d or d["kind"] is None:
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` is missing required field `kind` "
            f"(e.g. \"usage\" / \"discipline\" / \"gate\" / \"workflow\")")
    if not isinstance(d["kind"], str):
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` kind must be a string, "
            f"got {type(d['kind']).__name__}")
    if not d["kind"]:
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` kind must be non-empty")
    kind = d["kind"]
    phases: list[Phase] = []
    for i, pd in enumerate(phases_raw):
        sub = parse_phase(pd)
        if not sub.ok:
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"skill `{name}` phases[{i}]: {sub.message}")
        phases.append(sub.value)
    # Phase-index contiguity invariant (Spec 003): when ANY phase declares
    # `index`, EVERY phase must declare it AND the indices form 1..N. The
    # walker advances by list position while exposing/recording
    # `p["index"]`; mismatched indices produce misleading provenance.
    indices = [p.index for p in phases]
    has_any = any(i is not None for i in indices)
    has_all = all(i is not None for i in indices)
    if has_any and not has_all:
        missing = [i for i, val in enumerate(indices) if val is None]
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` mixes indexed + un-indexed phases "
            f"(missing index on positions {missing}); declare `index` "
            f"on every phase or none")
    if has_all and tuple(indices) != tuple(range(1, len(indices) + 1)):
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"skill `{name}` phase indices must be contiguous 1..{len(indices)} "
            f"(got {indices})")
    extras = {k: v for k, v in d.items() if k not in _SKILL_KNOWN_KEYS}
    return ParseResult.success(Skill(
        name=name, phases=tuple(phases), kind=kind, extras=extras,
        _source_keys=frozenset(d.keys())))
