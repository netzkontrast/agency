# agency-scaffold: v1
# agency-accept-warn: surface_size — Spec 109 ships 9 founding verbs (research-dossier + engineering lineages); Spec 129 adds 3 fragment verbs (fragment/fragments_for/register_fragment) for the Dramatica-as-prompts substrate; Spec 127 adds assemble_scene_brief for graph-driven brief assembly. 13 total > 12 budget by design — each verb pulls a distinct primitive; consolidating would re-grow the function signatures (kw-arg explosion). Tier discovery via Spec 068 not warranted while the cluster is still landing.
"""prompt — prompt-engineering capability (Spec 109 Slice 1).

Two-lineage capability:

1. **Research-dossier lineage**: intent_capture → catalog_list → brief_render
   → brief_audit → brief_finalize. Produces dossier-shaped research
   deliverables.
2. **Prompt-engineering lineage**: engineer (renders a PromptInstance inside
   a token budget) + audit (general-case reader-test simulation) +
   token_budget_gate (composite gate verb).

Slice 1 ships 7 user verbs + 1 gate verb + 2 walkable skills + 2
templates. Slice 2 adds the 7 builder/optimizer/variant verbs + 3 more
skills + the bundled module catalog YAML.

Use when: authoring research dossiers, engineering structured prompts that honor a token budget, auditing prompts for clarity / anti-patterns.
Triggers:
- A research intent needs a dossier authored before generation begins
- A prompt is being constructed and needs token-budget gating
- An LLM output flagged for anti-patterns needs an optimization pass
Red flags:
- Hand-rolling prompts outside the engineering pipeline → call `prompt.engineer`
- Skipping the audit gate → call `prompt.audit` (general-case) or `prompt.brief_audit` (dossier-case)
"""
from __future__ import annotations

from agency.capability import CapabilityBase, RenderTemplates, verb  # noqa: F401

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


class PromptCapability(
    DossierMixin,
    EngineeringMixin,
    GatesMixin,
    AssemblyMixin,
    FragmentsMixin,
    PromptBase,
    CapabilityBase,
):
    name = "prompt"
    home = "capability"
    ontology = prompt_ontology
    render_templates = RenderTemplates.from_module(__file__)
