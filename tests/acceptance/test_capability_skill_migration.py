"""Acceptance — capability skill migration (Spec 378 Slice 1, frugal A6 + phase-fill).

The core develop disciplines gain real inline phase `instructions` (A1), validated
the same as any skill (the schema doesn't care whether the data is auto-derived or
capability-authored — A6). Assertions read the LIVE schema (rule 8) — they assert
self-containment + render parity, not a snapshot of the instruction text.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when


scenarios("features/capability_skill_migration.feature")

_CORE_DISCIPLINES = ("debug", "verify", "plan", "execute")
_SDLC_DISCIPLINES = ("brainstorm", "review", "spec-panel")


def _schema(engine, name):
    from agency.capabilities.skills._main import _all_skills
    return _all_skills(engine.registry)[name]["_schema"]


# ── When ──────────────────────────────────────────────────────────────────────

@when("I strict-lint the core develop disciplines", target_fixture="disc_lints")
def _lint_core(engine, confirmed_intent):
    out = {}
    for name in _CORE_DISCIPLINES:
        raw, _ = engine.registry.invoke(
            engine.memory, confirmed_intent, "plugin", "lint_skill_schema",
            skill=_schema(engine, name))
        out[name] = raw["result"] if isinstance(raw, dict) and "result" in raw else raw
    return out


@when("I strict-lint the SDLC develop disciplines", target_fixture="disc_lints")
def _lint_sdlc(engine, confirmed_intent):
    out = {}
    for name in _SDLC_DISCIPLINES:
        raw, _ = engine.registry.invoke(
            engine.memory, confirmed_intent, "plugin", "lint_skill_schema",
            skill=_schema(engine, name))
        out[name] = raw["result"] if isinstance(raw, dict) and "result" in raw else raw
    return out


@when("the install files are generated", target_fixture="install_files")
def _generate(engine):
    from agency.install import generate
    return generate(engine)


@when("I strict-lint every develop discipline", target_fixture="disc_lints")
def _lint_all_develop(engine, confirmed_intent):
    from agency.capabilities.skills._main import _all_skills
    skills = _all_skills(engine.registry)
    targets = [n for n, m in skills.items()
               if m["capability"] == "develop" and m["kind"] == "discipline"]
    out = {}
    for name in targets:
        raw, _ = engine.registry.invoke(
            engine.memory, confirmed_intent, "plugin", "lint_skill_schema",
            skill=skills[name]["_schema"])
        out[name] = raw["result"] if isinstance(raw, dict) and "result" in raw else raw
    return out


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the "{name}" discipline is self-contained'))
def _self_contained(disc_lints, name):
    res = disc_lints[name]
    sc = [v for v in res.get("violations", []) if v["rule"] == "phase-self-contained"]
    assert not sc, f"{name!r} must be self-contained (A1 — every phase has instructions); got {sc}"


@when("I lint all registered disciplines", target_fixture="disc_gate")
def _lint_disc_gate(engine, confirmed_intent):
    raw, _ = engine.registry.invoke(
        engine.memory, confirmed_intent, "plugin", "lint_disciplines")
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


@then("no compliant discipline is blocked")
def _none_blocked(disc_gate):
    assert disc_gate["blocked"] == [], (
        f"a self-contained discipline regressed against the contract: "
        f"{disc_gate['blocked']}")


@then("every develop discipline is reported clean")
def _develop_clean(engine, disc_gate):
    from agency.capabilities.skills._main import _all_skills
    skills = _all_skills(engine.registry)
    develop_disc = {n for n, m in skills.items()
                    if m["capability"] == "develop" and m["kind"] == "discipline"}
    clean = set(disc_gate["clean"])
    assert develop_disc <= clean, (
        f"develop disciplines not in the clean set: {sorted(develop_disc - clean)}")


@then("the migration tail is reported as warnings")
def _tail_warned(disc_gate):
    assert disc_gate["warned"], (
        "expected the cross-capability migration tail surfaced as warnings")


@then(parsers.parse('the "{name}" discipline is reported clean'))
def _disc_reported_clean(disc_gate, name):
    assert name in disc_gate["clean"], (
        f"{name!r} expected in the clean set; "
        f"warned={[w['name'] for w in disc_gate['warned']]}, "
        f"blocked={[b['name'] for b in disc_gate['blocked']]}")


@then("every develop discipline is self-contained")
def _all_develop_self_contained(disc_lints):
    assert disc_lints, "expected develop disciplines"
    bad = {n: [v for v in r.get("violations", []) if v["rule"] == "phase-self-contained"]
           for n, r in disc_lints.items()}
    bad = {n: v for n, v in bad.items() if v}
    assert not bad, f"these develop disciplines are not self-contained (A1): {sorted(bad)}"


@then(parsers.parse('the rendered develop skill inlines the enriched "{name}" phase instructions'))
def _renders_instructions(engine, install_files, name):
    md = install_files["skills/develop/SKILL.md"]
    # Every instruction the enriched discipline declares must appear in the
    # rendered walk section (A2 parity — one source). Derived from the live schema.
    phases = _schema(engine, name).get("phases", [])
    authored = [p.get("instructions", "").strip() for p in phases if p.get("instructions")]
    assert authored, f"{name!r} must declare phase instructions for this slice"
    for instr in authored:
        first = next(ln for ln in instr.splitlines() if ln.strip())
        assert first.strip() in md, (
            f"rendered develop skill must inline {name!r} instructions; missing: {first!r}")
