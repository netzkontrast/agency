"""Wave-3 enhancement Slice 1 batch — substantive typed shapes (Specs 178/179/180/182/183).

Promotes 5 wave-3 specs from catalogue stub (agency/_enhancement_stubs.py)
to substantive Slice 1 code. Each spec ships a frozen-dataclass + __post_init__
invariants matching the wave-1/2 typed-shape pattern.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ── Spec 178 — analyze.llm-judge-axis: typed JudgeVerdict ────────────
JudgeAxis = Literal["quality", "security", "performance", "architecture"]
_VALID_AXES = ("quality", "security", "performance", "architecture")


@dataclass(frozen=True)
class JudgeVerdict:
    """LLM judge's verdict on one analyze axis."""

    axis:        JudgeAxis
    confidence:  float
    rationale:   str
    findings:    tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.axis not in _VALID_AXES:
            raise ValueError(
                f"axis must be one of {_VALID_AXES}; got {self.axis!r}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0]; got {self.confidence}")
        if len(self.rationale) > 500:
            raise ValueError(
                f"rationale must be <= 500 chars; got {len(self.rationale)}")


# ── Spec 179 — document.render-llm-narrative: typed NarrativeSection ─
@dataclass(frozen=True)
class NarrativeSection:
    """One LLM-generated narrative section in a rendered document."""

    heading:   str
    body:      str
    cite_count: int

    def __post_init__(self) -> None:
        if not self.heading:
            raise ValueError("heading must be non-empty")
        if not self.body:
            raise ValueError("body must be non-empty")
        if self.cite_count < 0:
            raise ValueError(f"cite_count must be >= 0; got {self.cite_count}")


# ── Spec 180 — research.managed-agent-fanout: typed FanoutPlan ──────
@dataclass(frozen=True)
class FanoutAgent:
    """One specialist agent in a fanout plan."""

    role:      str
    query:     str
    timeout_s: int = 30

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("role must be non-empty")
        if not self.query:
            raise ValueError("query must be non-empty")
        if self.timeout_s <= 0:
            raise ValueError(f"timeout_s must be > 0; got {self.timeout_s}")


@dataclass(frozen=True)
class FanoutPlan:
    """Spec 180 — research-fanout dispatch plan."""

    research_id: str
    agents:      tuple[FanoutAgent, ...]
    max_parallel: int = 4

    def __post_init__(self) -> None:
        if not self.research_id:
            raise ValueError("research_id must be non-empty")
        if not self.agents:
            raise ValueError("agents must be non-empty (no-op fanout)")
        if self.max_parallel <= 0:
            raise ValueError(
                f"max_parallel must be > 0; got {self.max_parallel}")


# ── Spec 182 — cluster-coherence-live-audit: typed ClusterCoherence ─
ClusterStatus = Literal["coherent", "drift", "broken"]
_VALID_CLUSTER = ("coherent", "drift", "broken")


@dataclass(frozen=True)
class ClusterCoherence:
    """Spec 182 — one cluster's live coherence audit verdict."""

    cluster_id:  str
    status:      ClusterStatus
    audited_at:  str
    drift_count: int = 0

    def __post_init__(self) -> None:
        if not self.cluster_id:
            raise ValueError("cluster_id must be non-empty")
        if self.status not in _VALID_CLUSTER:
            raise ValueError(
                f"status must be one of {_VALID_CLUSTER}; got {self.status!r}")
        if self.drift_count < 0:
            raise ValueError(
                f"drift_count must be >= 0; got {self.drift_count}")


# ── Spec 183 — intent-chain-opportunity-detector: typed ChainHint ───
HintKind = Literal["chain_next", "parallel_branch", "rollup"]
_VALID_HINTS = ("chain_next", "parallel_branch", "rollup")


@dataclass(frozen=True)
class ChainHint:
    """Spec 183 — one intent-chain opportunity hint."""

    source_intent_id:  str
    target_verb:       str
    kind:              HintKind
    confidence:        float

    def __post_init__(self) -> None:
        if not self.source_intent_id:
            raise ValueError("source_intent_id must be non-empty")
        if not self.target_verb:
            raise ValueError("target_verb must be non-empty")
        if self.kind not in _VALID_HINTS:
            raise ValueError(
                f"kind must be one of {_VALID_HINTS}; got {self.kind!r}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0]; got {self.confidence}")
