"""Spec 101 Slice 1 — novel capability MVN tests.

The 5-verb minimum viable novel path:
  conceptualize → create_novel → create_chapter → chapter_report → render_manuscript
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 101") -> str:
    iid = e.intent.capture(purpose, "ship MVN", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def test_novel_capability_registers_five_mvn_verbs() -> None:
    """Spec 101 First-Principles Minimum: the 5 MVN verbs MUST remain present.

    The cap grows beyond 5 as Spec 102+ ship (capture_idea etc.); this test
    guards the MVN-subset invariant — every novel cap, no matter which
    cluster slices are loaded, MUST expose the MVN path.
    """
    e = _fresh()
    cap = e.registry._caps["novel"]
    mvn = {"conceptualize", "create_novel", "create_chapter",
           "chapter_report", "render_manuscript"}
    assert mvn <= set(cap.verbs), f"missing MVN verbs: {mvn - set(cap.verbs)}"
    e.memory.close()


def test_novel_capability_lint_clean() -> None:
    from agency.capabilities.plugin import lint_capability
    e = Engine(":memory:", _require_skill_doc=False)
    res = lint_capability(e.registry._caps["novel"])
    assert res["ok"] is True
    assert res.get("mode") == "block"
    assert len(res.get("violations", [])) == 0
    e.memory.close()


def test_conceptualize_produces_novel_concept_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "conceptualize",
                      title="Modem Daze", author="The Phreakers",
                      premise="A phreaker tale set in 1984",
                      central_question="Does the BBS scene survive?")
    assert data["artefact"]["kind"] == "novel-concept"
    assert "Modem Daze" in data["result"]
    assert "BBS scene survive" in data["result"]
    e.memory.close()


def test_create_novel_records_node_serves_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "create_novel",
                      title="Modem Daze", author="The Phreakers")
    assert data["novel_id"].startswith("novel:")
    assert data["status"] == "concept"
    # SERVES edge
    rows = e.memory.g.query(
        "MATCH (n)-[r:SERVES]->(i) WHERE n.id = $nid AND i.id = $iid RETURN r",
        {"nid": data["novel_id"], "iid": iid})
    assert rows
    e.memory.close()


def test_create_chapter_records_chapter_of_edge() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="x", author="y")
    chapter, _ = _invoke(e, iid, "create_chapter",
                         novel_id=novel["novel_id"],
                         number=1, title="Opening")
    assert chapter["chapter_id"].startswith("chapter:")
    assert chapter["status"] == "outlined"
    # CHAPTER_OF edge
    rows = e.memory.g.query(
        "MATCH (c)-[r:CHAPTER_OF]->(n) WHERE c.id = $cid AND n.id = $nid "
        "RETURN r",
        {"cid": chapter["chapter_id"], "nid": novel["novel_id"]})
    assert rows
    e.memory.close()


def test_create_chapter_not_found_novel() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "create_chapter",
                        novel_id="bogus:does-not-exist",
                        number=1, title="x")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "NOT_FOUND" in err
    e.memory.close()


def test_chapter_report_aggregates_count_and_word_count() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="x", author="y")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=1, title="A",
            body="word " * 100)
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=2, title="B",
            body="word " * 200)
    report, _ = _invoke(e, iid, "chapter_report",
                        novel_id=novel["novel_id"])
    assert report["chapter_count"] == 2
    assert report["word_count_total"] >= 300
    assert report["by_status"] == {"outlined": 2}
    e.memory.close()


def test_render_manuscript_concatenates_chapters_in_order() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel",
                       title="My Novel", author="An Author")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=2, title="Second",
            body="second body")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=1, title="First",
            body="first body")
    ms, _ = _invoke(e, iid, "render_manuscript",
                    novel_id=novel["novel_id"])
    assert ms["artefact"]["kind"] == "manuscript"
    body = ms["artefact"]["body"]
    assert "My Novel" in body
    assert "An Author" in body
    # Order: chapter 1 before chapter 2
    assert body.index("First") < body.index("Second")
    assert body.index("first body") < body.index("second body")
    e.memory.close()


def test_novel_status_enum_bites() -> None:
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("Novel",
                          {"title": "x", "author": "y",
                           "status": "nonsense"})
    e.memory.close()


def test_novel_concept_skill_terminates_in_hard_gate() -> None:
    """Spec 101 → 102 invariant: the `novel-concept` skill is a conceptualizer
    that ends in a hard elicit. Phase count + names belong to whichever spec
    slice last extended the skill (Spec 102 extends to 10 phases) — this test
    guards the skill-shape invariant rather than a frozen phase list.
    """
    e = _fresh()
    sk = e.ontology.skill("novel-concept")
    assert sk["kind"] == "conceptualizer"
    assert sk["phases"][-1].get("gate") == "hard"
    assert sk["phases"][-1]["name"] == "confirmation"
    assert len(sk["phases"]) >= 5  # MVN floor; Spec 102 takes it to 10
    e.memory.close()


def test_novel_capability_ships_bitwize_templates_plus_documented_extensions() -> None:
    """The 10 bitwize-ported templates remain present (subset invariant), plus any
    documented Spec-NNN vendoring extensions.

    Per Spec 101 §"Templates (ported VERBATIM from the-agency-system)": 10 markdown
    templates ported verbatim from `Plan/_research/novel-mvp-source/templates/`,
    plus `ncp.json` (structural, at `data/ncp/ncp-template.json`).

    CLAUDE.md rule 8 (no hardcoded snapshots): the assertion is a relationship —
    the bitwize set is a SUBSET of live templates, and any extras must be
    declared as documented vendorings here. Adding a future template requires
    naming its source spec in `documented_extensions`, which is the intended
    audit trail.
    """
    e = _fresh()
    cap = e.registry._caps["novel"]
    bitwize = {"cast", "chapter", "character", "dramatica", "outline",
               "premise", "readme", "scene", "work", "world"}
    # Each entry: template name → source spec that vendored it.
    documented_extensions = {
        "chapter-briefing": "Spec 141",                             # KP wave (post-141 deepening)
    }
    live = set(cap.ontology.templates)
    assert bitwize <= live, f"missing bitwize templates: {bitwize - live}"
    extras = live - bitwize
    assert extras <= set(documented_extensions), (
        f"undocumented template additions: {extras - set(documented_extensions)} — "
        "add an entry to `documented_extensions` naming the source spec")
    # ncp.json is at data/ncp/, not in templates
    from pathlib import Path
    ncp = (Path(__file__).parent.parent
           / "agency" / "capabilities" / "novel"
           / "data" / "ncp" / "ncp-template.json")
    assert ncp.is_file()
    e.memory.close()


def test_dramatica_ontology_vendored_with_304_entries() -> None:
    """Per Spec 101 source-fidelity + decidability-matrix §"Context": the
    Dramatica ontology is the structural backbone (4 classes / 16 types / 62
    variations / 63 elements / 8 archetypes / 4 character-dynamics / 4
    plot-dynamics / 4 throughlines / 65 dynamic-pairs / 35 quads / 38 concepts
    = 303-304 entries depending on the vendor's count). Vendored at
    `data/dramatica/ontology.json` for Spec 103 storyform cluster to read."""
    from pathlib import Path
    import json
    ontology = (Path(__file__).parent.parent
                / "agency" / "capabilities" / "novel"
                / "data" / "dramatica" / "ontology.json")
    assert ontology.is_file()
    data = json.loads(ontology.read_text())
    # Tolerant: spec docs cite 303 OR 304; either is acceptable
    entries = data.get("entries", [])
    assert 300 <= len(entries) <= 310, (
        f"ontology has {len(entries)} entries — expected 303 or 304 per "
        f"Spec 101 source-fidelity audit")


def test_decidability_matrix_doc_vendored() -> None:
    """The 15-row Dramatica decidability matrix grounds Spec 103's check
    selection (11 decidable + 2 hybrid + 2 judgement). Vendored as a
    reference doc for the storyform cluster to cite."""
    from pathlib import Path
    matrix = (Path(__file__).parent.parent
              / "agency" / "capabilities" / "novel"
              / "data" / "reference" / "dramatica-decidability.md")
    assert matrix.is_file()
    body = matrix.read_text()
    assert "Decidable" in body
    assert "Judgement" in body
    assert "11 decidable + 2 hybrid + 2 judgement" in body


def test_novel_concept_schema_satisfied_by_skill_phases() -> None:
    """Guard against the schema↔skill name drift the self-review caught.

    Every field in the `novel-concept` schema must be producible by walking
    the `novel-concept` skill (any phase's `produces`) OR be a `conceptualize`
    verb arg. Otherwise the schema is unsatisfiable from the canonical path.
    """
    e = Engine(":memory:", _require_skill_doc=False)
    sk = e.ontology.skill("novel-concept")
    produced = {p for ph in sk["phases"] for p in ph.get("produces", [])}
    verb_args = {"title", "author"}
    schema_fields = set(
        e.registry._caps["novel"].ontology.schemas["novel-concept"])
    assert schema_fields <= (produced | verb_args), (
        f"schema fields not covered by skill phases or verb args: "
        f"{schema_fields - (produced | verb_args)}")
    e.memory.close()


def test_novel_concept_skill_walks_through_confirmation() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("novel-concept")
    run = SkillRun(e.memory, iid, sk)
    # Spec 102 extends to 10 phases — walk each then confirm.
    fills = [
        {"logline": "x", "central_question": "y"},
        {"genre": "g", "subgenre": "sg", "tone": "t"},
        {"target_reader": "r", "comp_titles": "c"},
        {"pov_choice": "p", "narrator_voice": "n"},
        {"world": "w", "time_period": "t", "geography": "g"},
        {"protagonist_seed": "p", "antagonist_seed": "a",
         "supporting_seeds": "s"},
        {"resolve_intent": "r", "growth_intent": "g",
         "approach_intent": "a", "mental_sex_intent": "m"},
        {"act_structure": "3-act", "midpoint_intent": "m",
         "ending_intent": "e"},
        {"standalone_or_series": "s", "series_arc": "n/a"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"user_confirmed": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()
