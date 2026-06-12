"""Spec 173 Slice 1 — typed LinkFinding for the reflection-edge linter.

Every Reflection in the graph MUST carry two edges: `SERVES` to an
Intent (Spec 002 provenance moat) and `OBSERVED_DURING` to the Event
that produced the observation (Spec 076 unified-hook discipline).

Spec 173 Slice 1 ships the typed lint finding so the audit + the CI
gate consume one shape. Slice 2 wires the live-graph walker into
`scripts/check-drift`; Slice 3 promotes warn → error per the
documented promotion calendar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MissingEdge = Literal["SERVES", "OBSERVED_DURING"]
Severity    = Literal["error", "warn"]
_VALID_EDGES = ("SERVES", "OBSERVED_DURING")
_VALID_SEVERITIES = ("error", "warn")


@dataclass(frozen=True)
class LinkFinding:
    """One reflection-edge lint finding.

    `reflection_id` — the offending Reflection node id.
    `missing_edge` — the edge that's missing (SERVES or OBSERVED_DURING).
    `severity` — error blocks CI; warn surfaces in the report only.
    `file` / `line` — best-effort source attribution; "" when unknown.
    """

    reflection_id: str
    missing_edge:  MissingEdge
    severity:      Severity
    file:          str = ""
    line:          int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.reflection_id, str) or not self.reflection_id:
            raise ValueError(
                f"reflection_id must be non-empty; got {self.reflection_id!r}")
        if self.missing_edge not in _VALID_EDGES:
            raise ValueError(
                f"missing_edge must be one of {_VALID_EDGES}; "
                f"got {self.missing_edge!r}")
        if self.severity not in _VALID_SEVERITIES:
            raise ValueError(
                f"severity must be one of {_VALID_SEVERITIES}; "
                f"got {self.severity!r}")
        if self.line < 0:
            raise ValueError(
                f"line must be >= 0; got {self.line}")
