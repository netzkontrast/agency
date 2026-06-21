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

# ── Spec 371 — the v2 layered schema vocabulary ──────────────────────────────
# `type` is the best-practices CLASSIFICATION (R15) — orthogonal to `kind`
# (the walk-shape). Each type carries a different required CORE (the layered
# floor): a small required set per type, everything else optional (frugal).
_SKILL_TYPES = frozenset({
    "pillar", "capability", "technique", "pattern", "reference", "discipline",
})
# `owner` records WHO authored the skill (A6): the auto-generator, or the
# capability declaring a custom skill of its own.
_OWNERS = frozenset({"auto", "capability"})
# Per-phase degrees-of-freedom (R8): how much the agent may deviate.
_FREEDOM = frozenset({"high", "medium", "low"})
# The per-type required CORE beyond the universal `description` (R1). Each
# type's required section is the one R15 says defines its shape + test method:
# technique = steps, pattern = mental model, reference = pointers, discipline =
# the rationalization table. Pillars carry an overview map; capability is the
# general case (description-only floor).
_TYPE_REQUIRED = {
    "technique": ("phases",),
    "pattern": ("overview",),
    "reference": ("references",),
    "discipline": ("common_mistakes",),
    "pillar": ("overview",),
    "capability": (),
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
    # Spec 371 — inline content (A1/A2/R8/R9):
    "goal", "instructions", "example", "done_when", "freedom",
})
_SKILL_KNOWN_KEYS = frozenset({
    "name", "phases", "kind",
    # Spec 371 — the v2 best-practices structure (R1/R15/A4/A6):
    "type", "owner", "description", "overview", "when_to_use", "when_not",
    "references", "common_mistakes", "examples", "eval_scenarios",
    "source_stamp",
})


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
    # Spec 371 — inline content so a non-skill-walk agent can follow the
    # phase top-to-bottom (A1) AND the walk/file render from one source (A2).
    goal: str = ""                                                 # one-line phase objective
    instructions: str = ""                                         # the inline steps (A1/A2)
    example: str = ""                                              # one concrete example (R9)
    done_when: str = ""                                           # the phase's done-criterion
    freedom: str = ""                                             # "" | "high" | "medium" | "low" (R8)
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
        # Spec 371 inline content — emitted when truthy OR present on source
        # (same convention as the structural fields above).
        if self.goal or "goal" in src:
            out["goal"] = self.goal
        if self.instructions or "instructions" in src:
            out["instructions"] = self.instructions
        if self.example or "example" in src:
            out["example"] = self.example
        if self.done_when or "done_when" in src:
            out["done_when"] = self.done_when
        if self.freedom or "freedom" in src:
            out["freedom"] = self.freedom
        # Live-registry extras (preserved unchanged).
        for k, v in self.extras.items():
            out[k] = v
        return out


@dataclass(frozen=True)
class Skill:
    name: str
    phases: tuple[Phase, ...] = ()
    kind: str = ""                                                 # "" | "usage" | "discipline" | "gate" | "workflow" | "conceptualizer" | …
    # Spec 371 — the v2 best-practices structure. `type` is the R15
    # classification (orthogonal to `kind`); `owner` records the author
    # (A6); the rest is the layered content (R1/R9/A4). All optional at the
    # dataclass level — the per-type required CORE is enforced in parse_skill.
    type: str = ""                                                 # "" | pillar | capability | technique | pattern | reference | discipline
    owner: str = ""                                               # "" | auto | capability
    description: str = ""                                         # R1 — "use when…", search keywords
    overview: str = ""                                            # the mental map (pattern/pillar core)
    when_to_use: str = ""
    when_not: str = ""
    references: tuple[dict, ...] = ()                              # [{path, title?}] — one-deep refs (R4)
    common_mistakes: tuple[dict, ...] = ()                        # [{symptom, counter}] — the rationalization table (R13)
    examples: tuple[dict, ...] = ()                               # [{input, output}] — R9
    eval_scenarios: tuple[dict, ...] = ()                         # [{name, …}] — R14
    source_stamp: str = ""                                        # source-hash for the staleness gate (A7)
    extras: dict = field(default_factory=dict)                     # applies_when, etc.
    _source_keys: frozenset = field(default_factory=frozenset)

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"name": self.name}
        if self.kind:
            out["kind"] = self.kind
        src = self._source_keys
        # Spec 371 v2 fields — emitted when truthy OR present on source.
        if self.type or "type" in src:
            out["type"] = self.type
        if self.owner or "owner" in src:
            out["owner"] = self.owner
        if self.description or "description" in src:
            out["description"] = self.description
        if self.overview or "overview" in src:
            out["overview"] = self.overview
        if self.when_to_use or "when_to_use" in src:
            out["when_to_use"] = self.when_to_use
        if self.when_not or "when_not" in src:
            out["when_not"] = self.when_not
        # Emit `phases` only when source had the key (Codex review on
        # PR #127: a metadata-only `{"name": "x"}` skill must NOT gain
        # `phases: []` on round-trip).
        if self.phases or "phases" in src:
            out["phases"] = [p.to_dict() for p in self.phases]
        if self.references or "references" in src:
            out["references"] = [dict(r) for r in self.references]
        if self.common_mistakes or "common_mistakes" in src:
            out["common_mistakes"] = [dict(m) for m in self.common_mistakes]
        if self.examples or "examples" in src:
            out["examples"] = [dict(e) for e in self.examples]
        if self.eval_scenarios or "eval_scenarios" in src:
            out["eval_scenarios"] = [dict(s) for s in self.eval_scenarios]
        if self.source_stamp or "source_stamp" in src:
            out["source_stamp"] = self.source_stamp
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
    index: Optional[int] = None
    if "index" in d:
        index_raw = d["index"]
        # Codex review (round 8): `index: null` is NOT the same as
        # absent. `Phase.to_dict()` would drop the key on round-trip
        # because the stored `self.index is None`.
        if index_raw is None:
            return ParseResult.failure(
                Codes.PHASE_MISSING_FIELD,
                f"phase `{name}` has `index: null` — declare an int "
                f"or remove the key entirely")
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
    # Reject `gate: "hard"` (or any gate) ON a verb-bound phase EVEN
    # WHEN no explicit `kind` is declared (Codex review on PR #127). If
    # the SkillDoc keeps both, to_dict() preserves them, and the existing
    # walker invokes the verb THEN pauses on the hard gate — confirmed
    # resubmit re-invokes the verb (double-execution bug).
    if variant == "verb_bound" and gate:
        return ParseResult.failure(
            Codes.PHASE_UNKNOWN_KIND,
            f"phase `{name}` is verb-bound (`invoke` set) but also "
            f"declares `gate: {gate!r}` — invoke phases delegate gate "
            f"semantics to the invoked verb; remove `gate` or convert "
            f"to a hard/soft-gate phase without `invoke`")
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
    # Spec 371 — inline content fields (A1/A2/R9). Optional strings; the
    # phase carries them so the walk AND the rendered file read one source.
    goal, err = _parse_optional_string(d, "goal", parent=f"phase `{name}`")
    if err:
        return err
    instructions, err = _parse_optional_string(
        d, "instructions", parent=f"phase `{name}`")
    if err:
        return err
    example, err = _parse_optional_string(d, "example", parent=f"phase `{name}`")
    if err:
        return err
    done_when, err = _parse_optional_string(
        d, "done_when", parent=f"phase `{name}`")
    if err:
        return err
    # `freedom` is a closed enum (R8 — degrees of freedom): high/medium/low.
    freedom, err = _parse_optional_string(d, "freedom", parent=f"phase `{name}`")
    if err:
        return err
    if freedom and freedom not in _FREEDOM:
        return ParseResult.failure(
            Codes.PHASE_UNKNOWN_KIND,
            f"phase `{name}` has unknown freedom {freedom!r} "
            f"(R8 levels: {sorted(_FREEDOM)})")
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
        goal=goal,
        instructions=instructions,
        example=example,
        done_when=done_when,
        freedom=freedom,
        extras=extras,
        _source_keys=frozenset(d.keys()),
    ))


def _parse_string_list(
    d: dict, key: str, *, parent: str, reject_empty_strings: bool = True,
    code: str = "",
) -> tuple[tuple[str, ...], Optional[ParseResult]]:
    """Validate `d[key]` is a list of strings (or absent). Returns the
    tuple + an optional failure ParseResult. No `or []` truthy coercion
    — a non-list value is a typed failure per Codex review.

    `code` selects the failure Codes value (Spec 371: skill-level callers
    pass SKILL_PARSE_INVALID); defaults to PHASE_MISSING_FIELD.

    Codex review (round 7): empty-string elements (`produces: [""]`)
    are rejected by default so generated SkillDocs with blank output
    names fail fast at the boundary rather than reaching SkillRun.submit().

    Codex review (round 8): when the KEY is present with a `null` value,
    fail fast — `inputs: null` is not the same as absent and `to_dict()`
    would later rewrite it as `[]`, breaking the round-trip invariant.
    """
    from .toolresult import Codes
    code = code or Codes.PHASE_MISSING_FIELD
    if key not in d:
        return (), None
    if d[key] is None:
        return (), ParseResult.failure(
            code,
            f"{parent} has `{key}: null` — declare a list (possibly "
            f"empty) or remove the key entirely")
    raw = d[key]
    if not isinstance(raw, list):
        return (), ParseResult.failure(
            code,
            f"{parent} `{key}` must be a list, "
            f"got {type(raw).__name__}")
    for i, v in enumerate(raw):
        if not isinstance(v, str):
            return (), ParseResult.failure(
                code,
                f"{parent} `{key}[{i}]` must be a string, "
                f"got {type(v).__name__}")
        if reject_empty_strings and not v:
            return (), ParseResult.failure(
                code,
                f"{parent} `{key}[{i}]` must be non-empty")
    return tuple(raw), None


def _parse_optional_string(
    d: dict, key: str, *, parent: str, code: str = "",
) -> tuple[str, Optional[ParseResult]]:
    """Validate `d[key]` is a string (or absent). Returns the string +
    an optional failure ParseResult. Non-string truthy values fail with
    a typed code instead of slipping past `or ""` coercion.

    `code` selects the failure Codes value (Spec 371: skill-level callers
    pass SKILL_PARSE_INVALID); defaults to PHASE_MISSING_FIELD.

    Codex review (round 8): `cue: null` / `reference: null` etc. are
    NOT the same as absent. The round-trip invariant would later rewrite
    them as empty strings; reject at the boundary instead so
    `to_dict()` doesn't synthesize a key the source didn't have."""
    from .toolresult import Codes
    code = code or Codes.PHASE_MISSING_FIELD
    if key not in d:
        return "", None
    if d[key] is None:
        return "", ParseResult.failure(
            code,
            f"{parent} has `{key}: null` — declare a string or remove "
            f"the key entirely")
    raw = d[key]
    if not isinstance(raw, str):
        return "", ParseResult.failure(
            code,
            f"{parent} `{key}` must be a string, "
            f"got {type(raw).__name__}")
    return raw, None


def _parse_dict_list(
    d: dict, key: str, *, required: tuple[str, ...], parent: str, code: str,
) -> tuple[tuple[dict, ...], Optional[ParseResult]]:
    """Validate `d[key]` is a list of dicts, each carrying the `required`
    NON-EMPTY string keys (Spec 371 — references / common_mistakes /
    examples / eval_scenarios). Item dicts are copied verbatim so extra
    keys round-trip. Returns the tuple + an optional failure ParseResult.

    Consistent with `_parse_string_list`: `null` is not absent, a non-list
    fails, and the typed `code` is the caller's (SKILL_PARSE_INVALID)."""
    if key not in d:
        return (), None
    if d[key] is None:
        return (), ParseResult.failure(
            code,
            f"{parent} has `{key}: null` — declare a list (possibly "
            f"empty) or remove the key entirely")
    raw = d[key]
    if not isinstance(raw, list):
        return (), ParseResult.failure(
            code, f"{parent} `{key}` must be a list, got {type(raw).__name__}")
    items: list[dict] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            return (), ParseResult.failure(
                code, f"{parent} `{key}[{i}]` must be a dict, "
                f"got {type(item).__name__}")
        for rk in required:
            v = item.get(rk)
            if not isinstance(v, str) or not v:
                return (), ParseResult.failure(
                    code, f"{parent} `{key}[{i}]` is missing required "
                    f"non-empty string `{rk}`")
        items.append(dict(item))
    return tuple(items), None


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
    # ── Spec 371 — the v2 layered fields (all optional at parse; the
    # per-type required CORE is enforced after phases are parsed). ──────
    parent = f"skill `{name}`"
    skill_type, err = _parse_optional_string(
        d, "type", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    if skill_type and skill_type not in _SKILL_TYPES:
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"{parent} has unknown type {skill_type!r} "
            f"(R15 types: {sorted(_SKILL_TYPES)})")
    owner, err = _parse_optional_string(
        d, "owner", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    if owner and owner not in _OWNERS:
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"{parent} has unknown owner {owner!r} (A6 owners: {sorted(_OWNERS)})")
    description, err = _parse_optional_string(
        d, "description", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    overview, err = _parse_optional_string(
        d, "overview", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    when_to_use, err = _parse_optional_string(
        d, "when_to_use", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    when_not, err = _parse_optional_string(
        d, "when_not", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    source_stamp, err = _parse_optional_string(
        d, "source_stamp", parent=parent, code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    references, err = _parse_dict_list(
        d, "references", required=("path",), parent=parent,
        code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    common_mistakes, err = _parse_dict_list(
        d, "common_mistakes", required=("symptom", "counter"), parent=parent,
        code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    examples, err = _parse_dict_list(
        d, "examples", required=("input", "output"), parent=parent,
        code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
    eval_scenarios, err = _parse_dict_list(
        d, "eval_scenarios", required=("name",), parent=parent,
        code=Codes.SKILL_PARSE_INVALID)
    if err:
        return err
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
    # ── Spec 371 — the layered per-type required CORE. Only enforced when a
    # `type` is declared (legacy skills with no `type` keep today's floor:
    # name + kind). `description` (R1) is required for EVERY typed skill;
    # each type then adds the one section R15 says defines its shape. ───────
    if skill_type:
        _present = {
            "description": bool(description),
            "overview": bool(overview),
            "phases": bool(phases),
            "references": bool(references),
            "common_mistakes": bool(common_mistakes),
            "examples": bool(examples),
        }
        if not description:
            return ParseResult.failure(
                Codes.SKILL_PARSE_INVALID,
                f"{parent} type={skill_type!r} requires a `description` "
                f"(R1 — 'use when…', the discovery surface)")
        for req in _TYPE_REQUIRED.get(skill_type, ()):
            if not _present.get(req, False):
                return ParseResult.failure(
                    Codes.SKILL_PARSE_INVALID,
                    f"{parent} type={skill_type!r} requires `{req}` "
                    f"(the R15 core for a {skill_type} skill)")
    extras = {k: v for k, v in d.items() if k not in _SKILL_KNOWN_KEYS}
    return ParseResult.success(Skill(
        name=name, phases=tuple(phases), kind=kind,
        type=skill_type, owner=owner, description=description,
        overview=overview, when_to_use=when_to_use, when_not=when_not,
        references=references, common_mistakes=common_mistakes,
        examples=examples, eval_scenarios=eval_scenarios,
        source_stamp=source_stamp, extras=extras,
        _source_keys=frozenset(d.keys())))
