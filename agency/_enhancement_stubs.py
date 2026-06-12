"""Wave 3-12 enhancement Slice 1 catalogue — typed stubs for every drafted spec.

Each EnhancementSliceStub records the Slice 1 commitment: the spec_id +
slug + wave. Slice 2 of each spec wires its runtime; Slice 1 IS the
typed catalogue entry — visible, queryable, deterministic.

The catalogue is the SUBSET invariant: every Plan/NNN-… drafted spec
in waves 3-12 has an entry. A new drafted spec MUST add a stub here
(enforced by the live-tree test).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SliceStatus = Literal["slice1_typed_stub", "slice1_concrete", "shipped_full"]
_VALID_STATUS = ("slice1_typed_stub", "slice1_concrete", "shipped_full")


@dataclass(frozen=True)
class EnhancementSliceStub:
    """One drafted-spec Slice 1 catalogue entry."""

    spec_id: str
    slug:    str
    wave:    int
    status:  SliceStatus = "slice1_typed_stub"

    def __post_init__(self) -> None:
        if not self.spec_id or len(self.spec_id) != 3 or not self.spec_id.isdigit():
            raise ValueError(
                f"spec_id must be a 3-digit string; got {self.spec_id!r}")
        if not self.slug:
            raise ValueError("slug must be non-empty")
        if not (1 <= self.wave <= 12):
            raise ValueError(f"wave must be 1..12; got {self.wave}")
        if self.status not in _VALID_STATUS:
            raise ValueError(
                f"status must be one of {_VALID_STATUS}; got {self.status!r}")


_CATALOG = [
    ('178', 'analyze-llm-judge-axis', 3),
    ('179', 'document-render-llm-narrative', 3),
    ('180', 'research-managed-agent-fanout', 3),
    ('181', 'reflect-embedder-upgrade', 3),
    ('182', 'cluster-coherence-live-audit', 3),
    ('183', 'intent-chain-opportunity-detector', 3),
    ('184', 'naming-rename-codemode-alias', 4),
    ('185', 'pipx-uvx-install-path', 4),
    ('186', 'token-economy-cluster-followup', 4),
    ('187', 'lint-token-rules-output-side', 4),
    ('188', 'tiered-discovery-llm-drill', 4),
    ('189', 'verb-surface-consolidation-impl', 4),
    ('190', 'skill-surface-reconciliation-impl', 4),
    ('191', 'vision-alignment-live-matrix', 4),
    ('192', 'shell-cap-safety-gate', 4),
    ('193', 'token-economy-capstone-output', 4),
    ('194', 'shell-define-llm-suggest', 4),
    ('196', 'bdd-gherkin-driver-impl', 5),
    ('197', 'static-walkable-skills-resolve', 5),
    ('198', 'cli-mirror-chain-parity', 5),
    ('199', 'agent-skills-publish-roundtrip', 5),
    ('200', 'walkable-usage-skill-depth', 5),
    ('201', 'token-counter-api-boundary', 5),
    ('202', 'skills-api-publish-managed', 5),
    ('203', 'analyze-graph-query-language', 5),
    ('204', 'reasoning-intent-driver-wet', 5),
    ('205', 'substrate-hardening-continuous', 5),
    ('206', 'music-master-llm-production', 6),
    ('207', 'music-lifecycle-output-budget', 6),
    ('208', 'music-lyrics-llm-generation', 6),
    ('209', 'music-audio-driver-managed', 6),
    ('210', 'music-catalogue-graph-query', 6),
    ('211', 'music-promo-llm-copy', 6),
    ('212', 'music-research-fanout', 6),
    ('213', 'music-gates-llm-judge', 6),
    ('214', 'music-binding-derived-config', 6),
    ('215', 'music-runtime-doctor', 6),
    ('216', 'music-name-exposure-driver', 6),
    ('217', 'novel-master-llm-build', 7),
    ('218', 'novel-lifecycle-output-budget', 7),
    ('219', 'novel-storyform-llm-assist', 7),
    ('220', 'novel-prose-driver-wet', 7),
    ('221', 'novel-research-fanout', 7),
    ('222', 'novel-catalogue-graph-query', 7),
    ('223', 'novel-manuscript-managed-export', 7),
    ('224', 'novel-gates-llm-judge', 7),
    ('225', 'prompt-cap-slice2-llm', 8),
    ('226', 'thinking-cap-slice2-wet', 8),
    ('227', 'capability-migration-execute', 8),
    ('228', 'dossier-cap-managed-corpus', 8),
    ('229', 'session-driver-slice2-hooks', 8),
    ('230', 'storyform-completion-llm-suggest', 9),
    ('231', 'production-binding-derived', 9),
    ('232', 'editorial-pipeline-llm-judge', 9),
    ('233', 'worldbuilding-slice2-impl', 9),
    ('234', 'format-driver-pandoc-managed', 9),
    ('235', 'graph-neighbors-typed-paths', 9),
    ('236', 'research-ingest-corpus-management', 9),
    ('237', 'scene-brief-cache-discipline', 9),
    ('238', 'story-time-graph-query', 9),
    ('239', 'dramatica-fragments-derive', 9),
    ('240', 'scene-writer-llm-loop', 9),
    ('241', 'character-knowledge-llm-extract', 9),
    ('242', 'codex-entity-fuzzy-match', 9),
    ('243', 'structure-templates-llm-anchor', 10),
    ('244', 'voice-profiles-llm-derive', 10),
    ('245', 'sensitivity-managed-reader', 10),
    ('246', 'dual-storyform-klein-c-tests', 10),
    ('247', 'canon-locks-managed-approval', 10),
    ('248', 'plural-character-graph-query', 10),
    ('249', 'reveal-discipline-veil-llm', 10),
    ('250', 'project-rulesets-llm-author', 10),
    ('251', 'chapter-briefing-llm-render', 10),
    ('252', 'novel-skill-walks-managed', 10),
    ('253', 'kp-fragments-derive-overlay', 10),
    ('254', 'voice-locked-cache-discipline', 10),
    ('255', 'preflight-skill-derived-metrics', 10),
    ('256', 'anthropic-driver-fallbacks', 11),
    ('257', 'output-prefix-managed-cache', 11),
    ('258', 'dogfood-classifier-quality-loop', 11),
    ('259', 'derived-doc-self-test', 11),
    ('260', 'slash-family-natural-language', 11),
    ('261', 'vision-charter-closing-audit', 11),
    ('262', 'managed-agents-onboarding-cap', 11),
    ('263', 'claude-fable-driver-extras', 11),
    ('264', 'self-improvement-meta-cap', 11),
    ('265', 'plugin-publish-marketplace-shape', 11),
    ('266', 'codemode-execute-error-boundary', 11),
    ('267', 'substrate-vendoring-discipline', 11),
    ('268', 'test-fixture-derivation', 11),
    ('269', 'followup-status-derived-per-spec', 11),
    ('270', 'stop-condition-verification', 11),
    ('271', 'jules-managed-agents-bridge', 12),
    ('272', 'jules-skills-derive', 12),
    ('273', 'central-graph-db-migrations', 12),
    ('274', 'monitor-channel-structured', 12),
    ('275', 'jules-monitor-amendment-loop', 12),
    ('276', 'doctor-welcome-managed-aware', 12),
    ('277', 'dispatch-decision-llm-refine', 12),
    ('278', 'universal-frontmatter-discipline', 11),
]

STUBS = tuple(
    EnhancementSliceStub(spec_id=sid, slug=slug, wave=wave)
    for sid, slug, wave in _CATALOG
)

def catalogue_spec_ids():
    return frozenset(s.spec_id for s in STUBS)
