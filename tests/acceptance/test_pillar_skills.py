"""Acceptance — pillar skills (Spec 375 Slice 1).

The three concept pillars (intent · lifecycle · memory) are committed `skill.yaml`
of `type: pillar`, loaded by `agency._pillars.load_pillars`, validated against the
371 schema, and rendered by `install.generate`. lifecycle & memory render
standalone at skills/<name>; intent (a live capability) is augmented with its
concept section rather than clobbered.

Assertions derive from the live pillar source (rule 8) — no snapshotted lists.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, then, when


scenarios("features/pillar_skills.feature")


def _pillar(name):
    from agency._pillars import load_pillars
    return next(p for p in load_pillars() if p.get("name") == name)


# ── When ──────────────────────────────────────────────────────────────────────

@when("I load the committed pillar skills", target_fixture="pillars")
def _load_pillars():
    from agency._pillars import load_pillars
    return load_pillars()


@when("the install files are generated", target_fixture="install_files")
def _generate(engine):
    from agency.install import generate
    return generate(engine)


@when("the install files are generated again", target_fixture="install_files_again")
def _generate_again(engine):
    from agency.install import generate
    return generate(engine)


# ── Then ──────────────────────────────────────────────────────────────────────

@then("at least one pillar is loaded")
def _at_least_one(pillars):
    assert pillars, "expected at least one committed pillar skill"


@then(parsers.parse('every loaded pillar is a schema-valid skill of type "{stype}"'))
def _all_valid(pillars, stype):
    from agency._skill_parse import parse_skill
    for p in pillars:
        res = parse_skill(p)
        assert res.ok, (
            f"pillar {p.get('name')!r} must satisfy the 371 schema; "
            f"got {res.code}: {res.message}")
        assert p.get("type") == stype, f"pillar {p.get('name')!r} must be type={stype!r}"


@then(parsers.parse('the loaded pillars include "{a}", "{b}" and "{c}"'))
def _named_pillars_present(pillars, a, b, c):
    names = {p.get("name") for p in pillars}
    for want in (a, b, c):
        assert want in names, f"expected {want!r} among loaded pillars; got {names}"


@then(parsers.parse('a "{path}" pillar skill is emitted'))
def _pillar_emitted(install_files, path):
    assert path in install_files, (
        f"install.generate must emit {path!r}; got skills/* keys: "
        f"{sorted(k for k in install_files if k.startswith('skills/'))}")


@then(parsers.parse('the rendered "{name}" pillar declares its name and '
                    'description in frontmatter'))
def _frontmatter_ok(install_files, name):
    md = install_files[f"skills/{name}/SKILL.md"]
    assert md.startswith("---\n"), "rendered pillar must open with YAML frontmatter"
    head = md.split("---", 2)[1]
    assert f"name: {name}" in head, f"frontmatter must name the skill; got:\n{head}"
    assert "description:" in head, "frontmatter must carry a description"


@then(parsers.parse('the rendered "{name}" pillar inlines its overview'))
def _overview_inlined(install_files, name):
    md = install_files[f"skills/{name}/SKILL.md"]
    overview = (_pillar(name).get("overview") or "").strip()
    first_line = next(ln for ln in overview.splitlines() if ln.strip())
    assert first_line.strip() in md, (
        f"rendered pillar must inline its overview; missing line: {first_line!r}")


@then(parsers.parse('the "{path}" skill keeps its capability verb table'))
def _keeps_verb_table(install_files, path):
    md = install_files[path]
    # The intent CAPABILITY skill has a verb table — the augment must not clobber it.
    assert "## Verbs" in md, (
        f"{path} must retain the capability's verb table after augmentation")


@then(parsers.parse('the "{path}" skill gains the intent pillar concept section'))
def _gains_concept(install_files, path):
    md = install_files[path]
    assert "pillar (concept)" in md, (
        f"{path} must gain the pillar concept section header")
    overview = (_pillar("intent").get("overview") or "").strip()
    first_line = next(ln for ln in overview.splitlines() if ln.strip())
    assert first_line.strip() in md, (
        f"{path} must inline the intent pillar overview; missing: {first_line!r}")


@then(parsers.parse('the two "{path}" renders are byte-identical'))
def _deterministic(install_files, install_files_again, path):
    assert install_files[path] == install_files_again[path], (
        f"{path} render must be deterministic (A7) — same source, same bytes")
