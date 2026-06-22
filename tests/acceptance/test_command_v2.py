"""Acceptance — Command v2 (Spec 376).

The generated `/agency-<slug>` commands are CURATED: one per discipline + one per
pillar, NOT a top-N alpha cap. Each body launches its skill (a discipline → the
skill walk; a pillar → its concept SKILL.md), rendered from the live schema.

All expectations derive from the live `_all_skills` registry (rule 8) — no
snapshotted command lists or pinned counts.
"""
from __future__ import annotations

import re

from pytest_bdd import scenarios, then, when


scenarios("features/command_v2.feature")

_CURATED = ("discipline", "pillar")
_ENTRY_SLUGS = {"agency", "onboard"}  # /agency, /agency-onboard — not per-skill
_CMD_RE = re.compile(r"commands/agency-(.+)\.md$")


def _skills(engine):
    from agency.capabilities.skills._main import _all_skills
    return _all_skills(engine.registry)


def _slug(name):
    from agency.install import _skill_name_to_slug
    return _skill_name_to_slug(name)


def _curated_slugs(engine):
    return {_slug(n) for n, m in _skills(engine).items()
            if m["kind"] in _CURATED} - _ENTRY_SLUGS


def _command_slugs(files):
    out = set()
    for path in files:
        mt = _CMD_RE.match(path)
        if mt and mt.group(1) not in _ENTRY_SLUGS:
            out.add(mt.group(1))
    return out


# ── When ──────────────────────────────────────────────────────────────────────

@when("the install files are generated", target_fixture="install_files")
def _generate(engine):
    from agency.install import generate
    return generate(engine)


@when("the install files are generated again", target_fixture="install_files_again")
def _generate_again(engine):
    from agency.install import generate
    return generate(engine)


# ── Then ──────────────────────────────────────────────────────────────────────

@then("the per-skill command slugs are exactly the discipline and pillar skills")
def _curated_exact(install_files, engine):
    expected = _curated_slugs(engine)
    got = _command_slugs(install_files)
    assert got == expected, (
        f"command set drift — extra={got - expected}, missing={expected - got}")


@then("no per-skill command is generated for a non-curated skill kind")
def _no_noncurated(install_files, engine):
    skills = _skills(engine)
    curated = _curated_slugs(engine)
    got = _command_slugs(install_files)
    # A slug that belongs ONLY to a non-curated skill must not have a command.
    noncurated_only = {
        _slug(n) for n, m in skills.items() if m["kind"] not in _CURATED
    } - curated - _ENTRY_SLUGS
    leaked = got & noncurated_only
    assert not leaked, f"non-curated skills got commands: {leaked}"


@then("every discipline command body invokes the skill walk naming its real skill")
def _disciplines_launch(install_files, engine):
    skills = _skills(engine)
    checked = 0
    for n, m in skills.items():
        if m["kind"] != "discipline":
            continue
        slug = _slug(n)
        if slug in _ENTRY_SLUGS:
            continue
        body = install_files[f"commands/agency-{slug}.md"]
        assert "skill_walk" in body, f"{slug}: discipline command must launch the walk"
        assert n in body, f"{slug}: command must name its real skill {n!r}"
        checked += 1
    assert checked, "expected at least one discipline command"


@then("every discipline command tabulates each phase's produced output")
def _phase_outputs_explained(install_files, engine):
    skills = _skills(engine)
    checked = 0
    for n, m in skills.items():
        if m["kind"] != "discipline":
            continue
        slug = _slug(n)
        if slug in _ENTRY_SLUGS:
            continue
        body = install_files[f"commands/agency-{slug}.md"]
        for p in m["_schema"].get("phases", []):
            for out in (p.get("produces") or []):
                assert out in body, (
                    f"{slug}: phase {p.get('name')!r} output {out!r} must be explained")
        checked += 1
    assert checked, "expected at least one discipline command"


@then("every declared phase input appears in its discipline command")
def _phase_inputs_explained(install_files, engine):
    skills = _skills(engine)
    for n, m in skills.items():
        if m["kind"] != "discipline":
            continue
        slug = _slug(n)
        if slug in _ENTRY_SLUGS:
            continue
        body = install_files[f"commands/agency-{slug}.md"]
        for p in m["_schema"].get("phases", []):
            for inp in (p.get("inputs") or []):
                assert inp in body, (
                    f"{slug}: phase {p.get('name')!r} input {inp!r} must be explained")


@then("a discipline command links each phase verb to its reference doc")
def _verbs_referenced(install_files, engine):
    skills = _skills(engine)
    found = False
    for n, m in skills.items():
        if m["kind"] != "discipline":
            continue
        slug = _slug(n)
        if slug in _ENTRY_SLUGS:
            continue
        body = install_files[f"commands/agency-{slug}.md"]
        for p in m["_schema"].get("phases", []):
            for v in (p.get("verbs") or []):
                if "." not in v:
                    continue
                cap, vb = v.split(".", 1)
                try:
                    c = engine.registry.get(cap)
                except KeyError:
                    continue
                if getattr(c, "skill_doc", None) is None or vb not in c.verbs:
                    continue
                ref = f"skills/{cap.replace('_', '-')}/references/{vb}.md"
                assert ref in body, f"{slug}: verb {v!r} must link to {ref}"
                found = True
    assert found, "expected at least one discipline command linking a verb to its reference"


@then("every pillar command body points at its concept SKILL.md")
def _pillars_point(install_files, engine):
    skills = _skills(engine)
    checked = 0
    for n, m in skills.items():
        if m["kind"] != "pillar":
            continue
        slug = _slug(n)
        body = install_files[f"commands/agency-{slug}.md"]
        assert f"skills/{slug}/SKILL.md" in body, (
            f"{slug}: pillar command must point at its concept skill")
        checked += 1
    assert checked, "expected at least one pillar command"


@then("no two per-skill command bodies are byte-identical")
def _no_identical(install_files):
    bodies = [c for p, c in install_files.items()
              if _CMD_RE.match(p) and _CMD_RE.match(p).group(1) not in _ENTRY_SLUGS]
    assert len(bodies) == len(set(bodies)), (
        "per-skill command bodies must not be identical stubs")


@then("the two command sets are identical")
def _deterministic(install_files, install_files_again):
    a = {p: c for p, c in install_files.items() if _CMD_RE.match(p)}
    b = {p: c for p, c in install_files_again.items() if _CMD_RE.match(p)}
    assert a == b, "the curated command set must be deterministic (A7)"
