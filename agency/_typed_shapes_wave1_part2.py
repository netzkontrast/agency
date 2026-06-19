"""Wave-1 enhancement Slice 1 batch — 8 typed shapes.

Specs 155 / 160 / 163 / 166 / 167 / 172 / 174 / 177. Each ships the
frozen-dataclass + __post_init__ invariant pattern as its Slice 1; the
data shape IS the contract Slice 2 wires through the runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ── Spec 155 — RedTeamInvariant ──────────────────────────────────────
RedTeamStatus = Literal["pass", "fail", "skip"]
_RT_STATUS = ("pass", "fail", "skip")


@dataclass(frozen=True)
class RedTeamInvariant:
    """One documented red-team invariant + the rerun verdict."""

    invariant_id: str
    description:  str
    status:       RedTeamStatus
    ran_at:       str

    def __post_init__(self) -> None:
        if not self.invariant_id:
            raise ValueError("invariant_id must be non-empty")
        if self.status not in _RT_STATUS:
            raise ValueError(
                f"status must be one of {_RT_STATUS}; got {self.status!r}")


# ── Spec 160 — GateProjection (CLI --fields/--chain composition) ────
@dataclass(frozen=True)
class ChainStep:
    """One step in a YAML dataflow chain (Spec 160)."""

    cap:     str
    verb:    str
    args:    dict
    save_as: str | None = None
    fields:  list[str] | None = None

    def __post_init__(self) -> None:
        if not self.cap:
            raise ValueError("ChainStep.cap must be non-empty")
        if not self.verb:
            raise ValueError("ChainStep.verb must be non-empty")
        if not isinstance(self.args, dict):
            raise ValueError("ChainStep.args must be a dictionary")


@dataclass(frozen=True)
class GateProjection:
    """The projected dict the bash agent receives from `agency <cap>
    <verb> --fields a,b`. `kept` is the ordered key list; `dropped`
    are the keys the projection trimmed (operator visibility)."""

    kept:     tuple[str, ...]
    dropped:  tuple[str, ...]

    def __post_init__(self) -> None:
        for k in self.kept:
            if not k:
                raise ValueError("GateProjection.kept must not contain empty keys")


# ── Spec 163 — DeriveStatus (SkillDoc byte-equal derive) ────────────
DeriveResult = Literal["byte_equal", "drift", "missing"]
_DR_RESULTS = ("byte_equal", "drift", "missing")


@dataclass(frozen=True)
class DeriveStatus:
    """One SkillDoc derive-status record."""

    skill_name: str
    result:     DeriveResult
    bytes_drift: int = 0

    def __post_init__(self) -> None:
        if not self.skill_name:
            raise ValueError("skill_name must be non-empty")
        if self.result not in _DR_RESULTS:
            raise ValueError(
                f"result must be one of {_DR_RESULTS}; got {self.result!r}")
        if self.bytes_drift < 0:
            raise ValueError(
                f"bytes_drift must be >= 0; got {self.bytes_drift}")


# ── Spec 166 — WrapperShape ─────────────────────────────────────────
@dataclass(frozen=True)
class WrapperShape:
    """One `_<tool>.py` wrapper module shape (Spec 050 extras family)."""

    tool_name:     str
    axis_prefixes: tuple[str, ...]
    extras:        tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tool_name:
            raise ValueError("tool_name must be non-empty")
        if not self.axis_prefixes:
            raise ValueError(
                "axis_prefixes must declare at least one prefix")


# ── Spec 167 — ArchMetric ───────────────────────────────────────────
ArchMetricKind = Literal["cycle", "fan_out", "fan_in", "god_module"]
_AM_KINDS = ("cycle", "fan_out", "fan_in", "god_module")


@dataclass(frozen=True)
class ArchMetric:
    """Spec 051/167 architecture-metric finding."""

    axis_id: str
    kind:    ArchMetricKind
    nodes:   tuple[str, ...]
    score:   float

    def __post_init__(self) -> None:
        if not self.axis_id:
            raise ValueError("axis_id must be non-empty")
        if self.kind not in _AM_KINDS:
            raise ValueError(
                f"kind must be one of {_AM_KINDS}; got {self.kind!r}")
        if self.score < 0.0:
            raise ValueError(f"score must be >= 0; got {self.score}")


# ── Spec 172 — AxisRegistry ─────────────────────────────────────────
@dataclass(frozen=True)
class AxisRegistry:
    """Spec 057/172 — analyzer-axis registry (prefix → AnalyzerId)."""

    prefixes: tuple[tuple[str, str], ...]   # (prefix, analyzer_id) pairs

    def __post_init__(self) -> None:
        seen = set()
        for prefix, analyzer in self.prefixes:
            if not prefix or not analyzer:
                raise ValueError(
                    f"AxisRegistry entries must be non-empty; "
                    f"got ({prefix!r}, {analyzer!r})")
            if prefix in seen:
                raise ValueError(
                    f"duplicate prefix {prefix!r} in AxisRegistry")
            seen.add(prefix)

    def resolve(self, finding_id: str) -> str | None:
        for prefix, analyzer in self.prefixes:
            if finding_id.startswith(prefix):
                return analyzer
        return None


# ── Spec 174 — MigrationVerdict (template-verb migration) ───────────
MigrationStatus = Literal["migrated", "deferred", "blocked"]
_MS_STATUS = ("migrated", "deferred", "blocked")


@dataclass(frozen=True)
class MigrationVerdict:
    """Spec 060/174 — one verb's migration verdict."""

    verb_id:          str
    template_node_id: str
    schema_node_id:   str
    status:           MigrationStatus

    def __post_init__(self) -> None:
        if not self.verb_id:
            raise ValueError("verb_id must be non-empty")
        if self.status not in _MS_STATUS:
            raise ValueError(
                f"status must be one of {_MS_STATUS}; got {self.status!r}")


# ── Spec 177 — RefFinding ───────────────────────────────────────────
Severity = Literal["error", "warn"]
_RF_SEV = ("error", "warn")


@dataclass(frozen=True)
class RefFinding:
    """Spec 064/177 — plugin-reference continuous-audit finding."""

    file:      str
    invariant: str
    observed:  str
    expected:  str
    severity:  Severity

    def __post_init__(self) -> None:
        if not self.file:
            raise ValueError("file must be non-empty")
        if not self.invariant:
            raise ValueError("invariant must be non-empty")
        if self.severity not in _RF_SEV:
            raise ValueError(
                f"severity must be one of {_RF_SEV}; got {self.severity!r}")
