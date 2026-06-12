"""Spec 181 Slice 1 — typed EmbedderHandle for the reflect-embedder upgrade.

Spec 045 ships the pluggable embedder boundary; Spec 181 extends it with
a typed handle that surfaces backend identity + readiness + the
ready=False⇒hint invariant (pipx-HINT pattern, Spec 065).

Slice 2 wires the new bge-large + openai backends behind the same handle;
Slice 1 ships the data shape so consumers (recall verb, agency_doctor,
the install path) speak ONE protocol regardless of backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EmbedderBackend = Literal["tfidf", "bge-small", "bge-large", "openai"]
_VALID_BACKENDS = ("tfidf", "bge-small", "bge-large", "openai")


@dataclass(frozen=True)
class EmbedderHandle:
    """Typed handle to one embedder instance."""

    name:    str
    dim:     int
    backend: EmbedderBackend
    ready:   bool
    hint:    str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError(f"name must be non-empty; got {self.name!r}")
        if self.backend not in _VALID_BACKENDS:
            raise ValueError(
                f"backend must be one of {_VALID_BACKENDS}; got {self.backend!r}")
        if self.dim < 0:
            raise ValueError(f"dim must be >= 0; got {self.dim}")
        if self.ready and self.dim <= 0:
            raise ValueError(
                f"ready=True embedder must have dim > 0; got {self.dim}")
        if not self.ready and not (self.hint or "").strip():
            raise ValueError(
                f"EmbedderHandle {self.name!r}: ready=False requires non-empty hint")
