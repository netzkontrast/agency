"""Acceptance — decay-risk Finding shape + decay knowledge (Spec 354).

The foundation slice of the Spec 353 brooks-lint port: the Finding value object
learns the Iron Law (Symptom → Source → Consequence → Remedy) and a derived
severity tier, the twelve decay risks are vendored as cited data, and the
decidable findings analyze already produces are tagged with the risk code + book
source they evidence. Behaviour only — assert what the shape DOES (defaults,
preservation, derived tier, data coverage, tagging), never internal call shapes.
"""
from __future__ import annotations

from dataclasses import fields

from pytest_bdd import given, parsers, scenarios, then, when

from agency.capabilities.analyze._findings import (
    Finding,
    FindingSeverity,
    make_finding,
)
from conftest import invoke

scenarios("features/decay_risk.feature")


# ── the Finding learns the Iron Law ─────────────────────────────────────────

@given("a finding constructed with no Iron Law fields", target_fixture="finding")
def _legacy_finding():
    return make_finding("Q001", "warn", "x.py", 3, "a symptom", "the evidence")


@then("its risk_code, source, consequence, and remedy all default to empty")
def _iron_law_defaults_empty(finding):
    assert finding.risk_code == ""
    assert finding.source == ""
    assert finding.consequence == ""
    assert finding.remedy == ""


@then("its legacy fields are unchanged")
def _legacy_unchanged(finding):
    assert finding.rule == "Q001"
    assert finding.severity == "warn"
    assert finding.file == "x.py"
    assert finding.line == 3
    assert finding.message == "a symptom"
    assert finding.evidence == "the evidence"


@given("a finding constructed with a long remedy and the Iron Law fields",
       target_fixture="finding")
def _iron_law_finding():
    long_remedy = "Extract the nested block into a named helper. " * 30  # ~1.3k chars
    return make_finding(
        "Q001", "warn", "x.py", 1, "a symptom", "the evidence",
        risk_code="R1", source="Fowler — Refactoring — Long Method",
        consequence="cognitive overload — readers must hold too much at once",
        remedy=long_remedy,
    )


@then("risk_code, source, consequence, and remedy are preserved verbatim")
def _iron_law_preserved(finding):
    assert finding.risk_code == "R1"
    assert finding.source == "Fowler — Refactoring — Long Method"
    assert finding.consequence == "cognitive overload — readers must hold too much at once"
    # The remedy is captured data (CLAUDE.md #9): kept in FULL, not truncated to
    # the message/evidence budget.
    expected = "Extract the nested block into a named helper. " * 30
    assert finding.remedy == expected
    assert len(finding.remedy) > 200  # would have been cut by the evidence budget


@given('a finding tagged with risk_code "R1"', target_fixture="finding")
def _tagged_finding():
    return make_finding(
        "Q001", "warn", "x.py", 1, "a symptom", "the evidence",
        risk_code="R1", source="Fowler — Refactoring",
        consequence="cognitive overload", remedy="extract a helper",
    )


@when("I serialise it with to_dict", target_fixture="finding_dict")
def _serialise(finding):
    return finding.to_dict()


@then("the dict still carries the legacy keys")
def _dict_legacy_keys(finding_dict):
    for key in ("rule", "severity", "file", "line", "message", "evidence"):
        assert key in finding_dict, f"to_dict dropped legacy key {key!r}"


@then("it also carries risk_code, source, consequence, and remedy")
def _dict_iron_law_keys(finding_dict):
    assert finding_dict["risk_code"] == "R1"
    assert finding_dict["source"] == "Fowler — Refactoring"
    assert finding_dict["consequence"] == "cognitive overload"
    assert finding_dict["remedy"] == "extract a helper"


# ── derived tier ────────────────────────────────────────────────────────────

@given('a finding with severity "fail"', target_fixture="finding")
def _fail_finding():
    return make_finding("X001", "fail", "x.py", 1, "m", "e")


@then('its rendered tier is "critical"')
def _tier_critical(finding):
    assert finding.tier == "critical"


@then("the dataclass has no second severity field")
def _no_second_severity_field(finding):
    names = [f.name for f in fields(finding)]
    assert "severity" in names
    # tier is a DERIVED property, never a stored field (rule 8).
    assert "tier" not in names
    assert [n for n in names if "sever" in n.lower()] == ["severity"]


@then(parsers.parse('severity "{sev}" renders tier "{tier}"'))
def _severity_renders_tier(sev, tier):
    f = make_finding("X001", sev, "x.py", 1, "m", "e")
    assert f.tier == tier


# ── the vendored decay-risk knowledge ───────────────────────────────────────

@when("I load the decay-risk data", target_fixture="risks")
def _load_risks():
    from agency.capabilities.analyze import _decay
    return _decay.load_risks()


@then("the built-in risks are exactly R1 through R6 and T1 through T6")
def _exact_risk_set(risks):
    canonical = {f"R{i}" for i in range(1, 7)} | {f"T{i}" for i in range(1, 7)}
    assert set(risks) == canonical


@then("the risk count is computed from the data, never a pinned literal")
def _count_from_data(risks):
    # len() over the loaded data is the only count source (rule 8) — equal to
    # the canonical set size DERIVED above, never a hardcoded 12.
    canonical = {f"R{i}" for i in range(1, 7)} | {f"T{i}" for i in range(1, 7)}
    assert len(risks) == len(canonical)


@then("every risk defines name, diagnostic, consequence, remedy, symptoms, "
      "sources, severity_guide, and what_not_to_flag")
def _full_shape(risks):
    required = ("name", "diagnostic", "consequence", "remedy", "symptoms",
                "sources", "severity_guide", "what_not_to_flag")
    for code, entry in risks.items():
        for key in required:
            assert entry.get(key), f"{code} missing or empty {key!r}"


@then("every listed source cites a book and a principle")
def _sources_cited(risks):
    for code, entry in risks.items():
        assert entry["sources"], f"{code} has no sources"
        for s in entry["sources"]:
            assert s.get("book") and s.get("principle"), \
                f"{code} source missing book/principle: {s}"


@then("every severity_guide names a critical, warning, and suggestion band")
def _severity_bands(risks):
    for code, entry in risks.items():
        guide = entry["severity_guide"]
        for band in ("critical", "warning", "suggestion"):
            assert guide.get(band), f"{code} severity_guide missing {band!r}"


@then('decay-risks.json carries a "_source" key naming the brooks-lint revision')
def _source_provenance():
    import json
    from pathlib import Path

    from agency.capabilities.analyze import _decay
    raw = json.loads(Path(_decay.DECAY_RISKS_PATH).read_text(encoding="utf-8"))
    assert raw.get("_source", "").startswith("brooks-lint@")


# ── the decidable→risk tagger (the bridge) ──────────────────────────────────

@given("a Python source file with a very long function", target_fixture="src")
def _src_long_function(tmp_path):
    # Derive the threshold from source (rule 8) so the fixture stays valid if the
    # long-function limit is retuned — never a guessed magic number.
    from agency.capabilities.analyze._quality import _FUNC_LOC_LIMIT
    body = "def big():\n    total = 0\n" + "    total += 1\n" * (_FUNC_LOC_LIMIT + 10)
    (tmp_path / "big.py").write_text(body)
    return str(tmp_path)


@given("a Python package with a circular import between two modules",
       target_fixture="src")
def _src_circular(tmp_path):
    (tmp_path / "__init__.py").write_text("")
    (tmp_path / "a.py").write_text("from . import b\nVALUE = 1\n")
    (tmp_path / "b.py").write_text("from . import a\nVALUE = 2\n")
    return str(tmp_path)


@given("a Python source file with one unused import", target_fixture="src")
def _src_unused(tmp_path):
    (tmp_path / "x.py").write_text("import sys\nx = 1\n")
    return str(tmp_path)


@when("the quality scanner runs and its findings are decay-tagged",
      target_fixture="tagged")
def _quality_tagged(src):
    from agency.capabilities.analyze import _decay, _quality
    return _decay.tag(_quality.scan(src))


@when("the architecture scanner runs and its findings are decay-tagged",
      target_fixture="tagged")
def _architecture_tagged(src):
    from agency.capabilities.analyze import _architecture, _decay
    return _decay.tag(_architecture.scan(src))


@then("the long-function finding keeps its legacy rule, severity, file, and line")
def _q003_legacy(tagged):
    hits = [f for f in tagged if f.rule == "Q003"]
    assert hits, "no Q003 long-function finding produced"
    f = hits[0]
    assert f.severity in ("info", "warn", "fail")
    assert f.file.endswith("big.py")
    assert f.line >= 1


@then('it is tagged risk_code "R1" with a Source, Consequence, and Remedy')
def _q003_tagged(tagged):
    f = [f for f in tagged if f.rule == "Q003"][0]
    assert f.risk_code == "R1"
    assert f.source and f.consequence and f.remedy


@then('the import-cycle finding is tagged risk_code "R5"')
def _a001_r5(tagged):
    hits = [f for f in tagged if f.rule == "A001"]
    assert hits, "no A001 import-cycle finding produced"
    assert hits[0].risk_code == "R5"


@then("its Source names a book from decay-risks.json")
def _a001_source(tagged):
    f = [f for f in tagged if f.rule == "A001"][0]
    assert "Martin — Clean Architecture" in f.source


@then("it carries a non-empty Consequence and Remedy")
def _a001_iron_law(tagged):
    f = [f for f in tagged if f.rule == "A001"][0]
    assert f.consequence and f.remedy


@then("the unused-import finding keeps an empty risk_code")
def _q001_untagged(tagged):
    hits = [f for f in tagged if f.rule == "Q001"]
    assert hits, "no Q001 unused-import finding produced"
    assert hits[0].risk_code == ""


@then("it still carries its original message")
def _q001_message(tagged):
    f = [f for f in tagged if f.rule == "Q001"][0]
    assert "unused import" in f.message


# ── the open set — custom Cx risks ──────────────────────────────────────────

@given('a custom risk registry defining "C1" over the long-function rule',
       target_fixture="custom_registry")
def _custom_registry():
    # The shape a project's custom_risks config (Spec 356) would merge in — the
    # registry is open (§4), so the SAME tagger machinery handles it without a
    # code edit.
    return {"C1": {
        "name": "Project House Style",
        "sources": [{"book": "Team Handbook", "principle": "House Style"}],
        "consequence": "violates the team's documented house style",
        "remedy": "follow the documented house style for function length",
        "decidable": ["Q003"],
    }}


@when("a long-function finding is decay-tagged against that registry",
      target_fixture="tagged")
def _tag_against_custom(custom_registry):
    from agency.capabilities.analyze import _decay
    f = make_finding("Q003", "warn", "big.py", 1, "function too long",
                     "def big(...)")
    return _decay.tag([f], risks=custom_registry)


@then('the finding is tagged risk_code "C1" with the custom Source, '
      "Consequence, and Remedy")
def _custom_tagged(tagged):
    f = tagged[0]
    assert f.risk_code == "C1"
    assert "Team Handbook" in f.source
    assert f.consequence == "violates the team's documented house style"
    assert f.remedy == "follow the documented house style for function length"


# ── analyze.run records the enriched findings ───────────────────────────────

@when('I run analyze on that package with axis "architecture"',
      target_fixture="run_result")
def _run_architecture(engine, confirmed_intent, src):
    res, _ = invoke(engine, confirmed_intent, "analyze", "run",
                    path=src, axes=["architecture"], agent_id="agent:test")
    return res["result"] if isinstance(res, dict) and "result" in res else res


@then('a recorded Finding node for the cycle carries risk_code "R5"')
def _recorded_r5(engine):
    a001 = [f for f in engine.memory.find("Finding") if f.get("rule") == "A001"]
    assert a001, "no A001 Finding recorded by analyze.run"
    assert any(f.get("risk_code") == "R5" for f in a001), \
        [f.get("risk_code") for f in a001]
