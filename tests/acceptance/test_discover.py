"""Acceptance — discover capability scaffold (Spec 308).

Behaviour: the drop-in shell is discoverable, registers the locked Spec 307
ontology surface, reuses research's Citation, and derives its Agent Skill —
all from adding one folder. Rule 8: assert the locked SETS, never pinned counts.
"""
from __future__ import annotations

from pytest_bdd import scenarios, then, when

from conftest import invoke

scenarios("features/discover.feature")

# The locked Spec 307 surface (the contract every child of 307 populates).
_NODES = {"DiscoverySession", "ElicitationTurn", "ClarificationQuestion",
          "ScopeBoundary", "AcceptanceCriterion", "FeasibilitySignal",
          "IntentRefinement"}
_EDGES = {"ELICITS", "DISCOVERED", "CLARIFIES", "GROUNDS", "BOUNDS",
          "VALIDATES", "REFINES"}
_SCHEMAS = {"discovery-session", "elicitation-turn", "scope-boundary",
            "acceptance-criteria", "feasibility-probe", "intent-brief"}


@when("I ask discover for its status", target_fixture="status")
def _status(engine, confirmed_intent):
    return invoke(engine, confirmed_intent, "discover", "status",
                  agent_id="agent:test")[0]


@then("the discover status reports the seven program node types")
def _nodes(status):
    assert set(status["nodes"]) == _NODES, status["nodes"]


@then("the discover status reports the seven program edges")
def _edges(status):
    assert set(status["edges"]) == _EDGES, status["edges"]


@then("the discover status reports the four program enums and six schemas")
def _enums_schemas(status):
    # enums are reported as "Label.field"; assert the four enumerated fields.
    enum_fields = {e.split(".", 1)[1] for e in status["enums"]}
    assert enum_fields == {"ambiguity_kind", "kind", "side", "verdict"}, status["enums"]
    assert set(status["schemas"]) == _SCHEMAS, status["schemas"]


@then("the discover ontology does not declare a Citation node")
def _no_citation(engine):
    cap = engine.registry._caps["discover"]
    assert "Citation" not in cap.ontology.nodes, "discover must reuse research's Citation"


@then("discover has a derived SkillDoc")
def _skilldoc(engine):
    cap = engine.registry._caps["discover"]
    assert getattr(cap, "skill_doc", None) is not None, "no SkillDoc derived"


@then("the guided-discovery walkable skill is registered")
def _usage_walk(engine):
    # Spec 322 Slice 3: the authored discipline replaces the derived discover-usage
    # (Spec 081 — authored skills are the override, never replaced).
    assert "guided-discovery" in (engine.ontology.skills or {}), \
        "guided-discovery discipline skill missing"
