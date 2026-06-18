"""Acceptance — discover.acceptance, Gherkin criteria derivation (Spec 317).

Invariants (rule 8 — relationships, not pinned text): each criterion derives from
a deliverable sub-part; the VALIDATES edge count equals the criteria count;
unmeasurable parts are FLAGGED not dropped; coverage partitions the parts
(covered + gaps == deliverable_parts); every gherkin parses Given/When/Then.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/discover_acceptance.feature")


@when(parsers.parse('I derive acceptance for a deliverable "{deliverable}"'),
      target_fixture="acc")
def _derive(engine, confirmed_intent, deliverable):
    target = engine.intent.capture("a purpose", deliverable, "an acceptance")
    res, _ = invoke(engine, confirmed_intent, "discover", "acceptance",
                    agent_id="agent:test", for_intent_id=target)
    return {"target": target, "deliverable": deliverable, "res": res}


@then("every criterion derives from a deliverable sub-part")
def _derived(acc):
    deliverable = acc["deliverable"]
    for c in acc["res"]["criteria"]:
        assert c["source"] in deliverable, c["source"]


@then("each criterion validates the intent exactly once")
def _validates(engine, acc):
    edges = engine.memory.neighbors(acc["target"], "VALIDATES", direction="in")
    assert len(edges) == len(acc["res"]["criteria"]), (len(edges), len(acc["res"]["criteria"]))


@then("every criterion gherkin has Given When and Then clauses")
def _gherkin(acc):
    for c in acc["res"]["criteria"]:
        lines = [ln.strip() for ln in c["gherkin"].splitlines() if ln.strip()]
        assert len(lines) == 3, c["gherkin"]
        assert lines[0].startswith("Given") and lines[1].startswith("When") \
            and lines[2].startswith("Then"), c["gherkin"]


@then("at least one criterion is flagged unmeasurable")
def _flagged(acc):
    flagged = [c for c in acc["res"]["criteria"] if c["flagged"]]
    assert flagged, acc["res"]["criteria"]
    assert all(c["measurable"] is False for c in flagged), flagged


@then("the flagged criterion is still present")
def _not_dropped(acc):
    # flagged criteria are returned (surfaced), not silently dropped.
    assert any(c["flagged"] for c in acc["res"]["criteria"])
    # and the unmeasurable one is among the gaps, the measurable ones covered.
    cov = acc["res"]["coverage"]
    assert cov["gaps"], cov


@then("covered plus gaps equals the deliverable part count")
def _coverage_partition(acc):
    cov = acc["res"]["coverage"]
    assert cov["covered"] + len(cov["gaps"]) == cov["deliverable_parts"], cov
