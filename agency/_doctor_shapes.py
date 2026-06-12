"""Spec 170 Slice 1 — typed Field/Section/Report shapes for `agency_doctor`.

The doctor surface today is an ad-hoc dict with per-section dict bodies.
Spec 170 lifts it to a typed contract so every section has the same
shape + the invariants are enforced at construction:

  ready=False ⇒ hint is non-empty (pipx-HINT pattern, Spec 065 generalised)
  source ∈ {env, extra, graph, registry}  (where the value comes from)

Slice 1 ships the shapes + invariants offline-clean. Slice 2 wires
the existing `agency_doctor` verb to emit `DoctorReport` instead of
the ad-hoc dict; Slice 3 adds a CLI `--strict` gate that fails when
any documented `ready=False` field's hint is the empty string.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


FieldSource = Literal["env", "extra", "graph", "registry"]
_VALID_SOURCES = ("env", "extra", "graph", "registry")


@dataclass(frozen=True)
class DoctorField:
    """One field in a doctor section.

    `key` — short identifier (e.g. "plugin_enabled", "anthropic_backend").
    `value` — JSON-serialisable scalar / list / dict.
    `ready` — True iff the field's value indicates a healthy state.
    `hint` — when `ready=False`, MUST be a non-empty string telling
             the operator what to do. When `ready=True`, optional.
    `source` — where the value was read from (env / extra / graph / registry).
    """

    key:    str
    value:  Any
    ready:  bool
    hint:   str | None
    source: FieldSource

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key:
            raise ValueError(f"key must be a non-empty string; got {self.key!r}")
        if self.source not in _VALID_SOURCES:
            raise ValueError(
                f"source must be one of {_VALID_SOURCES}; got {self.source!r}")
        if not self.ready and not (self.hint or "").strip():
            raise ValueError(
                f"DoctorField {self.key!r}: ready=False requires a non-empty "
                f"hint (pipx-HINT pattern; Spec 170 invariant)")


@dataclass(frozen=True)
class DoctorSection:
    """A named group of fields (e.g. "hooks", "anthropic", "embedder")."""

    name:   str
    fields: tuple[DoctorField, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError(
                f"section name must be a non-empty string; got {self.name!r}")
        for f in self.fields:
            if not isinstance(f, DoctorField):
                raise TypeError(
                    f"DoctorSection {self.name!r}: fields must be DoctorField; "
                    f"got {type(f).__name__}")


@dataclass(frozen=True)
class DoctorReport:
    """Whole doctor payload — ordered sections."""

    sections: tuple[DoctorSection, ...] = ()

    def to_dict(self) -> dict:
        """Render as a nested dict preserving section + field order.
        `{section_name: {field_key: {value, ready, hint, source}}}`."""
        out: dict = {}
        for sec in self.sections:
            body: dict = {}
            for f in sec.fields:
                body[f.key] = {
                    "value":  f.value,
                    "ready":  f.ready,
                    "hint":   f.hint,
                    "source": f.source,
                }
            out[sec.name] = body
        return out

    def invariant_violations(self) -> list[str]:
        """Walk every section + field; report any invariant violation
        (the dataclasses already raise at construction, but this lets a
        merged Report be re-audited — e.g. after a JSON round-trip)."""
        bad: list[str] = []
        for sec in self.sections:
            for f in sec.fields:
                try:
                    DoctorField(key=f.key, value=f.value, ready=f.ready,
                                 hint=f.hint, source=f.source)
                except (ValueError, TypeError) as e:
                    bad.append(f"{sec.name}.{f.key}: {e}")
        return bad
