"""Acceptance — strict skill-schema lint (Spec 377 Slice 1).

`plugin.lint_skill_schema` validates a 371 Skill dict against the strict contract
(per-type completeness, R1 trigger, self-containment, no-stub, verb-resolves). The
crafted samples are deliberate FAIL cases; the committed pillars are the live PASS
exemplars (rule 8 — the pass assertion derives from the real source).
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when


scenarios("features/skill_lint.feature")


# Crafted fail-case skills (one per rule). Minimal valid-enough to reach the rule.
_SAMPLES = {
    # type=technique requires `phases` (R15 core) — absent ⇒ schema failure.
    "thin-technique": {
        "name": "thin", "kind": "technique", "type": "technique",
        "description": "Use when doing the thing.",
    },
    # a Tier-B render stub committed into the body ⇒ no-stub.
    "tier-b-stub": {
        "name": "stub", "kind": "capability", "type": "capability",
        "description": "Use when x.", "overview": "_(Tier B verb)_ unfilled",
    },
    # a discipline phase with no `instructions` ⇒ phase-self-contained.
    "no-instructions": {
        "name": "nodisc", "kind": "discipline", "type": "discipline",
        "description": "Use when x.",
        "common_mistakes": [{"symptom": "s", "counter": "c"}],
        "phases": [{"name": "p1", "produces": ["out"]}],
    },
    # an invoke binding naming a verb absent from the live registry ⇒ verb-resolves.
    "bad-verb": {
        "name": "badverb", "kind": "capability", "type": "capability",
        "description": "Use when x.",
        "phases": [{"name": "p", "produces": ["r"], "instructions": "do it",
                    "invoke": {"capability": "analyze", "verb": "nonexistent_xyz"}}],
    },
}


def _lint(engine, iid, skill):
    raw, _ = engine.registry.invoke(
        engine.memory, iid, "plugin", "lint_skill_schema", skill=skill)
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I strict-lint the "{key}" sample skill'),
      target_fixture="lint_result")
def _lint_sample(engine, confirmed_intent, key):
    return _lint(engine, confirmed_intent, _SAMPLES[key])


@when("I strict-lint every committed pillar", target_fixture="pillar_lints")
def _lint_pillars(engine, confirmed_intent):
    from agency._pillars import load_pillars
    return {p["name"]: _lint(engine, confirmed_intent, p) for p in load_pillars()}


# ── Then ──────────────────────────────────────────────────────────────────────

@then("the skill lint result is not ok")
def _not_ok(lint_result):
    assert lint_result.get("ok") is False, f"expected lint to fail; got {lint_result}"


@then(parsers.parse('a skill-lint violation names the rule "{rule}"'))
def _violation_rule(lint_result, rule):
    rules = {x["rule"] for x in lint_result.get("violations", [])}
    assert rule in rules, f"expected a {rule!r} violation; got {sorted(rules)}"


@then("every committed pillar passes strict lint")
def _pillars_pass(pillar_lints):
    assert pillar_lints, "expected at least one committed pillar"
    for name, res in pillar_lints.items():
        assert res.get("ok") is True, (
            f"pillar {name!r} must pass strict lint; got {res.get('violations')}")
