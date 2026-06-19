# agency-scaffold: v1
"""dogfood — graph-native observation ledgers (Spec 017).

Dogfood keeps observation ledgers graph-native: notes recorded as nodes, exported and imported as JSON preserving ids and validity windows, and rendered to markdown on demand.

Use when: recording or rendering observation ledgers in the graph — capturing a development note, exporting the graph for merge-recovery, or importing it back.
Triggers:
- An insight from a dev session worth keeping
- A graph that must survive a container or merge boundary
- A ledger that should render to markdown on demand
Red flags:
- Writing a markdown ledger by hand → record it via capability_dogfood_note
- Losing graph state across a container → capability_dogfood_export the graph
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, RenderTemplates, verb  # noqa: F401
from ...ontology import OntologyExtension

# Spec 286 P3 — the verb surface is split across cluster mixins (one file per
# cluster under ``clusters/``); the helper functions + module constants those
# verbs use live alongside their owning cluster. Re-exported here so any
# external import of ``dogfood._main.<symbol>`` keeps working (back-compat).
from .clusters._base import DogfoodBase  # noqa: F401
from .clusters.observe import (  # noqa: F401
    ObserveMixin,
    _HEADER_RE,
    _clean_title,
    _count_tokens,
    _parse_observations,
)
from .clusters.portage import (  # noqa: F401
    PortageMixin,
    _EXPORT_VERSION,
)
from .clusters.session import (  # noqa: F401
    SessionMixin,
)
from .clusters.amendment import (  # noqa: F401
    AmendmentMixin,
    _CLASSIFIER_RULES,
    _CLASSIFIER_SYSTEM,
    _LLM_OPS,
    _LLM_SECTIONS,
    _PROPOSAL_LIST_SCHEMA,
    _build_classifier_messages,
    _classify_reflection,
    _parse_llm_proposals,
    _payload_hash,
    _reflection_payload_for_llm,
    _render_unified_diff,
    _resolve_spec_path,
    _spec_id_from_slug,
)
from .clusters.lifecycle import (  # noqa: F401
    LifecycleMixin,
    _archive_path_for,
    _list_plan_dirs,
    _read_frontmatter,
)


# Spec 286 P3 — DogfoodCapability composes the cluster mixins into ONE
# registered ``dogfood`` capability. Mixins FIRST, CapabilityBase LAST so the
# base resolvers (ctx, etc.) sit at the end of the MRO and DogfoodBase's
# overrides win. ``CapabilityBase.as_capability`` walks the full MRO, so every
# mixin's @verb methods are discovered — same verb-name set + count as before.
# The class stays defined in ``_main`` so the DERIVED skill_doc keeps reading
# this module's docstring (Spec 080).
class DogfoodCapability(
    ObserveMixin,
    PortageMixin,
    SessionMixin,
    AmendmentMixin,
    LifecycleMixin,
    DogfoodBase,
    CapabilityBase,
):
    name = "dogfood"
    home = "memory"
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    # Spec 114 — session-tracking ontology: DecisionRecord binds decisions to
    # a session; BoundaryUse records a raw-tool invocation so future sessions
    # can detect "should have called a capability verb" patterns.
    ontology = OntologyExtension(
        nodes={
            # `rationale` required for grounded decisions; `next_action`
            # optional. SessionLifecycle linkage via RELATES_TO when known.
            "DecisionRecord": ["subject", "decision", "rationale"],
            # Spec 195 Slice 1 — BoundaryUse carries the raw-tool
            # bypass info: `tool` (Write/Edit/Bash), `argument_summary`
            # (trimmed), `target` (full path/command), `verb_shadow`
            # (the capability verb that SHOULD have served the same
            # intent), `intent_id` (SERVES which Intent), `session`.
            "BoundaryUse":    ["tool", "argument_summary"],
            # Spec 150 — amendment-proposal provenance: every accepted
            # amendment writes an `Artefact(kind="amendment-proposal")`
            # with PRODUCES_FROM edges to every cited Reflection so a
            # reviewer can trace any amendment back to its sources.
            "Artefact":       ["kind"],
        },
        # PRODUCES_FROM: amendment → cited Reflection
        # RECORDED_BY: Spec 195 — BoundaryUse → originating Event
        edges={"RELATES_TO", "PRODUCES_FROM", "RECORDED_BY"},
    )
