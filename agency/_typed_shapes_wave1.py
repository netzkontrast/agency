"""Spec 171 + 175 + 176 Slice 1 — typed shapes for the wave-1 batch.

Three small typed-shape Slice-1's, batched into one module since they
share the same frozen-dataclass + invariant pattern shipped across the
rest of the wave-1 enhancement specs (156/157/162/164/165/168/169/170).

- Spec 171 — `GuardFinding` for the node-id-guard CI gate.
- Spec 175 — `InstallSurface{marketplace_desc, readme_capability_rows,
  slash_commands, userconfig_extras, generated_at}` typed install map.
- Spec 176 — `IntentCapture` per-session capture record.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ── Spec 171 — GuardFinding ───────────────────────────────────────────
Severity = Literal["error", "warn"]
_VALID_SEVERITIES = ("error", "warn")


@dataclass(frozen=True)
class GuardFinding:
    """One node-id-guard lint finding (Spec 056 + Spec 171)."""

    verb_id:        str
    param_name:     str
    expected_label: str
    severity:       Severity
    file:           str = ""
    line:           int = 0

    def __post_init__(self) -> None:
        for label, val in (("verb_id", self.verb_id),
                            ("param_name", self.param_name),
                            ("expected_label", self.expected_label)):
            if not isinstance(val, str) or not val:
                raise ValueError(f"{label} must be non-empty string; got {val!r}")
        if self.severity not in _VALID_SEVERITIES:
            raise ValueError(
                f"severity must be one of {_VALID_SEVERITIES}; "
                f"got {self.severity!r}")


# ── Spec 175 — InstallSurface ────────────────────────────────────────
@dataclass(frozen=True)
class CapabilityRow:
    """One row in the README capability table."""

    name:        str
    verb_count:  int
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError(
                f"CapabilityRow.name must be non-empty; got {self.name!r}")
        if self.verb_count < 0:
            raise ValueError(
                f"CapabilityRow.verb_count must be >= 0; got {self.verb_count}")


@dataclass(frozen=True)
class CommandFile:
    """One slash-command file in the install."""

    name: str
    path: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError(
                f"CommandFile.name must be non-empty; got {self.name!r}")
        if not isinstance(self.path, str) or not self.path:
            raise ValueError(
                f"CommandFile.path must be non-empty; got {self.path!r}")


@dataclass(frozen=True)
class InstallSurface:
    """The whole derived install surface as ONE object (Spec 061 + 175)."""

    marketplace_desc:        str
    readme_capability_rows:  tuple[CapabilityRow, ...]
    slash_commands:          tuple[CommandFile, ...]
    userconfig_extras:       tuple[str, ...]
    generated_at:            str

    def __post_init__(self) -> None:
        if not isinstance(self.marketplace_desc, str) or not self.marketplace_desc:
            raise ValueError(
                f"InstallSurface.marketplace_desc must be non-empty")


# ── Spec 176 — IntentCapture ─────────────────────────────────────────
IntentSource = Literal["sessionstart", "manual", "auto_ad_hoc"]
_VALID_SOURCES = ("sessionstart", "manual", "auto_ad_hoc")


@dataclass(frozen=True)
class IntentCapture:
    """Per-session intent-capture record (Spec 062 + 176)."""

    intent_id:    str
    captured_at:  str
    source:       IntentSource
    artefact_ids: tuple[str, ...] = ()
    turns:        int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.intent_id, str) or not self.intent_id:
            raise ValueError(
                f"IntentCapture.intent_id must be non-empty")
        if self.source not in _VALID_SOURCES:
            raise ValueError(
                f"IntentCapture.source must be one of {_VALID_SOURCES}; "
                f"got {self.source!r}")
        if self.turns < 0:
            raise ValueError(
                f"IntentCapture.turns must be >= 0; got {self.turns}")
