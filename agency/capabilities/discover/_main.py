# agency-scaffold: v1
"""discover — guided intent discovery (Spec 307 program · 308 scaffold).

Use when: a fresh or vague intent needs guided discovery BEFORE work begins —
an underspecified ask, a missing acceptance test, a "not sure what I want yet".
The capability turns a one-sentence seed into a grounded, clarity-gated,
confirmed Intent by interleaving research-grounding with AskUser elicitation.
Triggers:
- An underspecified ask arrives and the WHY is captured, not discovered
- An intent has no measurable acceptance criteria yet
- Work is about to start against an unconfirmed or ungrounded intent
Red flags:
- Starting work against an unconfirmed intent → run ``discover.interview`` first
- Inventing AskUser options instead of deriving them from evidence → ``discover.ground``
- Treating a one-line seed as a finished intent → walk ``guided-discovery``

Spec 308 is the SCAFFOLD: it lands the package, the consolidated ontology
(Spec 307's locked node/edge/enum/schema surface), this docstring-derived
SkillDoc, and the derived ``discover-usage`` walkable — an empty-but-discoverable
capability the 17 children (309-325) fill in. The only behaviour here is the
``status`` smoke verb; ``discover.interview`` (Spec 309) becomes the real entry.
"""
from __future__ import annotations

from agency.capability import CapabilityBase, verb
from agency.toolresult import ToolResult

from .clusters import (AskCluster, ClarifyCluster, DiscoverCluster,
                       InterviewCluster, RefineCluster, ScopeCluster)
from .ontology import discover_ontology


class DiscoverCapability(InterviewCluster, AskCluster, ClarifyCluster,
                         RefineCluster, ScopeCluster, DiscoverCluster,
                         CapabilityBase):
    name = "discover"
    # Intent-pillar peer to ``prompt``. Spec 291 re-homes the intent pillar to
    # ``home="intent"``; until that reorg lands, ``capability`` keeps the cap on
    # the current loader path (Spec 308 Followup open question — default: ship
    # now, re-home with 291).
    home = "capability"
    ontology = discover_ontology

    @verb(role="transform")
    def status(self) -> ToolResult:
        """Smoke verb — report the registered ``discover`` ontology surface.

        Proves the capability is wired and its ontology registered (Spec 308
        acceptance). Pure introspection — records nothing. Removed/absorbed once
        ``discover.interview`` (Spec 309) lands as the real entry point.

        Inputs: (none).
        Returns: ``{nodes, edges, enums, schemas}`` — the locked Spec 307 surface
                 this capability registers.
        chain_next: ``discover.interview`` (Spec 309 — not yet shipped).
        """
        return ToolResult.success(data={
            "nodes": sorted(discover_ontology.nodes),
            "edges": sorted(discover_ontology.edges),
            "enums": sorted(f"{label}.{field}"
                            for (label, field) in discover_ontology.enums),
            "schemas": sorted(discover_ontology.schemas),
        })
