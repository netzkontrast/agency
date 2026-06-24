"""Spec 060 Phase 1 — Engine.materialise_ontology() wires the schema/template
materialisers into a graph projection.

The two `Ontology.materialise_{schemas,templates}` methods existed but were never
called (dormant surface). This closes the Phase-1 Done-When ("materialise once at
bootstrap completion") via an OPT-IN method the production server calls in
``__main__`` (like ``enable_session_autolog``) — a bare test Engine stays
graph-clean unless it opts in, so there is no blast radius on the suite.
"""
from __future__ import annotations

from agency.engine import Engine


def test_materialise_ontology_records_nodes_and_is_idempotent(tmp_path):
    eng = Engine(str(tmp_path / "s.db"))
    try:
        # dormant by default — nothing materialised until opted in
        assert eng.memory.find("Schema") == []
        assert eng.memory.find("Template") == []

        out = eng.materialise_ontology()

        # every ontology schema/template now has a graph node
        schemas = eng.memory.find("Schema")
        templates = eng.memory.find("Template")
        assert len(schemas) >= 1 and len(templates) >= 1
        assert len(out["schemas"]) == len(schemas)
        assert len(out["templates"]) == len(templates)

        n_s, n_t = len(schemas), len(templates)
        # idempotent: a second run records no new nodes (no churn)
        eng.materialise_ontology()
        assert len(eng.memory.find("Schema")) == n_s
        assert len(eng.memory.find("Template")) == n_t
    finally:
        eng.memory.close()


def test_bare_engine_does_not_materialise_unless_opted_in(tmp_path):
    eng = Engine(str(tmp_path / "s2.db"))   # no materialise_ontology() call
    try:
        assert eng.memory.find("Schema") == []
        assert eng.memory.find("Template") == []
    finally:
        eng.memory.close()
