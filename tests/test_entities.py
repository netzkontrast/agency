"""Spec 289 Slice 1 — SQLModel entity models derived from the graph ontology.

The derived models are the typed surface; validation has parity with
`Ontology.violations` (the established schema semantics) so wiring it into
`Memory` later is behaviour-preserving.
"""
from __future__ import annotations

import pytest
from sqlmodel import SQLModel

from agency._entities import EntityModels


def test_a_model_is_derived_for_every_ontology_label(engine):
    em = EntityModels(engine.ontology)
    for label in engine.ontology.nodes:
        m = em.model_for(label)
        assert issubclass(m, SQLModel)
        assert m.__agency_required__ == list(engine.ontology.nodes[label])


def test_validate_has_parity_with_ontology_violations(engine):
    em = EntityModels(engine.ontology)
    ont = engine.ontology
    cases = [
        ("Intent", {"purpose": "p", "deliverable": "d", "acceptance": "a",
                    "status": "working", "owner": "user"}),       # valid
        ("Intent", {"purpose": "p"}),                              # missing required
        ("Intent", {"purpose": "p", "deliverable": "d", "acceptance": "a",
                    "status": "working", "owner": "BOGUS"}),       # bad enum
        ("Invocation", {"capability": "c", "verb": "v", "role": "act"}),
        ("Invocation", {"capability": "c", "verb": "v", "role": "nope"}),  # bad enum
        ("Lifecycle", {"state": "working", "phase": 0}),
        ("Lifecycle", {"state": "not-a-state", "phase": 0}),       # bad enum
        ("Plan", {"title": "t"}),
        ("Plan", {}),                                              # missing required
        ("PlanStep", {"plan": "p", "index": 1, "description": "d", "state": "pending"}),
        ("PlanStep", {"plan": "p", "index": 1, "description": "d", "state": "bogus"}),
        ("NoSuchLabel", {}),                                       # unknown label
    ]
    for label, props in cases:
        assert sorted(em.validate(label, props)) == sorted(ont.violations(label, props)), \
            (label, props)


def test_derived_model_enforces_required_and_enum(engine):
    em = EntityModels(engine.ontology)
    m = em.model_for("Invocation")
    m.model_validate({"capability": "c", "verb": "v", "role": "act"})    # ok
    with pytest.raises(Exception):                                       # bad enum
        m.model_validate({"capability": "c", "verb": "v", "role": "bogus"})
    with pytest.raises(Exception):                                       # missing required
        m.model_validate({"capability": "c"})


def test_dump_raises_on_violation_else_returns_clean(engine):
    em = EntityModels(engine.ontology)
    with pytest.raises(ValueError):
        em.dump("Intent", {"purpose": "p"})
    assert em.dump("Plan", {"title": "t"})["title"] == "t"


def test_extension_label_is_covered(engine):
    """A capability-contributed node label (PlanStep, Spec 287) is derivable +
    enum-enforced just like a core label — proving derivation reads the EFFECTIVE
    ontology, not just the core."""
    em = EntityModels(engine.ontology)
    m = em.model_for("PlanStep")
    assert "state" in m.__agency_enums__
    assert m.__agency_enums__["state"] == {"pending", "done", "blocked", "skipped"}
