"""Acceptance — per-type skill rendering (Spec 373).

`render_typed_skill` is the ONE renderer: it selects `render/skill/<type>.md` by
the Skill's `type` and inlines the schema-driven data body (overview / when-to-use
/ example / common-mistakes / references) self-contained (A1). The description is
authored (no truncation); the render is deterministic (A7); the `_(Tier B…)_` stub
is gone (Spec 373 Slice 3 — a marker-less verb is a lint finding, Spec 377).
"""
from __future__ import annotations

from pathlib import Path

from pytest_bdd import parsers, scenarios, then, when

scenarios("features/skill_render_v2.feature")

_REPO = Path(__file__).resolve().parents[2]


def _capability_skill():
    return {
        "name": "demo", "kind": "capability", "type": "capability",
        "description": "Use when demonstrating the per-type renderer.",
        "overview": "demo is the per-type render exemplar.",
        "when_to_use": "rendering a capability skill from the v2 schema",
        "examples": [{"input": "demo.run()", "output": "a self-contained skill"}],
    }


@when("I render a capability-type v2 skill", target_fixture="rendered")
def _render_capability():
    from agency.skill_emit import render_typed_skill
    return render_typed_skill(_capability_skill())


@when("I render a discipline-type v2 skill", target_fixture="rendered")
def _render_discipline():
    from agency.skill_emit import render_typed_skill
    return render_typed_skill({
        "name": "frugal", "kind": "discipline", "type": "discipline",
        "description": "Use when adding code — reach for the leanest path first.",
        "overview": "frugal is the YAGNI discipline.",
        "common_mistakes": [
            {"symptom": "installs a library for a one-liner",
             "counter": "check the stdlib and native platform first"},
        ],
    })


@when("I render a pillar-type v2 skill", target_fixture="rendered")
def _render_pillar():
    from agency.skill_emit import render_typed_skill
    return render_typed_skill({
        "name": "memory", "kind": "pillar", "type": "pillar",
        "description": "Use when reasoning about what agency remembers.",
        "overview": "memory is the bi-temporal graph pillar.",
    })


@when("I render a v2 skill with a multi-sentence description", target_fixture="rendered")
def _render_multi_sentence():
    from agency.skill_emit import render_typed_skill
    sk = _capability_skill()
    sk["description"] = ("Use when X. This second sentence must survive intact.")
    return render_typed_skill(sk)


@then(parsers.parse(
    'the rendered skill heads with "{stype}" and inlines its overview and example'))
def _heads_capability(rendered, stype):
    body = next(iter(rendered.values()))
    assert f"# Demo {stype}" in body, body[:200]
    assert "demo is the per-type render exemplar." in body
    assert "a self-contained skill" in body


@then(parsers.parse(
    'the rendered skill heads with "{stype}" and inlines its common-mistakes table'))
def _heads_discipline(rendered, stype):
    body = next(iter(rendered.values()))
    assert f"# Frugal {stype}" in body, body[:200]
    assert "## Common mistakes" in body
    assert "| Symptom | Counter |" in body
    assert "check the stdlib and native platform first" in body


@then(parsers.parse('the rendered skill heads with "{stype}"'))
def _heads_pillar(rendered, stype):
    body = next(iter(rendered.values()))
    assert f"# Memory {stype}" in body, body[:200]


@then("the full authored description survives in the frontmatter")
def _desc_full(rendered):
    body = next(iter(rendered.values()))
    assert "This second sentence must survive intact." in body, body[:300]


@then("rendering the same skill again yields byte-identical output")
def _deterministic(rendered):
    from agency.skill_emit import render_typed_skill
    again = render_typed_skill(_capability_skill())
    assert again == rendered, "render_typed_skill is not deterministic (A7)"


@then("no committed SKILL.md contains the Tier-B apologetic stub")
def _no_tier_b():
    offenders = [
        str(p.relative_to(_REPO))
        for p in (_REPO / "skills").rglob("SKILL.md")
        if "Tier B" in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"Tier-B apologetic stub still on disk: {offenders}"
