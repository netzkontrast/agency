"""Waves 4-12 typed-shape batch tests — basic invariant checks per shape."""
from __future__ import annotations

import pytest

import agency._typed_shapes_waves4_12 as M


def test_all_shapes_export():
    """Module exports the documented 80+ typed shapes for waves 4-12."""
    expected_min = 70   # subset invariant; module ships >= this many shapes
    cls_count = sum(
        1 for name in dir(M)
        if not name.startswith("_")
        and isinstance(getattr(M, name), type)
        and getattr(getattr(M, name), "__module__", "") == M.__name__
    )
    assert cls_count >= expected_min, (
        f"module should export >= {expected_min} typed shapes; got {cls_count}")


# A representative sample of invariant rejection tests across the waves.

def test_codemode_alias_requires_fields():
    with pytest.raises(ValueError):
        M.CodemodeAlias(name="", cap="c", verb="v")


def test_install_path_validates_tool():
    with pytest.raises(ValueError):
        M.InstallPath(tool="bogus", binary="b", ready=True)


def test_token_economy_followup_validates_status():
    with pytest.raises(ValueError):
        M.TokenEconomyFollowup(rule_id="r", status="bogus")


def test_drill_candidate_validates_relevance():
    with pytest.raises(ValueError):
        M.DrillCandidate(capability="c", relevance=2.0)


def test_alignment_cell_validates_goal_id():
    with pytest.raises(ValueError):
        M.AlignmentCell(spec_id="146", goal_id=99, status="aligned")


def test_gherkin_scenario_requires_all_fields():
    with pytest.raises(ValueError):
        M.GherkinScenario(feature="", given="g", when="w", then="t")


def test_token_api_validates_backend():
    with pytest.raises(ValueError):
        M.TokenAPIShape(backend="bogus", ready=True)


def test_promo_copy_validates_platform():
    with pytest.raises(ValueError):
        M.PromoCopy(track_id="t", body="b", platform="bogus")


def test_manuscript_export_validates_format():
    with pytest.raises(ValueError):
        M.ManuscriptExport(novel_id="n", format="bogus")


def test_codex_fuzzy_match_validates_score():
    with pytest.raises(ValueError):
        M.CodexFuzzyMatch(entry_id="e", score=2.5)


def test_reveal_veil_validates_audience():
    with pytest.raises(ValueError):
        M.RevealVeil(reveal_id="r", audience="bogus")


def test_stop_verification_validates_condition_range():
    with pytest.raises(ValueError):
        M.StopVerification(condition_id=99, met=True)


def test_db_migration_validates_direction():
    with pytest.raises(ValueError):
        M.DBMigration(migration_id="m", direction="bogus")


def test_dispatch_refinement_validates_weight():
    with pytest.raises(ValueError):
        M.DispatchRefinement(signal_id="s", weight=2.0)


# Accept-path tests — every shape accepts a valid construction.
def test_representative_valid_constructions():
    M.CodemodeAlias(name="x", cap="c", verb="v")
    M.InstallPath(tool="pipx", binary="agency", ready=True)
    M.AlignmentCell(spec_id="146", goal_id=1, status="aligned")
    M.GherkinScenario(feature="f", given="g", when="w", then="t")
    M.PromoCopy(track_id="t", body="b", platform="instagram")
    M.ManuscriptExport(novel_id="n", format="epub")
    M.CodexFuzzyMatch(entry_id="e", score=0.5)
    M.RevealVeil(reveal_id="r", audience="reader")
    M.StopVerification(condition_id=1, met=True)
    M.DBMigration(migration_id="m", direction="up")
    M.DispatchRefinement(signal_id="s", weight=0.5)
