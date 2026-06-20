"""Spec 164 Slice 1 — typed VerifyResult shape for wet implementation-discipline phases.

The Slice 2 wet path (Spec 147 AnthropicDriver) runs the discipline-skill
verify step against a phase's outputs + the live graph; this slice ships
the typed return shape every verifier — wet OR scaffold (the deterministic
fallback) — coerces to.

Per Spec 050 graceful-degradation pattern: when `[anthropic]` is absent
(or the API key isn't provisioned), `matcher == "scaffold"` for every
discipline. Slice 2 promotes to `matcher == "wet"` when the driver is
ready.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


VerifyMatcher = Literal["wet", "scaffold"]


@dataclass(frozen=True)
class VerifyResult:
    """Typed return of one discipline's verify step against a phase.

    `rationale` ≤ 200 chars (Slice 1 invariant). `evidence_refs` is a list
    of graph node ids the verdict cites (Reflection / Artefact / Skill /
    Phase ids). `matcher` discriminates wet vs scaffold; when `[anthropic]`
    is absent the runner MUST emit `"scaffold"` (Slice 1 graceful-
    degradation invariant)."""

    phase_id:      str
    accepted:      bool
    rationale:     str
    evidence_refs: tuple[str, ...] = ()
    matcher:       VerifyMatcher = "scaffold"

    def __post_init__(self) -> None:
        if len(self.rationale) > 200:
            raise ValueError(
                f"rationale must be ≤ 200 chars; got {len(self.rationale)}")
        if self.matcher not in ("wet", "scaffold"):
            raise ValueError(
                f"matcher must be 'wet' or 'scaffold'; got {self.matcher!r}")
        for r in self.evidence_refs:
            if not isinstance(r, str) or ":" not in r:
                raise ValueError(
                    f"evidence_refs must be node ids of form '<label>:<id>'; "
                    f"got {r!r}")

    @classmethod
    def scaffold(cls, *, phase_id: str, accepted: bool,
                  rationale: str = "scaffold-fallback (no LLM driver)",
                  evidence_refs: tuple[str, ...] = (),
                  ) -> "VerifyResult":
        """Construct a `scaffold`-mode result (the deterministic fallback
        path). Use when `[anthropic]` is absent or the call would block
        the dispatch."""
        return cls(phase_id=phase_id, accepted=accepted,
                    rationale=rationale[:200],
                    evidence_refs=tuple(evidence_refs),
                    matcher="scaffold")

    @classmethod
    def wet(cls, *, phase_id: str, accepted: bool, rationale: str,
             evidence_refs: tuple[str, ...] = (),
             ) -> "VerifyResult":
        """Construct a `wet`-mode result. Slice 2 wires this from the
        Spec 147 AnthropicDriver `complete()` response."""
        return cls(phase_id=phase_id, accepted=accepted,
                    rationale=rationale[:200],
                    evidence_refs=tuple(evidence_refs),
                    matcher="wet")

    def to_dict(self) -> dict:
        d = asdict(self)
        # Tuple round-trips as list — fine for JSON.
        d["evidence_refs"] = list(self.evidence_refs)
        return d
