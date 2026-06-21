"""Acceptance — Brooks-lint conceptual-integrity pass (Spec 359).

Behaviour through the real Engine registry: `intent.brooks_lint` returns
decidable, evidence-anchored findings across the five Brooks principles, with
`block` reserved for conceptual-integrity / irreversible-surface violations.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when

from conftest import invoke

scenarios("features/brooks_lint.feature")


# A coherent spec: balanced Why/Design, a real Failure-modes section, no parallel
# store, no irreversible surface touched.
_COHERENT = """# Spec — add a derived count

## Why
Callers need the live marker count beside the cited medians; today it is missing.

## Design
Add a read-only `count()` over the existing markers; reuse the store.

## Failure modes
A miscount misleads the gain report — assert it against a fixture so a regression
surfaces in CI rather than in a release.
"""

# Introduces a parallel store — the conceptual-integrity violation.
_PARALLEL = """# Spec — faster lookups

## Why
Lookups are slow.

## Design
We add a parallel store for decisions, a second index kept in sync with the graph,
so reads skip the traversal entirely.

## Failure modes
The two stores can diverge.
"""

# Gold-plated — many second-system wish-list markers over a thin Why.
_GOLDPLATED = """# Spec — the everything widget

## Why
A small helper is needed.

## Design
Ship the helper. It would be nice to also support themes; a future enhancement
could add plugins; for completeness we add export; while we're at it, a wish-list
of formats.

## Failure modes
Scope creep is a risk that must be watched carefully over the whole programme.
"""


def _lint(engine, intent, body):
    res, _ = invoke(engine, intent, "intent", "brooks_lint", target=body, kind="spec")
    return res


@when("I brooks-lint a coherent spec", target_fixture="brooks")
def _b_clean(engine, confirmed_intent):
    return _lint(engine, confirmed_intent, _COHERENT)


@when("I brooks-lint a spec that adds a parallel store", target_fixture="brooks")
def _b_parallel(engine, confirmed_intent):
    return _lint(engine, confirmed_intent, _PARALLEL)


@when("I brooks-lint a gold-plated spec", target_fixture="brooks")
def _b_gold(engine, confirmed_intent):
    return _lint(engine, confirmed_intent, _GOLDPLATED)


@then("the spec is conceptually coherent")
def _coherent(brooks):
    assert brooks.get("conceptual_integrity_ok") is True, brooks


@then("the spec is not conceptually coherent")
def _not_coherent(brooks):
    assert brooks.get("conceptual_integrity_ok") is False, brooks


@then(parsers.parse('a brooks finding has principle "{principle}" with severity "{sev}"'))
def _has_finding(brooks, principle, sev):
    assert any(f["principle"] == principle and f["severity"] == sev
               for f in brooks.get("findings", [])), brooks


@then("every brooks finding cites evidence")
def _evidence(brooks):
    findings = brooks.get("findings", [])
    assert findings and all(str(f.get("evidence", "")).strip() for f in findings), brooks
