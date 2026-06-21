"""adr ontology — the WH(Y) Decision node + its typed Schema + dependency edges
(Spec 354).

Reconciliations folded from the spec-panel (2026-06-20) and the
think-hard-about-the-ontology-and-Schema pass (owner directive, 2026-06-20):

- **AdrTheme is NOT a new node label** — a theme is a ``Document`` with
  ``kind="adr-theme"`` + a ``layer`` tag. Only ``Decision`` is genuinely new.

- **Two layers, not one (the key correction).** The node's *required* fields are
  the STORAGE constraint Memory enforces on ``record``; a ``Schema`` is the
  TYPED CONTRACT that powers ``validate`` (CORE.md §"Schemas & templates"). They
  are different:
  - **Node-required (storage):** minimal — ``decision`` (what was decided — the
    record's identity) + ``status``. The five other WH(Y) elements are recordable
    EMPTY, so a ``proposed`` skeleton (Spec 356 ``extract_decisions``) can persist
    and be completed → approved incrementally. WHY-001 is an *approval*-gating
    validation rule, NOT a storage constraint.
  - **The ``decision`` Schema (completeness contract):** a draft-07 schema whose
    ``required`` is the full six WH(Y) elements + ``status`` and whose
    ``properties`` carry the per-element ``maxLength`` budgets (SPEC-001-A; rule 8
    — documented, overridable). ``validate`` DERIVES WHY-001 (required) + WHY-LEN
    (maxLength) from this ONE Schema (rule 2 — no second source).

- The five ported dependency types map to edges: ``DEPENDS_ON``, ``RELATES_TO``,
  ``PART_OF`` (new here); ``REFINES`` (already in the graph via ``discover`` —
  unioned, idempotent); ``SUPERSEDES`` → the core ``SUPERSEDED_BY`` edge (reused
  by ``adr.supersede``, Slice 2).
"""
from __future__ import annotations

from agency.ontology import OntologyExtension

# The SPEC-001-A status set (the `Decision.status` closed enum).
DECISION_STATUS = {
    "proposed", "under-review", "approved", "implemented",
    "superseded", "rejected", "retired", "expired",
}

# The six WH(Y) elements with their SPEC-001-A length budgets (tunable — rule 8).
# This dict is the SINGLE SOURCE for the WH(Y) shape; the Schema below is built
# from it, and `validate` reads the Schema (not this dict) so there is one
# authoritative contract.
_WHY_MAXLEN = {
    "context": 200, "facing": 250, "decision": 150,
    "neglected": 200, "benefits": 250, "tradeoffs": 300,
}

# Node-required (STORAGE): minimal identity — what was decided + its state. The
# rest of the WH(Y) justification is recordable empty (a `proposed` skeleton),
# completeness is gated at approval by `validate` + the DoD gate (355).
_NODE_REQUIRED = ["decision", "status"]

# The `decision` Schema (the COMPLETENESS contract `validate` consumes). draft-07
# so it carries required + per-element maxLength in one typed artefact. `title`
# is the PascalCase ontology label it covers (Spec 153 coverage audit).
DECISION_SCHEMA = {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "title": "Decision",
    "type": "object",
    "required": list(_WHY_MAXLEN) + ["status"],
    "properties": {
        **{elem: {"type": "string", "maxLength": cap}
           for elem, cap in _WHY_MAXLEN.items()},
        "status": {"type": "string", "enum": sorted(DECISION_STATUS)},
    },
}

adr_ontology = OntologyExtension(
    nodes={"Decision": _NODE_REQUIRED},
    # PART_OF (Decision→theme/Spec), DEPENDS_ON / RELATES_TO (Decision↔Decision).
    # REFINES is unioned (already present); SUPERSEDED_BY is core. GATED_BY links a
    # Decision to the DoD-approval Gate it cleared (Spec 355 — traversable audit).
    edges={"PART_OF", "DEPENDS_ON", "RELATES_TO", "REFINES", "GATED_BY"},
    enums={("Decision", "status"): DECISION_STATUS},
    # The typed contract for a Decision artefact (powers validate; covers the
    # `Decision` label for the Spec 153 schema-coverage audit via `title`).
    schemas={"decision": DECISION_SCHEMA},
)
