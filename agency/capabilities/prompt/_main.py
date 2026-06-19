# agency-scaffold: v1
# agency-accept-warn: surface_size — Spec 109 ships 9 founding verbs (research-dossier + engineering lineages); Spec 129 adds 3 fragment verbs (fragment/fragments_for/register_fragment) for the Dramatica-as-prompts substrate; Spec 127 adds assemble_scene_brief for graph-driven brief assembly; Spec 304 adds 3 framework verbs (framework/frameworks_for/register_framework) for the 27-framework library; Spec 305 adds 3 (route_framework/render/evaluate) for token-efficient routing + template render + goal-aware evaluation. 19 total > 12 budget by design — each verb pulls a distinct primitive; consolidating would re-grow the function signatures (kw-arg explosion). Tier discovery via Spec 068 not warranted while the cluster is still landing.
"""prompt — prompt-engineering substrate (Spec 109 · 129 · 304-306).

Author research dossiers, engineer token-budgeted prompts, route a draft to the
right one of 27 research-backed frameworks, and score prompts — and agency's own
functional docs — for clarity and anti-patterns. The prompt-as-substrate spine
where templates, the framework library, and evaluation meet.

Three lineages on one capability:

1. **Research-dossier**: intent_capture → catalog_list → brief_render →
   brief_audit → brief_finalize — dossier-shaped research deliverables.
2. **Prompt-engineering**: engineer (token-budgeted PromptInstance) +
   audit / evaluate (clarity + anti-pattern scoring) + token_budget_gate.
3. **Framework library (Spec 304-306)**: framework / frameworks_for /
   route_framework / render over the 27-framework library + the functional
   family (skilldoc / tool-desc / template) for agency's own documentation.

Use when: authoring a research dossier, engineering a token-budgeted prompt,
picking the right framework for a goal (route_framework), or scoring a prompt or
functional doc for clarity / anti-patterns (evaluate).
Triggers:
- A research intent needs a dossier authored before generation begins
- A draft prompt needs the right framework picked, then filled to a token budget
- A prompt or a capability's own doc needs clarity / anti-pattern scoring
Red flags:
- Hand-rolling a prompt instead of routing → call `prompt.route_framework` then `prompt.render`
- Reading all 27 frameworks to pick one → `prompt.route_framework` returns the one
- Skipping the score gate → `prompt.evaluate` (or `prompt.audit` for the legacy contract)
- Adding a Role to a function's doc → that is `role_padding`; functions need actionable insight, not a persona
"""
from __future__ import annotations

from agency.capability import ArtefactSchemas, CapabilityBase, RenderTemplates, verb  # noqa: F401

from .ontology import prompt_ontology

# ─────────────────────────── capability ───────────────────────────
# Spec 286 P3 — the verb surface is split across cluster mixins (one file per
# section grouping under ``clusters/``); PromptCapability composes them into
# ONE registered ``prompt`` capability. Mixins FIRST, CapabilityBase LAST so
# the base resolvers (ctx) sit at the end of the MRO and PromptBase anchors the
# shared (driver-less) chain. ``CapabilityBase.as_capability`` walks the full
# MRO, so every mixin's @verb methods are discovered — same verb-name set +
# count as before.
from .clusters import (
    PromptBase,
    DossierMixin,
    EngineeringMixin,
    GatesMixin,
    AssemblyMixin,
    FragmentsMixin,
    FrameworksMixin,
)

# ─── Re-exports for back-compat (symbols imported elsewhere or test-referenced) ───
# Spec 286 P3 — these moved into cluster modules; re-export from ``_main`` so
# ``from agency.capabilities.prompt._main import _load_fragments`` (and the
# scoring/token helpers + tunable budgets) keep resolving.
from .clusters._base import (  # noqa: F401
    _CHARS_PER_TOKEN,
    _CLARITY_PENALTY_NO_CONSTRAINTS,
    _CLARITY_PENALTY_OVER_BUDGET,
    _CLARITY_PENALTY_VAGUE,
    _DEFAULT_AUDIT_MIN_SCORE,
    _DEFAULT_TOKEN_BUDGET,
    _VAGUE_WORDS,
    _approx_tokens,
    _score_brief,
)
from .clusters.dossier import _SEED_CATALOG  # noqa: F401
from .clusters.fragments import (  # noqa: F401
    _DEFAULT_OVERLAY_PATH,
    _FRAGMENTS_FILE,
    _load_fragments,
    _load_overlay,
    _resolve_to_canonical,
    _throughline_slug,
    _write_overlay_fragment,
)
from .clusters.assembly import (  # noqa: F401
    _BriefContext,
    _SECTION_TITLES,
    _ncp_to_scope,
    _render_brief,
    _truncate_to_tokens,
)
from .clusters.frameworks import (  # noqa: F401
    _DEFAULT_FW_OVERLAY_PATH,
    _FRAMEWORKS_FILE,
    _load_frameworks,
    _load_intent_signals,
)


class PromptCapability(
    DossierMixin,
    EngineeringMixin,
    GatesMixin,
    AssemblyMixin,
    FragmentsMixin,
    FrameworksMixin,
    PromptBase,
    CapabilityBase,
):
    name = "prompt"
    home = "capability"
    ontology = prompt_ontology
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
