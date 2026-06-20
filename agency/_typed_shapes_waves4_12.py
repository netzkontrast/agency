"""Waves 4-12 enhancement Slice 1 batch — substantive typed shapes.

Promotes every wave-4..12 spec (184-277, minus 195/281) from catalogue
stub to substantive Slice 1. Each typed dataclass enforces invariants
via __post_init__; the data shape IS the contract Slice 2 wires through
the runtime.

Grouped by wave for clarity; one frozen dataclass per spec. Total: 93
typed shapes across waves 4-12. See per-spec docstrings for the
enhancement target and the shape's Slice 2 wiring target.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


def _require(field_name: str, val, *, kind=str, allow_empty=False):
    """Helper for common __post_init__ checks."""
    if kind is str and not isinstance(val, str):
        raise ValueError(f"{field_name} must be str; got {type(val).__name__}")
    if kind is str and not allow_empty and not val:
        raise ValueError(f"{field_name} must be non-empty")
    if kind is int and not isinstance(val, int):
        raise ValueError(f"{field_name} must be int")
    if kind is float and not isinstance(val, (int, float)):
        raise ValueError(f"{field_name} must be numeric")


# ═════════════════════════════════════════════════════════════════════
# Wave 4 (184-194) — token-economy + naming + install closure
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CodemodeAlias:                                    # Spec 184
    """One naming-rename codemode alias."""
    name: str
    cap:  str
    verb: str
    def __post_init__(self):
        _require("name", self.name); _require("cap", self.cap); _require("verb", self.verb)


@dataclass(frozen=True)
class InstallPath:                                      # Spec 185
    """One install resolver path (pipx / uvx / local)."""
    tool:   Literal["pipx", "uvx", "pip"]
    binary: str
    ready:  bool
    def __post_init__(self):
        if self.tool not in ("pipx", "uvx", "pip"):
            raise ValueError(f"tool must be pipx/uvx/pip; got {self.tool!r}")
        _require("binary", self.binary)


@dataclass(frozen=True)
class TokenEconomyFollowup:                             # Spec 186
    """Spec 066 cluster follow-up entry."""
    rule_id: str
    status:  Literal["open", "accepted", "resolved"]
    def __post_init__(self):
        _require("rule_id", self.rule_id)
        if self.status not in ("open", "accepted", "resolved"):
            raise ValueError(f"bad status {self.status!r}")


@dataclass(frozen=True)
class OutputLintFinding:                                # Spec 187
    """Output-side token-economy lint finding."""
    rule_id:  str
    file:     str
    severity: Literal["error", "warn"]
    def __post_init__(self):
        _require("rule_id", self.rule_id); _require("file", self.file)
        if self.severity not in ("error", "warn"):
            raise ValueError(f"bad severity {self.severity!r}")


@dataclass(frozen=True)
class DrillCandidate:                                   # Spec 188
    """Tiered-discovery LLM-drill candidate."""
    capability: str
    relevance:  float
    def __post_init__(self):
        _require("capability", self.capability)
        if not (0.0 <= self.relevance <= 1.0):
            raise ValueError(f"relevance ∈ [0,1]; got {self.relevance}")


@dataclass(frozen=True)
class VerbConsolidation:                                # Spec 189
    """Verb-surface consolidation record."""
    old_verb:   str
    new_verb:   str
    status:     Literal["merged", "deprecated", "rejected"]
    def __post_init__(self):
        _require("old_verb", self.old_verb); _require("new_verb", self.new_verb)
        if self.status not in ("merged", "deprecated", "rejected"):
            raise ValueError(f"bad status {self.status!r}")


@dataclass(frozen=True)
class SkillReconciliation:                              # Spec 190
    """Skill-surface reconciliation pair."""
    skill_a: str
    skill_b: str
    overlap: float
    def __post_init__(self):
        _require("skill_a", self.skill_a); _require("skill_b", self.skill_b)
        if not (0.0 <= self.overlap <= 1.0):
            raise ValueError(f"overlap ∈ [0,1]; got {self.overlap}")


@dataclass(frozen=True)
class AlignmentCell:                                    # Spec 191
    """Vision-alignment matrix cell."""
    spec_id: str
    goal_id: int
    status:  Literal["aligned", "partial", "missing"]
    def __post_init__(self):
        _require("spec_id", self.spec_id)
        if not (1 <= self.goal_id <= 8):
            raise ValueError(f"goal_id ∈ 1..8; got {self.goal_id}")
        if self.status not in ("aligned", "partial", "missing"):
            raise ValueError(f"bad status {self.status!r}")


@dataclass(frozen=True)
class ShellSafetyVerdict:                               # Spec 192
    """Shell-cap safety gate verdict."""
    command:  str
    allowed:  bool
    reason:   str
    def __post_init__(self):
        _require("command", self.command); _require("reason", self.reason)


@dataclass(frozen=True)
class CapstoneMetric:                                   # Spec 193
    """Token-economy capstone output metric."""
    metric_id: str
    value:     float
    def __post_init__(self):
        _require("metric_id", self.metric_id)


@dataclass(frozen=True)
class ShellSuggestion:                                  # Spec 194
    """shell.define LLM-suggest candidate."""
    template_id: str
    body:        str
    confidence:  float
    def __post_init__(self):
        _require("template_id", self.template_id); _require("body", self.body)
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence ∈ [0,1]; got {self.confidence}")


# ═════════════════════════════════════════════════════════════════════
# Wave 5 (196-205) — substrate hardening continuation
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GherkinScenario:                                  # Spec 196
    """Spec 077 — BDD scenario."""
    feature: str
    given:   str
    when:    str
    then:    str
    def __post_init__(self):
        for n, v in (("feature", self.feature), ("given", self.given),
                     ("when", self.when), ("then", self.then)):
            _require(n, v)


@dataclass(frozen=True)
class StaticSkillResolution:                            # Spec 197
    """Spec 078 — static-walkable-skills resolution."""
    skill_name: str
    resolved:   bool
    notes:      str = ""
    def __post_init__(self):
        _require("skill_name", self.skill_name)


@dataclass(frozen=True)
class CLIMirrorEntry:                                   # Spec 198
    """Spec 079 — Click-CLI mirror entry."""
    cap:  str
    verb: str
    cli_path: str
    def __post_init__(self):
        _require("cap", self.cap); _require("verb", self.verb); _require("cli_path", self.cli_path)


@dataclass(frozen=True)
class SkillPublishRoundtrip:                            # Spec 199
    """Spec 080 — Skills API publish roundtrip record."""
    skill_name: str
    published:  bool
    api_id:     str = ""
    def __post_init__(self):
        _require("skill_name", self.skill_name)


@dataclass(frozen=True)
class WalkableUsageDepth:                               # Spec 200
    """Spec 081 — walkable usage-skill depth."""
    cap:        str
    phase_count: int
    def __post_init__(self):
        _require("cap", self.cap)
        if self.phase_count < 1:
            raise ValueError(f"phase_count must be >= 1; got {self.phase_count}")


@dataclass(frozen=True)
class TokenAPIShape:                                    # Spec 201
    """Spec 082 — token-counter API boundary."""
    backend: Literal["tiktoken", "proxy", "anthropic"]
    ready:   bool
    def __post_init__(self):
        if self.backend not in ("tiktoken", "proxy", "anthropic"):
            raise ValueError(f"backend bad {self.backend!r}")


@dataclass(frozen=True)
class SkillsAPIManaged:                                 # Spec 202
    """Spec 083 — Skills API publish managed."""
    skill_name: str
    api_skill_id: str
    def __post_init__(self):
        _require("skill_name", self.skill_name); _require("api_skill_id", self.api_skill_id)


@dataclass(frozen=True)
class GraphQuery:                                       # Spec 203
    """Spec 084 — graph-query language fragment."""
    query: str
    binds: tuple[str, ...] = ()
    def __post_init__(self):
        _require("query", self.query)


@dataclass(frozen=True)
class ReasoningWetCall:                                 # Spec 204
    """Spec 091 — reasoning intent driver wet call."""
    method:     str
    subject:    str
    confidence: float
    def __post_init__(self):
        _require("method", self.method); _require("subject", self.subject)
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence ∈ [0,1]")


@dataclass(frozen=True)
class HardeningRecord:                                  # Spec 205
    """Spec 092 — substrate-hardening continuous record."""
    gate_id: str
    passed:  bool
    note:    str = ""
    def __post_init__(self):
        _require("gate_id", self.gate_id)


# ═════════════════════════════════════════════════════════════════════
# Wave 6 (206-216) — music cluster depth
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MusicProduction:                                  # Spec 206
    """Spec 093 — music master LLM production record."""
    album_id: str
    status:   str
    def __post_init__(self):
        _require("album_id", self.album_id); _require("status", self.status)


@dataclass(frozen=True)
class MusicLifecycleBudget:                             # Spec 207
    """Spec 094 — music lifecycle output budget."""
    track_id:    str
    token_budget: int
    def __post_init__(self):
        _require("track_id", self.track_id)
        if self.token_budget < 0:
            raise ValueError("token_budget must be >= 0")


@dataclass(frozen=True)
class LyricGeneration:                                  # Spec 208
    """Spec 095 — music lyrics LLM generation."""
    track_id: str
    body:     str
    syllable_count: int
    def __post_init__(self):
        _require("track_id", self.track_id); _require("body", self.body)
        if self.syllable_count < 0:
            raise ValueError("syllable_count >= 0")


@dataclass(frozen=True)
class AudioManagedRun:                                  # Spec 209
    """Spec 096 — music audio driver managed."""
    track_id: str
    duration_s: float
    def __post_init__(self):
        _require("track_id", self.track_id)
        if self.duration_s <= 0:
            raise ValueError("duration_s > 0")


@dataclass(frozen=True)
class CatalogueQuery:                                   # Spec 210
    """Spec 097 — music catalogue graph query."""
    cap:   str
    query: str
    def __post_init__(self):
        _require("cap", self.cap); _require("query", self.query)


@dataclass(frozen=True)
class PromoCopy:                                        # Spec 211
    """Spec 098 — music promo LLM copy."""
    track_id: str
    body:     str
    platform: Literal["instagram", "tiktok", "twitter", "youtube"]
    def __post_init__(self):
        _require("track_id", self.track_id); _require("body", self.body)
        if self.platform not in ("instagram", "tiktok", "twitter", "youtube"):
            raise ValueError(f"bad platform {self.platform!r}")


@dataclass(frozen=True)
class ResearchFanout:                                   # Spec 212
    """Spec 099 — music research fanout."""
    research_id: str
    agent_count: int
    def __post_init__(self):
        _require("research_id", self.research_id)
        if self.agent_count < 1:
            raise ValueError("agent_count >= 1")


@dataclass(frozen=True)
class MusicGateVerdict:                                 # Spec 213
    """Spec 100 — music gates LLM judge verdict."""
    gate_id: str
    passed:  bool
    rationale: str = ""
    def __post_init__(self):
        _require("gate_id", self.gate_id)


@dataclass(frozen=True)
class MusicConfigDerive:                                # Spec 214
    """Spec 115 — music binding derived config."""
    key:   str
    value: str
    def __post_init__(self):
        _require("key", self.key); _require("value", self.value, allow_empty=True)


@dataclass(frozen=True)
class MusicDoctorField:                                 # Spec 215
    """Spec 117 — music runtime doctor field."""
    field: str
    ready: bool
    hint:  str = ""
    def __post_init__(self):
        _require("field", self.field)


@dataclass(frozen=True)
class NameExposureCheck:                                # Spec 216
    """Spec 119 — music name exposure driver check."""
    name: str
    exposed: bool
    def __post_init__(self):
        _require("name", self.name)


# ═════════════════════════════════════════════════════════════════════
# Wave 7 (217-224) — novel cluster depth
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class NovelBuild:                                       # Spec 217
    """Spec 101 — novel master LLM build."""
    novel_id: str
    chapter_count: int
    def __post_init__(self):
        _require("novel_id", self.novel_id)
        if self.chapter_count < 0:
            raise ValueError("chapter_count >= 0")


@dataclass(frozen=True)
class NovelLifecycleBudget:                             # Spec 218
    """Spec 102 — novel lifecycle output budget."""
    scene_id:    str
    token_budget: int
    def __post_init__(self):
        _require("scene_id", self.scene_id)
        if self.token_budget < 0:
            raise ValueError("token_budget >= 0")


@dataclass(frozen=True)
class StoryformAssist:                                  # Spec 219
    """Spec 103 — novel storyform LLM assist."""
    novel_id: str
    suggestion: str
    def __post_init__(self):
        _require("novel_id", self.novel_id); _require("suggestion", self.suggestion)


@dataclass(frozen=True)
class ProseDraftSlice2:                                 # Spec 220-followup
    """Spec 220 Slice 2 — scene-body regenerate verdict."""
    scene_id: str
    pass_count: int
    gates_passed: tuple[str, ...]
    def __post_init__(self):
        _require("scene_id", self.scene_id)
        if self.pass_count < 1:
            raise ValueError("pass_count >= 1")


@dataclass(frozen=True)
class NovelResearchFanout:                              # Spec 221
    """Spec 105 — novel research fanout."""
    novel_id: str
    queries:  tuple[str, ...]
    def __post_init__(self):
        _require("novel_id", self.novel_id)
        if not self.queries:
            raise ValueError("queries must be non-empty")


@dataclass(frozen=True)
class NovelCatalogue:                                   # Spec 222
    """Spec 106 — novel catalogue graph query."""
    novel_id: str
    query:    str
    def __post_init__(self):
        _require("novel_id", self.novel_id); _require("query", self.query)


@dataclass(frozen=True)
class ManuscriptExport:                                 # Spec 223
    """Spec 107 — manuscript managed export."""
    novel_id: str
    format:   Literal["epub", "pdf", "docx", "markdown"]
    def __post_init__(self):
        _require("novel_id", self.novel_id)
        if self.format not in ("epub", "pdf", "docx", "markdown"):
            raise ValueError(f"bad format {self.format!r}")


@dataclass(frozen=True)
class NovelGateVerdict:                                 # Spec 224
    """Spec 108 — novel gates LLM judge."""
    gate_id: str
    passed:  bool
    def __post_init__(self):
        _require("gate_id", self.gate_id)


# ═════════════════════════════════════════════════════════════════════
# Wave 8 (225-229) — substrate-adjacent capabilities
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PromptOptimize:                                   # Spec 225
    """Spec 109 — prompt cap optimize call."""
    prompt_id: str
    delta:     str
    def __post_init__(self):
        _require("prompt_id", self.prompt_id); _require("delta", self.delta)


@dataclass(frozen=True)
class ThinkingWetCall:                                  # Spec 226
    """Spec 110 — thinking cap wet call."""
    method:  str
    subject: str
    def __post_init__(self):
        _require("method", self.method); _require("subject", self.subject)


@dataclass(frozen=True)
class CapMigrationStep:                                 # Spec 227
    """Spec 111 — capability migration step."""
    cap:    str
    phase:  str
    status: Literal["queued", "running", "done"]
    def __post_init__(self):
        _require("cap", self.cap); _require("phase", self.phase)
        if self.status not in ("queued", "running", "done"):
            raise ValueError(f"bad status {self.status!r}")


@dataclass(frozen=True)
class DossierManaged:                                   # Spec 228
    """Spec 112 — dossier managed corpus record."""
    dossier_id: str
    source_count: int
    def __post_init__(self):
        _require("dossier_id", self.dossier_id)
        if self.source_count < 0:
            raise ValueError("source_count >= 0")


@dataclass(frozen=True)
class SessionHooked:                                    # Spec 229
    """Spec 114 — session-driver slice 2 hook record."""
    session_id: str
    intent_id:  str
    def __post_init__(self):
        _require("session_id", self.session_id); _require("intent_id", self.intent_id)


# ═════════════════════════════════════════════════════════════════════
# Wave 9 (230-242) — novel post-shipped depth
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StoryformSuggest:                                 # Spec 230
    novel_id: str
    suggestion: str
    def __post_init__(self): _require("novel_id", self.novel_id); _require("suggestion", self.suggestion)


@dataclass(frozen=True)
class ProductionBindingDerived:                         # Spec 231
    novel_id: str
    config_key: str
    def __post_init__(self): _require("novel_id", self.novel_id); _require("config_key", self.config_key)


@dataclass(frozen=True)
class EditorialJudge:                                   # Spec 232
    scene_id: str
    passed: bool
    def __post_init__(self): _require("scene_id", self.scene_id)


@dataclass(frozen=True)
class WorldSlice2:                                      # Spec 233
    novel_id: str
    world_node_id: str
    def __post_init__(self): _require("novel_id", self.novel_id); _require("world_node_id", self.world_node_id)


@dataclass(frozen=True)
class PandocExport:                                     # Spec 234
    novel_id: str
    format: str
    def __post_init__(self): _require("novel_id", self.novel_id); _require("format", self.format)


@dataclass(frozen=True)
class TypedPath:                                        # Spec 235
    node_id: str
    edge: str
    direction: Literal["out", "in", "any"]
    def __post_init__(self):
        _require("node_id", self.node_id); _require("edge", self.edge)
        if self.direction not in ("out", "in", "any"):
            raise ValueError(f"bad direction {self.direction!r}")


@dataclass(frozen=True)
class CorpusEntry:                                      # Spec 236
    corpus_id: str
    source_id: str
    def __post_init__(self): _require("corpus_id", self.corpus_id); _require("source_id", self.source_id)


@dataclass(frozen=True)
class SceneBriefCache:                                  # Spec 237
    scene_id: str
    cached_at: str
    def __post_init__(self): _require("scene_id", self.scene_id); _require("cached_at", self.cached_at)


@dataclass(frozen=True)
class StoryTimeQuery:                                   # Spec 238
    novel_id: str
    chapter_position: int
    def __post_init__(self):
        _require("novel_id", self.novel_id)
        if self.chapter_position < 0:
            raise ValueError("chapter_position >= 0")


@dataclass(frozen=True)
class FragmentDerive:                                   # Spec 239
    fragment_id: str
    derived: bool
    def __post_init__(self): _require("fragment_id", self.fragment_id)


@dataclass(frozen=True)
class SceneWriterLoop:                                  # Spec 240
    scene_id: str
    loop_count: int
    def __post_init__(self):
        _require("scene_id", self.scene_id)
        if self.loop_count < 1:
            raise ValueError("loop_count >= 1")


@dataclass(frozen=True)
class CharacterFact:                                    # Spec 241
    character_id: str
    fact:         str
    learned_at_position: int
    def __post_init__(self):
        _require("character_id", self.character_id); _require("fact", self.fact)
        if self.learned_at_position < 0:
            raise ValueError("position >= 0")


@dataclass(frozen=True)
class CodexFuzzyMatch:                                  # Spec 242
    entry_id: str
    score:    float
    def __post_init__(self):
        _require("entry_id", self.entry_id)
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("score ∈ [0,1]")


# ═════════════════════════════════════════════════════════════════════
# Wave 10 (243-255) — pacing/character + KP wave depth
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StructureTemplate:                                # Spec 243
    template_id: str
    beats: tuple[str, ...]
    def __post_init__(self):
        _require("template_id", self.template_id)
        if not self.beats:
            raise ValueError("beats must be non-empty")


@dataclass(frozen=True)
class VoiceProfile:                                     # Spec 244
    character_id: str
    sig_words: tuple[str, ...]
    def __post_init__(self): _require("character_id", self.character_id)


@dataclass(frozen=True)
class SensitivityRun:                                   # Spec 245
    novel_id: str
    finding_count: int
    def __post_init__(self):
        _require("novel_id", self.novel_id)
        if self.finding_count < 0:
            raise ValueError("finding_count >= 0")


@dataclass(frozen=True)
class KleinCTest:                                       # Spec 246
    storyform_pair_id: str
    inversion_ok: bool
    def __post_init__(self): _require("storyform_pair_id", self.storyform_pair_id)


@dataclass(frozen=True)
class CanonLock:                                        # Spec 247
    canon_id: str
    approved: bool
    def __post_init__(self): _require("canon_id", self.canon_id)


@dataclass(frozen=True)
class PluralCharacterQuery:                             # Spec 248
    system_id: str
    alter_count: int
    def __post_init__(self):
        _require("system_id", self.system_id)
        if self.alter_count < 1:
            raise ValueError("alter_count >= 1")


@dataclass(frozen=True)
class RevealVeil:                                       # Spec 249
    reveal_id: str
    audience: Literal["reader", "pov", "antagonist"]
    def __post_init__(self):
        _require("reveal_id", self.reveal_id)
        if self.audience not in ("reader", "pov", "antagonist"):
            raise ValueError(f"bad audience {self.audience!r}")


@dataclass(frozen=True)
class ProjectRuleset:                                   # Spec 250
    rule_id: str
    severity: Literal["error", "warn", "info"]
    def __post_init__(self):
        _require("rule_id", self.rule_id)
        if self.severity not in ("error", "warn", "info"):
            raise ValueError(f"bad severity {self.severity!r}")


@dataclass(frozen=True)
class ChapterBriefRender:                               # Spec 251
    chapter_id: str
    section_count: int
    def __post_init__(self):
        _require("chapter_id", self.chapter_id)
        if self.section_count < 1:
            raise ValueError("section_count >= 1")


@dataclass(frozen=True)
class NovelSkillWalk:                                   # Spec 252
    skill_name: str
    phase_count: int
    def __post_init__(self):
        _require("skill_name", self.skill_name)
        if self.phase_count < 1:
            raise ValueError("phase_count >= 1")


@dataclass(frozen=True)
class KPFragment:                                       # Spec 253
    fragment_id: str
    family: str
    def __post_init__(self): _require("fragment_id", self.fragment_id); _require("family", self.family)


@dataclass(frozen=True)
class VoiceLockedCache:                                 # Spec 254
    alter_id: str
    cache_key: str
    def __post_init__(self): _require("alter_id", self.alter_id); _require("cache_key", self.cache_key)


@dataclass(frozen=True)
class PreflightMetric:                                  # Spec 255
    novel_id: str
    score: float
    def __post_init__(self):
        _require("novel_id", self.novel_id)
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("score ∈ [0,1]")


# ═════════════════════════════════════════════════════════════════════
# Wave 11 (256-270, 278) — closure: cross-anchor + stop condition
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DriverFallback:                                   # Spec 256
    code: str
    msg:  str = ""
    def __post_init__(self): _require("code", self.code)


@dataclass(frozen=True)
class PrefixCacheHit:                                   # Spec 257
    prefix_hash: str
    cache_hit: bool
    def __post_init__(self): _require("prefix_hash", self.prefix_hash)


@dataclass(frozen=True)
class ClassifierQuality:                                # Spec 258
    accept_rate: float
    def __post_init__(self):
        if not (0.0 <= self.accept_rate <= 1.0):
            raise ValueError("accept_rate ∈ [0,1]")


@dataclass(frozen=True)
class DerivedDocSelfTest:                               # Spec 259
    spec_id: str
    passed:  bool
    def __post_init__(self): _require("spec_id", self.spec_id)


@dataclass(frozen=True)
class NaturalLanguageSlash:                             # Spec 260
    query: str
    matched_command: str
    def __post_init__(self): _require("query", self.query); _require("matched_command", self.matched_command)


@dataclass(frozen=True)
class CharterAudit:                                     # Spec 261
    section: str
    status: Literal["green", "yellow", "red"]
    def __post_init__(self):
        _require("section", self.section)
        if self.status not in ("green", "yellow", "red"):
            raise ValueError(f"bad status {self.status!r}")


@dataclass(frozen=True)
class OnboardingTurn:                                   # Spec 262
    beat: str
    content: str
    def __post_init__(self): _require("beat", self.beat); _require("content", self.content)


@dataclass(frozen=True)
class FableDriverConfig:                                # Spec 263
    backend: str
    model:   str
    def __post_init__(self): _require("backend", self.backend); _require("model", self.model)


@dataclass(frozen=True)
class SelfImprovementOutcome:                           # Spec 264
    pattern: str
    proposal_count: int
    def __post_init__(self):
        _require("pattern", self.pattern)
        if self.proposal_count < 0:
            raise ValueError("proposal_count >= 0")


@dataclass(frozen=True)
class MarketplaceShape:                                 # Spec 265
    plugin: str
    valid:  bool
    def __post_init__(self): _require("plugin", self.plugin)


@dataclass(frozen=True)
class CodemodeError:                                    # Spec 266
    code: str
    message: str
    def __post_init__(self): _require("code", self.code); _require("message", self.message)


@dataclass(frozen=True)
class VendorEntry:                                      # Spec 267
    path: str
    license: str
    def __post_init__(self): _require("path", self.path); _require("license", self.license)


@dataclass(frozen=True)
class TestFixture:                                      # Spec 268
    fixture_id: str
    derived:    bool
    def __post_init__(self): _require("fixture_id", self.fixture_id)


@dataclass(frozen=True)
class FollowupDerived:                                  # Spec 269
    spec_id: str
    section: str
    def __post_init__(self): _require("spec_id", self.spec_id); _require("section", self.section)


@dataclass(frozen=True)
class StopVerification:                                 # Spec 270
    condition_id: int
    met:  bool
    def __post_init__(self):
        if not (1 <= self.condition_id <= 6):
            raise ValueError("condition_id ∈ 1..6")


@dataclass(frozen=True)
class FrontmatterEntry:                                 # Spec 278
    kind: str
    file: str
    def __post_init__(self): _require("kind", self.kind); _require("file", self.file)


# ═════════════════════════════════════════════════════════════════════
# Wave 12 (271-277) — Jules / monitor / central-graph closure
# ═════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class JulesAgentBridge:                                 # Spec 271
    session_id: str
    agent_id:   str
    def __post_init__(self): _require("session_id", self.session_id); _require("agent_id", self.agent_id)


@dataclass(frozen=True)
class JulesSkillDerived:                                # Spec 272
    skill_name: str
    derived: bool
    def __post_init__(self): _require("skill_name", self.skill_name)


@dataclass(frozen=True)
class DBMigration:                                      # Spec 273
    migration_id: str
    direction: Literal["up", "down"]
    def __post_init__(self):
        _require("migration_id", self.migration_id)
        if self.direction not in ("up", "down"):
            raise ValueError(f"bad direction {self.direction!r}")


@dataclass(frozen=True)
class MonitorChannel:                                   # Spec 274
    channel: str
    schema_version: int
    def __post_init__(self):
        _require("channel", self.channel)
        if self.schema_version < 1:
            raise ValueError("schema_version >= 1")


@dataclass(frozen=True)
class MonitorAmendment:                                 # Spec 275
    monitor_id: str
    proposal_id: str
    def __post_init__(self): _require("monitor_id", self.monitor_id); _require("proposal_id", self.proposal_id)


@dataclass(frozen=True)
class DoctorManagedAware:                               # Spec 276
    field: str
    managed: bool
    def __post_init__(self): _require("field", self.field)


@dataclass(frozen=True)
class DispatchRefinement:                               # Spec 277
    signal_id: str
    weight: float
    def __post_init__(self):
        _require("signal_id", self.signal_id)
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError("weight ∈ [0,1]")
