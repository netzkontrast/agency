"""Acceptance — core engine behaviours: the code-mode wire contract, provenance
(the moat), and the capability surface. Uses the shared conftest fixtures
(`engine`, `confirmed_intent`) + helpers (`tool_names`/`call_tool`/`invoke`/`served`)
and the shared Given steps. Behaviour only.
"""
from pytest_bdd import parsers, scenarios, then, when

from conftest import call_tool, invoke, served, tool_names
from agency.capability import is_cap_tool

scenarios("features/wire_contract.feature")
scenarios("features/provenance.feature")
scenarios("features/capability_surface.feature")


# ── wire contract ─────────────────────────────────────────────────────────────
@when("a client lists the available tools", target_fixture="tools")
def _list_tools(engine):
    return tool_names(engine, codemode=True)


@then(parsers.parse('"{a}", "{b}" and "{c}" are all available'))
def _three_verbs(tools, a, b, c):
    assert {a, b, c} <= tools, f"missing wire verbs in {tools}"


@then("no capability verb is exposed directly at the wire")
def _no_leak(tools):
    leaked = {n for n in tools if is_cap_tool(n)}
    assert not leaked, f"capability verbs leaked to the wire: {sorted(leaked)[:5]}"


@then("the execute verb is available to run capability code")
def _execute(tools):
    assert "execute" in tools


# ── provenance ────────────────────────────────────────────────────────────────
@when("I invoke a capability verb under that intent")
def _invoke_verb(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "reflect", "note",
           scope="observation", text="behaviour check")


@then("an Invocation is recorded in the graph")
def _invocation_recorded(engine):
    assert engine.memory.find("Invocation"), "no Invocation recorded"


@then("that Invocation SERVES the intent")
def _invocation_serves(engine, confirmed_intent):
    assert served(engine, confirmed_intent) >= 1, "no Invocation SERVES the intent"


@then("the intent has no served invocations")
def _no_served(engine, confirmed_intent):
    assert served(engine, confirmed_intent) == 0


# ── capability surface ──────────────────────────────────────────────────────────
@when("a client lists the capability verbs", target_fixture="verbs")
def _list_verbs(engine):
    return {n for n in tool_names(engine, codemode=False) if is_cap_tool(n)}


@then("many capability verbs are available")
def _many_verbs(verbs):
    assert len(verbs) > 50, f"verb surface collapsed to {len(verbs)}"


@then(parsers.parse('the "{cap}" capability exposes a full clustered verb suite'))
def _clustered(verbs, cap):
    n = len([v for v in verbs if v.startswith(f"capability_{cap}_")])
    assert n > 80, f"capability {cap!r} suite collapsed to {n}"


@when("I ask the engine doctor for a health report", target_fixture="health")
def _doctor(engine):
    return call_tool(engine, "agency_doctor", {})


@then("a non-empty health report is returned")
def _health_ok(health):
    assert isinstance(health, dict) and health


@when("a client lists all tools without code-mode", target_fixture="all_tools")
def _all_tools(engine):
    return tool_names(engine, codemode=False)


@then("the onboarding tools are all exposed")
def _onboarding(all_tools):
    expected = {"agency_welcome", "agency_install", "agency_doctor", "intent_bootstrap"}
    assert expected <= all_tools, f"missing onboarding tools: {expected - all_tools}"
