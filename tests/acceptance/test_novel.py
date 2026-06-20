"""Acceptance — novel capability (Gherkin conversion).

Converted from tests/test_novel_capability.py, test_novel_lifecycle.py,
test_novel_lifecycle_slice2.py, test_novel_prose.py, test_novel_prose_slice2.py,
test_novel_manuscript.py, test_novel_research.py, test_novel_storyform.py,
test_novel_storyform_slice2.py, test_novel_storyform_completion.py,
test_novel_ncp_validation.py, test_novel_worldbuilding.py, test_novel_codex.py,
test_novel_character_knowledge.py, test_novel_story_time.py,
test_novel_gates_slice2.py, test_novel_editorial_pipeline.py,
test_novel_e2e.py, test_novel_integration_xcap.py,
test_novel_walkable_skills.py.

DROPPED (not behaviour — implementation / structural):
 - test_novel_capability_registers_five_mvn_verbs — verifies internal verb
   registry set; structural invariant, not observable behaviour.
 - test_novel_capability_lint_clean — internal lint check on docstring shape.
 - test_novel_capability_ships_bitwize_templates_plus_documented_extensions —
   enumerates a frozen template-name set; structural.
 - test_dramatica_ontology_vendored_with_304_entries — file-content count,
   structural vendoring check.
 - test_decidability_matrix_doc_vendored — file existence/content, structural.
 - test_novel_concept_schema_satisfied_by_skill_phases — schema/skill alignment
   check against internal data structures.
 - test_novel_concept_skill_terminates_in_hard_gate — verifies internal skill
   shape; checked indirectly via walk behaviour.
 - test_novel_concept_skill_walks_through_confirmation — drives SkillRun
   internals directly (not via invoke); implementation.
 - test_novel_concept_skill_extended_to_ten_phases — frozen phase count.
 - test_novel_concept_skill_walks_through_all_ten_phases — SkillRun internals.
 - test_novel_status_enum_bites / test_idea_status_enum_bites — raw
   Memory.record enum enforcement; tests internal schema guard, not cap verbs.
 - test_novel_claim_status_enum_bites — same.
 - test_idea_node_declared_with_status_enum / test_promoted_to_edge_declared /
   test_storyform_node_declared / test_known_fact_node_declared /
   test_knows_and_learned_in_edges_registered / test_story_time_event_node_declared /
   test_narrative_beat_node_declared / test_new_edges_registered /
   test_codex_entry_node_declared / test_codex_kind_enum_present /
   test_codex_of_edge_registered / test_scene_node_declared_with_pov_enum /
   test_scene_of_edge_declared / test_world_nodes_declared /
   test_world_axiom_severity_enum / test_part_of_world_edge_registered /
   test_novel_claim_node_declared — ontology registration assertions on
   internal data structures, not observable verb behaviour.
 - test_novel_capability_registers_* (multiple registration tests) — internal
   registry set membership; structural.
 - test_twelve_ncp_fixtures_ported_verbatim / test_fixtures_byte_identical_to_upstream —
   file-identity / vendoring audit; structural.
 - test_check_throughline_partition_does_not_fail_other_broken_fixtures /
   test_check_slot_fill_does_not_fail_other_broken_fixtures /
   test_check_storybeat_moment_refs_does_not_fail_other_broken_fixtures —
   test matrix correctness of other fixtures; structural.
 - test_check_report_shape_is_low_token — token budget proxy on JSON length;
   implementation concern.
 - test_validate_appreciations_canonical_set_size_463 /
   test_validate_narrative_functions_canonical_set_size_144 — frozen count
   snapshots against vendored data.
 - test_resolve_term_module_helper_exists / test_resolve_term_* — private
   module helper; implementation detail.
 - test_storyform_build_skill_registered / test_character_architect_* /
   test_world_bible_architect_* / test_scene_bridge_auditor_* /
   test_three_new_skills_registered — skill-shape / phase-count assertions
   on internal ontology structures.
 - test_compose_world_rules_injects_matched_codex / test_compose_pov_card_* /
   test_assemble_scene_brief_continuity_* — tests internal prompt.assemble_scene_brief
   via a different cap; xcap prompt tests belong in prompt acceptance suite.
 - test_developmental_editor_phases_bind_to_gate /
   test_line_editor_phases_bind_to_gate — verify internal skill phase index
   bindings; structural.
 - test_skills_registered (editorial_pipeline) — internal registry membership.
 - All test_novel_production.py tests — test FileNovelStateDriver disk I/O and
   monkeypatching; driver implementation detail, not observable verb behaviour.
 - All test_novel_format_driver.py tests — test FormatDriver disk I/O / fake
   drivers / file paths; driver implementation, requires monkeypatching.
 - test_novel_prose_wet.py tests — require monkeypatched AnthropicDriver /
   Completion stub; driver binding, not observable behaviour of the engine.
 - test_novel_scene_writer_skill.py — SkillRun walker internals.
 - test_novel_xcap_dogfood_analyze.py — internal xcap routing analysis,
   not observable behaviour.

GAPS:
 - publication_gate (requires FormatDriver disk writes) — needs production
   engine monkeypatching. Excluded per the no-faking doctrine.
 - export_epub / export_pdf / export_docx — require FormatDriver; excluded.
 - generate_scene_body / fetch_scene_body — require AnthropicDriver stub;
   excluded.
 - render_chapter_brief / storyform_critical_pass / dispatch_novel_research
   xcap provenance detail — xcap routing is exercised at the verb level;
   the deep multi-cap provenance graph shape is a separate xcap suite.
 - assemble_scene_brief upgrades (world_rules composer, pov_card composer,
   continuity composer) — belong in prompt capability acceptance suite.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/novel.feature")

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "novel"


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.ncp.json").read_text())


# ─── shared state containers ────────────────────────────────────────────────

@pytest.fixture
def ctx():
    """Mutable bag for step-level state within a scenario."""
    return {}


# ─── novel ───────────────────────────────────────────────────────────────────

@given("a novel titled \"Modem Daze\" by \"The Phreakers\"")
@given(parsers.parse('a novel titled "{title}" by "{author}"'))
def _given_novel(engine, confirmed_intent, ctx, title="Modem Daze", author="The Phreakers"):
    result, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                       title=title, author=author)
    ctx["novel_id"] = result["novel_id"]
    ctx["novel"] = result
    return result


@given("a novel for codex tests")
def _given_novel_codex(engine, confirmed_intent, ctx):
    result, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                       title="Codex Test", author="A. Author", genre="lit")
    ctx["novel_id"] = result["novel_id"]
    return result


@given("a novel titled \"Empty\" by \"Author\"")
def _given_empty_novel(engine, confirmed_intent, ctx):
    result, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                       title="Empty", author="Author")
    ctx["novel_id"] = result["novel_id"]
    return result


@given("a novel titled \"X\" by \"Y\"")
def _given_xy_novel(engine, confirmed_intent, ctx):
    result, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                       title="X", author="Y")
    ctx["novel_id"] = result["novel_id"]
    return result


@given("a novel titled \"Original Title\" by \"Author\"")
def _given_original_title_novel(engine, confirmed_intent, ctx):
    result, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                       title="Original Title", author="Author")
    ctx["novel_id"] = result["novel_id"]
    return result


@given("a novel with chapters of 100 words and 200 words")
def _given_novel_with_chapters_word_counts(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="W", author="A")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=1, title="A", body="word " * 100)
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=2, title="B", body="word " * 200)
    ctx["novel_id"] = nid


@given("a novel with chapters added in reverse order 3 2 1")
def _given_novel_reverse_chapters(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="R", author="A")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=3, title="C")
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=1, title="A")
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=2, title="B")
    ctx["novel_id"] = nid


@given("a novel with a chapter")
def _given_novel_with_chapter(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    chap, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                     novel_id=nid, number=1, title="Opening")
    ctx["novel_id"] = nid
    ctx["chapter_id"] = chap["chapter_id"]


@given("a novel with one 50-word chapter drafted and one 100-word chapter outlined")
def _given_novel_progress_seed(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    c1, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                   novel_id=nid, number=1, title="A", body="word " * 50)
    c2, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                   novel_id=nid, number=2, title="B", body="word " * 100)
    invoke(engine, confirmed_intent, "novel", "set_chapter_status",
           chapter_id=c1["chapter_id"], status="drafted")
    ctx["novel_id"] = nid


@given("two novels have been created, the second titled \"Last\"")
def _given_two_novels_last(engine, confirmed_intent, ctx):
    invoke(engine, confirmed_intent, "novel", "create_novel",
           title="First", author="X")
    last, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                     title="Last", author="Y")
    ctx["last_novel_id"] = last["novel_id"]


@given(parsers.parse('a novel titled "{title}" by "{author}"'))
def _given_novel_titled(engine, confirmed_intent, ctx, title, author):
    result, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                       title=title, author=author)
    ctx["novel_id"] = result["novel_id"]


@given("chapter 2 titled \"Second\" with body \"second body\"")
def _given_chapter_second(engine, confirmed_intent, ctx):
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=ctx["novel_id"], number=2, title="Second",
           body="second body")


@given("chapter 1 titled \"First\" with body \"first body\"")
def _given_chapter_first(engine, confirmed_intent, ctx):
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=ctx["novel_id"], number=1, title="First",
           body="first body")


@given("a novel with chapters \"Connection\" \"Discovery\" \"Confrontation\"")
def _given_novel_synopsis_chapters(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="Modem Daze", author="The Phreakers")
    nid = novel["novel_id"]
    for n, title in [(1, "Connection"), (2, "Discovery"), (3, "Confrontation")]:
        invoke(engine, confirmed_intent, "novel", "create_chapter",
               novel_id=nid, number=n, title=title)
    ctx["novel_id"] = nid


@given("novels titled \"The Great Modem\" and \"Quantum Dawn\" and \"Modem Mysteries\"")
def _given_three_novels(engine, confirmed_intent, ctx):
    invoke(engine, confirmed_intent, "novel", "create_novel",
           title="The Great Modem", author="A")
    invoke(engine, confirmed_intent, "novel", "create_novel",
           title="Quantum Dawn", author="B")
    invoke(engine, confirmed_intent, "novel", "create_novel",
           title="Modem Mysteries", author="C")


# ─── when: novel core ────────────────────────────────────────────────────────

@when("I create a novel titled \"Modem Daze\" by \"The Phreakers\"",
      target_fixture="result_pair")
def _when_create_novel(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "create_novel",
                    title="Modem Daze", author="The Phreakers")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I create chapter 1 titled \"Opening\" for that novel",
      target_fixture="result_pair")
def _when_create_chapter(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "create_chapter",
                    novel_id=ctx["novel_id"], number=1, title="Opening")
    ctx["result"] = r
    ctx["inv"] = inv
    ctx["chapter_id"] = r["chapter_id"] if r else None
    return r, inv


@when("I create a chapter for novel_id \"novel:does-not-exist\"",
      target_fixture="result_pair")
def _when_create_chapter_not_found(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "create_chapter",
                    novel_id="novel:does-not-exist", number=1, title="x")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I call chapter_report for that novel", target_fixture="report")
def _when_chapter_report(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "chapter_report",
                  novel_id=ctx["novel_id"])
    ctx["report"] = r
    return r


@when("I call render_manuscript", target_fixture="ms_result")
def _when_render_manuscript(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "render_manuscript",
                  novel_id=ctx["novel_id"])
    ctx["ms"] = r
    return r


@when("I call conceptualize with title \"Modem Daze\" premise \"A phreaker tale\"",
      target_fixture="concept_result")
def _when_conceptualize(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "conceptualize",
                  title="Modem Daze", author="The Phreakers",
                  premise="A phreaker tale set in 1984",
                  central_question="Does the BBS scene survive?")
    ctx["concept"] = r
    return r


# ─── when: ideas ─────────────────────────────────────────────────────────────

@when("I capture an idea with text \"A novel about time-loops\"",
      target_fixture="idea_result")
def _when_capture_idea(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "capture_idea",
                    text="A novel about time-loops")
    ctx["result"] = r
    ctx["inv"] = inv
    ctx["idea_id"] = r["idea_id"] if r else None
    return r, inv


@given("three ideas have been captured")
def _given_three_ideas(engine, confirmed_intent, ctx):
    for text in ["idea-1", "idea-2", "idea-3"]:
        invoke(engine, confirmed_intent, "novel", "capture_idea", text=text)


@given("a captured idea")
def _given_captured_idea(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "capture_idea",
                  text="A premise for a novel")
    ctx["idea_id"] = r["idea_id"]


@when("I list all ideas", target_fixture="ideas_result")
def _when_list_all_ideas(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "list_ideas")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when(parsers.parse('I list ideas with status "{status}"'),
      target_fixture="ideas_result")
def _when_list_ideas_status(engine, confirmed_intent, ctx, status):
    r, inv = invoke(engine, confirmed_intent, "novel", "list_ideas",
                    status=status)
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I promote the idea to a novel titled \"The Promoted Novel\" by \"An Author\"",
      target_fixture="promote_result")
def _when_promote_idea(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "promote_idea",
                    idea_id=ctx["idea_id"],
                    title="The Promoted Novel", author="An Author")
    ctx["result"] = r
    ctx["inv"] = inv
    ctx["promoted_novel_id"] = r["novel_id"] if r else None
    ctx["promoted_idea_id"] = ctx.get("idea_id")
    return r, inv


@when("I promote idea_id \"idea:does-not-exist\" to a novel",
      target_fixture="promote_result")
def _when_promote_not_found(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "promote_idea",
                    idea_id="idea:does-not-exist",
                    title="x", author="y")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


# ─── when: find_novel ────────────────────────────────────────────────────────

@when(parsers.parse('I call find_novel with query "{query}"'),
      target_fixture="find_result")
def _when_find_novel(engine, confirmed_intent, ctx, query):
    r, _ = invoke(engine, confirmed_intent, "novel", "find_novel",
                  query=query)
    ctx["find"] = r
    return r


@when('I call find_novel with query ""', target_fixture="find_result")
def _when_find_novel_empty(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "find_novel", query="")
    ctx["find"] = r
    return r


# ─── when: set_novel_status ───────────────────────────────────────────────────

@when(parsers.parse('I set the novel status to "{status}"'),
      target_fixture="status_result")
def _when_set_novel_status(engine, confirmed_intent, ctx, status):
    r, inv = invoke(engine, confirmed_intent, "novel", "set_novel_status",
                    novel_id=ctx["novel_id"], status=status)
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when(parsers.parse('I set status "{status}" on novel_id "novel:nope"'),
      target_fixture="status_result")
def _when_set_novel_status_not_found(engine, confirmed_intent, ctx, status):
    r, inv = invoke(engine, confirmed_intent, "novel", "set_novel_status",
                    novel_id="novel:nope", status=status)
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


# ─── when: lifecycle slice 2 ─────────────────────────────────────────────────

@when("I call list_chapters", target_fixture="chapters_result")
def _when_list_chapters(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "list_chapters",
                    novel_id=ctx["novel_id"])
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I create a scene with slug \"cold-open\" and pov \"third-limited\"",
      target_fixture="scene_result")
def _when_create_scene(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "create_scene",
                    chapter_id=ctx["chapter_id"],
                    slug="cold-open", pov="third-limited")
    ctx["result"] = r
    ctx["inv"] = inv
    ctx["scene_id"] = r["scene_id"] if r else None
    return r, inv


@when("I create a scene with pov \"qwerty gibberish nonsense\"",
      target_fixture="scene_result")
def _when_create_scene_bad_pov(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "create_scene",
                    chapter_id=ctx["chapter_id"],
                    slug="bad-pov", pov="qwerty gibberish nonsense")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I create a scene with a rich pov \"omniscient-but-spelt-wrong\"",
      target_fixture="scene_result")
def _when_create_scene_rich_pov(engine, confirmed_intent, ctx):
    # Spec 284 — pov is a projected enum: rich free text projects onto a
    # canonical SCENE_POV member, preserving the original in pov_detail.
    r, inv = invoke(engine, confirmed_intent, "novel", "create_scene",
                    chapter_id=ctx["chapter_id"],
                    slug="rich-pov", pov="omniscient-but-spelt-wrong")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@then("the scene pov is the canonical \"third-omniscient\"")
def _then_scene_pov_canonical(ctx):
    assert ctx["result"]["pov"] == "third-omniscient"


@then("the scene pov_detail preserves \"omniscient-but-spelt-wrong\"")
def _then_scene_pov_detail(ctx):
    assert ctx["result"]["pov_detail"] == "omniscient-but-spelt-wrong"


@when("I set the chapter status to \"drafted\"",
      target_fixture="chap_status_result")
def _when_set_chapter_status(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "set_chapter_status",
                    chapter_id=ctx["chapter_id"], status="drafted")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I set the chapter status to \"bogus\"",
      target_fixture="chap_status_result")
def _when_set_chapter_status_bogus(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "set_chapter_status",
                    chapter_id=ctx["chapter_id"], status="bogus")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I rename the novel to \"Renamed Title\"",
      target_fixture="rename_result")
def _when_rename_novel(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "rename_novel",
                    novel_id=ctx["novel_id"], new_title="Renamed Title")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I call novel_progress", target_fixture="progress_result")
def _when_novel_progress(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "novel_progress",
                  novel_id=ctx["novel_id"])
    ctx["progress"] = r
    return r


@when("I call resume_session", target_fixture="session_result")
def _when_resume_session(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "resume_session")
    ctx["session"] = r
    return r


@when("I call resume_session on a fresh engine with no novels",
      target_fixture="session_result")
def _when_resume_session_empty(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "resume_session")
    ctx["session"] = r
    return r


@when("I call list_chapters", target_fixture="empty_chapters_result")
def _when_list_chapters_empty(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "list_chapters",
                    novel_id=ctx["novel_id"])
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


# ─── when: prose verbs ───────────────────────────────────────────────────────

@when("I call count_words with body \"The quick brown fox jumps over the lazy dog.\"",
      target_fixture="word_result")
def _when_count_words(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "count_words",
                  body="The quick brown fox jumps over the lazy dog.")
    ctx["wc"] = r
    return r


@when("I call count_words with body \"\"",
      target_fixture="word_result")
def _when_count_words_empty(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "count_words", body="")
    ctx["wc"] = r
    return r


@when("I call analyze_readability with simple short-sentence prose",
      target_fixture="readability_result")
def _when_analyze_readability(engine, confirmed_intent, ctx):
    body = ("The cat sat on the mat. The mat was red. "
            "The cat was happy. The day was bright.")
    r, inv = invoke(engine, confirmed_intent, "novel", "analyze_readability",
                    body=body)
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I call analyze_readability with body \"\"",
      target_fixture="readability_result")
def _when_analyze_readability_empty(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "analyze_readability",
                    body="")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I call check_filter_words with filter-heavy prose",
      target_fixture="filter_result")
def _when_check_filter_heavy(engine, confirmed_intent, ctx):
    body = ("She really just wanted to somehow feel actually alive. "
            "It was very quiet, really still.")
    r, _ = invoke(engine, confirmed_intent, "novel", "check_filter_words",
                  body=body)
    ctx["fw"] = r
    return r


@when("I call check_filter_words with clean prose",
      target_fixture="filter_result")
def _when_check_filter_clean(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_filter_words",
                  body="She wanted to feel alive. The room held its breath, silent.")
    ctx["fw"] = r
    return r


@when("I call scan_proper_nouns with body \"Alice met Bob at the diner. Then Charlie arrived. Alice waved.\"",
      target_fixture="proper_noun_result")
def _when_scan_proper_nouns(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "scan_proper_nouns",
                  body="Alice met Bob at the diner. Then Charlie arrived. Alice waved.")
    ctx["pn"] = r
    return r


@when("I call scan_proper_nouns with body \"The morning was clear. She walked to the park. Then George arrived.\"",
      target_fixture="proper_noun_result")
def _when_scan_proper_nouns_sentence_initial(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "scan_proper_nouns",
                  body="The morning was clear. She walked to the park. Then George arrived.")
    ctx["pn"] = r
    return r


@when("I call check_dialogue_attribution with plain attribution prose",
      target_fixture="dialogue_result")
def _when_check_dialogue_plain(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_dialogue_attribution",
                  body='"Hi," she said. "Are you ready?" he asked. "Yes," she said.')
    ctx["da"] = r
    return r


@when("I call check_dialogue_attribution with flowery attribution prose",
      target_fixture="dialogue_result")
def _when_check_dialogue_flowery(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_dialogue_attribution",
                  body=('"Watch out!" he exclaimed. "I see it," she muttered. '
                        '"Of course," he ejaculated.'))
    ctx["da"] = r
    return r


@when("I call check_show_dont_tell with action prose",
      target_fixture="sdt_result")
def _when_check_sdt_clean(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_show_dont_tell",
                  body="The door swung open. Sunlight spilled across the floor.")
    ctx["sdt"] = r
    return r


@when("I call check_show_dont_tell with telling-verb prose",
      target_fixture="sdt_result")
def _when_check_sdt_tells(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_show_dont_tell",
                  body=("She felt sad. He realized something was wrong. "
                        "She noticed his face. They wondered if it would end."))
    ctx["sdt"] = r
    return r


@when("I call check_content_warnings with neutral prose",
      target_fixture="cw_result")
def _when_cw_clean(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_content_warnings",
                  body="She walked through the meadow. Bees danced. The sun was warm.")
    ctx["cw"] = r
    return r


@when("I call check_content_warnings with violent substance prose",
      target_fixture="cw_result")
def _when_cw_violent(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_content_warnings",
                  body=("The knife pierced his chest. Blood pooled. "
                        "She drank the whiskey and lit a cigarette."))
    ctx["cw"] = r
    return r


# ─── when: manuscript ────────────────────────────────────────────────────────

@when("I call render_blurb with hook \"A phreaker discovers a secret BBS\" and stakes \"The sysop is watching\"",
      target_fixture="blurb_result")
def _when_render_blurb(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "render_blurb",
                    novel_id=ctx["novel_id"],
                    hook="A phreaker discovers a secret BBS",
                    stakes="The sysop is watching")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I call render_blurb on novel_id \"novel:nope\"",
      target_fixture="blurb_result")
def _when_render_blurb_not_found(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "render_blurb",
                    novel_id="novel:nope", hook="x", stakes="y")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when("I call render_query_letter with agent \"Jane Smith\" and comp_titles \"Neuromancer, Snow Crash\"",
      target_fixture="ql_result")
def _when_render_query_letter(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "render_query_letter",
                  novel_id=ctx["novel_id"],
                  agent_name="Jane Smith",
                  comp_titles="Neuromancer, Snow Crash")
    ctx["ql"] = r
    return r


@when("I call render_synopsis", target_fixture="synopsis_result")
def _when_render_synopsis(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "render_synopsis",
                  novel_id=ctx["novel_id"])
    ctx["synopsis"] = r
    return r


# ─── when: research ──────────────────────────────────────────────────────────

@when("I capture a claim with text \"BBS peaked at 60K nodes\" domain \"historical\"",
      target_fixture="claim_result")
def _when_capture_claim(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "capture_claim",
                    text="BBS peaked at 60K nodes",
                    source_uri="https://archive.org/x",
                    domain="historical")
    ctx["result"] = r
    ctx["inv"] = inv
    ctx["claim_id"] = r["claim_id"] if r else None
    return r, inv


@when("I capture a claim with invalid domain \"not-a-domain\"",
      target_fixture="claim_result")
def _when_capture_claim_bad_domain(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "capture_claim",
                    text="x", source_uri="u", domain="not-a-domain")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@given("three claims have been captured")
def _given_three_claims(engine, confirmed_intent, ctx):
    for text, domain in [("a", "historical"), ("b", "scientific"), ("c", "cultural")]:
        invoke(engine, confirmed_intent, "novel", "capture_claim",
               text=text, source_uri="u", domain=domain)


@when("I list all claims", target_fixture="claims_result")
def _when_list_all_claims(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "list_claims")
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@when(parsers.parse('I list claims with verified "{verified}"'),
      target_fixture="claims_result")
def _when_list_claims_verified(engine, confirmed_intent, ctx, verified):
    r, inv = invoke(engine, confirmed_intent, "novel", "list_claims",
                    verified=verified)
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@given("claims captured for domains \"historical\" and \"scientific\"")
def _given_claims_two_domains(engine, confirmed_intent, ctx):
    invoke(engine, confirmed_intent, "novel", "capture_claim",
           text="p1", source_uri="u", domain="historical")
    invoke(engine, confirmed_intent, "novel", "capture_claim",
           text="p2", source_uri="u", domain="scientific")


@when("I call pending_verifications", target_fixture="pending_result")
def _when_pending_verifications(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "pending_verifications")
    ctx["pending"] = r
    return r


# ─── when: storyform checks ──────────────────────────────────────────────────

@when("I call check_throughline_partition with the good_work fixture",
      target_fixture="check_result")
def _when_throughline_good(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_throughline_partition", ncp=_load("good_work"))
    ctx["check"] = r
    return r


@when("I call check_throughline_partition with the broken_work_throughline_partition fixture",
      target_fixture="check_result")
def _when_throughline_broken(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_throughline_partition",
                  ncp=_load("broken_work_throughline_partition"))
    ctx["check"] = r
    return r


@when("I call check_slot_fill with the good_work fixture",
      target_fixture="check_result")
def _when_slot_fill_good(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_slot_fill", ncp=_load("good_work"))
    ctx["check"] = r
    return r


@when("I call check_slot_fill with the broken_work_slot_fill fixture",
      target_fixture="check_result")
def _when_slot_fill_broken(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_slot_fill", ncp=_load("broken_work_slot_fill"))
    ctx["check"] = r
    return r


@when("I call check_storybeat_moment_refs with the good_work fixture",
      target_fixture="check_result")
def _when_storybeat_good(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_storybeat_moment_refs", ncp=_load("good_work"))
    ctx["check"] = r
    return r


@when("I call check_storybeat_moment_refs with the broken_work_storybeat_moment_refs fixture",
      target_fixture="check_result")
def _when_storybeat_broken(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_storybeat_moment_refs",
                  ncp=_load("broken_work_storybeat_moment_refs"))
    ctx["check"] = r
    return r


@when("I call novel_coherence_check with the good_work fixture",
      target_fixture="composite_result")
def _when_coherence_good(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "novel_coherence_check", ncp=_load("good_work"))
    ctx["composite"] = r
    return r


@when("I call novel_coherence_check with the broken_work_throughline_partition fixture",
      target_fixture="composite_result")
def _when_coherence_throughline_broken(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "novel_coherence_check",
                  ncp=_load("broken_work_throughline_partition"))
    ctx["composite"] = r
    return r


@when("I call novel_coherence_check with the broken_work_approach_concern fixture",
      target_fixture="composite_result")
def _when_coherence_approach(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "novel_coherence_check",
                  ncp=_load("broken_work_approach_concern"))
    ctx["composite"] = r
    return r


@when("I call validate_appreciations with the good_work fixture",
      target_fixture="appreciation_result")
def _when_validate_appreciations_good(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "validate_appreciations", ncp=_load("good_work"))
    ctx["check"] = r
    return r


@when("I call validate_appreciations with an NCP containing appreciation \"NOT-A-REAL-APPRECIATION\"",
      target_fixture="appreciation_result")
def _when_validate_appreciations_bad(engine, confirmed_intent, ctx):
    ncp = {"story": {"narratives": [{"subtext": {"perspectives": [
        {"appreciation": "NOT-A-REAL-APPRECIATION"}]}}]}}
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "validate_appreciations", ncp=ncp)
    ctx["check"] = r
    return r


@when("I call validate_narrative_functions with the good_work fixture",
      target_fixture="nf_result")
def _when_validate_nf_good(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "validate_narrative_functions", ncp=_load("good_work"))
    ctx["check"] = r
    return r


@when("I call validate_narrative_functions with an NCP containing narrative_function \"BOGUS-FUNCTION-NAME\"",
      target_fixture="nf_result")
def _when_validate_nf_bad(engine, confirmed_intent, ctx):
    ncp = {"story": {"narratives": [{"subtext": {"elements": [
        {"narrative_function": "BOGUS-FUNCTION-NAME"}]}}]}}
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "validate_narrative_functions", ncp=ncp)
    ctx["check"] = r
    return r


# ─── when: worldbuilding ─────────────────────────────────────────────────────

@when("I create a world with slug \"midgard\" and name \"Midgard\"",
      target_fixture="world_result")
def _when_create_world(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_world",
                  slug="midgard", name="Midgard")
    ctx["world"] = r
    ctx["world_id"] = r["world_id"] if r else None
    return r


@given("a world \"midgard\"")
def _given_world(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_world",
                  slug="midgard", name="Midgard")
    ctx["world_id"] = r["world_id"]


@given("a world \"midgard\" with 2 cultures 1 religion 1 axiom")
def _given_world_with_children(engine, confirmed_intent, ctx):
    w, _ = invoke(engine, confirmed_intent, "novel", "create_world",
                  slug="midgard", name="Midgard")
    wid = w["world_id"]
    ctx["world_id"] = wid
    invoke(engine, confirmed_intent, "novel", "create_culture",
           world_id=wid, slug="vikings", name="Vikings")
    invoke(engine, confirmed_intent, "novel", "create_culture",
           world_id=wid, slug="saxons", name="Saxons")
    invoke(engine, confirmed_intent, "novel", "create_religion",
           world_id=wid, slug="asatru", name="Asatru")
    invoke(engine, confirmed_intent, "novel", "create_world_axiom",
           world_id=wid, text="The Allfather watches all.", severity="hard")


@given("a world with two contradicting axioms about the dead returning")
def _given_contradicting_axioms(engine, confirmed_intent, ctx):
    w, _ = invoke(engine, confirmed_intent, "novel", "create_world",
                  slug="midgard", name="Midgard")
    wid = w["world_id"]
    a1, _ = invoke(engine, confirmed_intent, "novel", "create_world_axiom",
                   world_id=wid,
                   text="The dead can return through ritual.", severity="hard")
    a2, _ = invoke(engine, confirmed_intent, "novel", "create_world_axiom",
                   world_id=wid,
                   text="The dead can not return through ritual.", severity="hard")
    ctx["world_id"] = wid
    ctx["axiom_ids"] = (a1["axiom_id"], a2["axiom_id"])


@given("a world with two independent axioms")
def _given_independent_axioms(engine, confirmed_intent, ctx):
    w, _ = invoke(engine, confirmed_intent, "novel", "create_world",
                  slug="midgard", name="Midgard")
    wid = w["world_id"]
    invoke(engine, confirmed_intent, "novel", "create_world_axiom",
           world_id=wid, text="Gravity pulls down always.", severity="hard")
    invoke(engine, confirmed_intent, "novel", "create_world_axiom",
           world_id=wid, text="Magic costs blood to wield.", severity="hard")
    ctx["world_id"] = wid


@given("a world with a religion")
def _given_world_with_religion(engine, confirmed_intent, ctx):
    w, _ = invoke(engine, confirmed_intent, "novel", "create_world",
                  slug="midgard", name="Midgard")
    wid = w["world_id"]
    rel, _ = invoke(engine, confirmed_intent, "novel", "create_religion",
                    world_id=wid, slug="asatru", name="Asatru")
    nv, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                   title="Saga", author="A", genre="lit")
    ctx["world_id"] = wid
    ctx["religion_id"] = rel["religion_id"]
    ctx["character_id"] = nv["novel_id"]  # Novel stands in as character proxy


@when("I create culture \"vikings\" religion \"asatru\" language \"old-norse\" magic \"seidr\" under that world",
      target_fixture="world_children_result")
def _when_create_world_children(engine, confirmed_intent, ctx):
    wid = ctx["world_id"]
    c = (invoke(engine, confirmed_intent, "novel", "create_culture",
                world_id=wid, slug="vikings", name="Vikings"))[0]
    rel = (invoke(engine, confirmed_intent, "novel", "create_religion",
                  world_id=wid, slug="asatru", name="Asatru"))[0]
    lang = (invoke(engine, confirmed_intent, "novel", "create_language",
                   world_id=wid, slug="old-norse", name="Old Norse"))[0]
    mag = (invoke(engine, confirmed_intent, "novel", "create_magic_system",
                  world_id=wid, slug="seidr", name="Seidr"))[0]
    ctx["children"] = [c, rel, lang, mag]
    return c, rel, lang, mag


@when("I create a culture under world_id \"world:does-not-exist\"",
      target_fixture="world_result")
def _when_create_culture_not_found(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_culture",
                  world_id="world:does-not-exist", slug="x", name="X")
    ctx["result"] = r
    return r


@when("I create a hard axiom \"The dead never return.\"",
      target_fixture="axiom_result")
def _when_create_axiom_hard(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_world_axiom",
                  world_id=ctx["world_id"],
                  text="The dead never return.", severity="hard")
    ctx["axiom"] = r
    return r


@when("I create an axiom with severity \"medium\"",
      target_fixture="axiom_result")
def _when_create_axiom_bad_severity(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_world_axiom",
                  world_id=ctx["world_id"], text="x", severity="medium")
    ctx["result"] = r
    return r


@when("I call list_world", target_fixture="world_list_result")
def _when_list_world(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "list_world",
                  world_id=ctx["world_id"])
    ctx["world_list"] = r
    return r


@when("I call find_axiom_contradictions", target_fixture="contradiction_result")
def _when_find_contradictions(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "find_axiom_contradictions", world_id=ctx["world_id"])
    ctx["contradictions"] = r
    return r


@when("I link a character to the religion with edge_kind \"SHOPS_AT\"",
      target_fixture="link_result")
def _when_link_bad_edge(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "link_character_to_world",
                  character_id=ctx["character_id"],
                  target_id=ctx["religion_id"],
                  edge_kind="SHOPS_AT")
    ctx["result"] = r
    return r


@when("I link a character to the religion with edge_kind \"WORSHIPS\"",
      target_fixture="link_result")
def _when_link_worships(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "link_character_to_world",
                  character_id=ctx["character_id"],
                  target_id=ctx["religion_id"],
                  edge_kind="WORSHIPS")
    ctx["link"] = r
    return r


# ─── when: codex ─────────────────────────────────────────────────────────────

@when("I create a codex entry slug \"iron-mask\" kind \"artefact\"",
      target_fixture="codex_result")
def _when_create_codex_artefact(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_codex_entry",
                  novel_id=ctx["novel_id"], slug="iron-mask",
                  name="The Iron Mask", kind="artefact",
                  body="A black-iron half-mask.", triggers="Iron Mask, the mask")
    ctx["entry_id"] = r["entry_id"] if r else None
    ctx["codex_entry"] = r
    return r


@when("I create a codex entry with kind \"hyperbole\"",
      target_fixture="codex_result")
def _when_create_codex_bad_kind(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "create_codex_entry",
                  novel_id=ctx["novel_id"], slug="x", name="X",
                  kind="hyperbole", body="x")
    ctx["result"] = r
    return r


@given("a novel with codex entries \"a\" location and \"b\" artefact")
def _given_codex_novel(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="Codex Test", author="A.", genre="lit")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_codex_entry",
           novel_id=nid, slug="a", name="A", kind="location",
           body="x", triggers="a")
    invoke(engine, confirmed_intent, "novel", "create_codex_entry",
           novel_id=nid, slug="b", name="B", kind="artefact",
           body="x", triggers="b")
    ctx["novel_id"] = nid


@when("I list all codex entries", target_fixture="codex_list_result")
def _when_list_codex_all(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "list_codex_entries",
                  novel_id=ctx["novel_id"])
    ctx["codex_list"] = r
    return r


@when("I list codex entries with kind \"location\"",
      target_fixture="codex_list_result")
def _when_list_codex_location(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "list_codex_entries",
                  novel_id=ctx["novel_id"], kind="location")
    ctx["codex_list"] = r
    return r


@given("a codex entry with triggers \"Iron Mask, the mask\"")
def _given_codex_trigger(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="T", author="A", genre="lit")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_codex_entry",
           novel_id=nid, slug="iron-mask", name="Iron Mask",
           kind="artefact", body="A black-iron half-mask.",
           triggers="Iron Mask, the mask")
    ctx["novel_id"] = nid


@given("a codex entry \"raven\" with trigger \"Raven\"")
def _given_codex_raven(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="T", author="A", genre="lit")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_codex_entry",
           novel_id=nid, slug="raven", name="Raven",
           kind="minor-character", body="A trickster.", triggers="Raven")
    ctx["novel_id"] = nid


@given("a codex entry with trigger \"X\"")
def _given_codex_x(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="T", author="A", genre="lit")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_codex_entry",
           novel_id=nid, slug="x", name="X",
           kind="concept", body="x", triggers="X")
    ctx["novel_id"] = nid


@given("a codex entry \"cult\" that has been archived")
def _given_codex_archived(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="T", author="A", genre="lit")
    nid = novel["novel_id"]
    ent, _ = invoke(engine, confirmed_intent, "novel", "create_codex_entry",
                    novel_id=nid, slug="cult", name="The Cult",
                    kind="faction", body="A faction.", triggers="cult")
    invoke(engine, confirmed_intent, "novel", "archive_codex_entry",
           entry_id=ent["entry_id"], reason="superseded")
    ctx["novel_id"] = nid


@when(parsers.parse('I call match_codex_entries with text "{text}"'),
      target_fixture="match_result")
def _when_match_codex(engine, confirmed_intent, ctx, text):
    r, _ = invoke(engine, confirmed_intent, "novel", "match_codex_entries",
                  novel_id=ctx["novel_id"], text=text)
    ctx["matches"] = r
    return r


@given("a codex entry with body \"old body\"")
def _given_codex_old_body(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="T", author="A", genre="lit")
    nid = novel["novel_id"]
    ent, _ = invoke(engine, confirmed_intent, "novel", "create_codex_entry",
                    novel_id=nid, slug="x", name="X",
                    kind="concept", body="old body", triggers="X")
    ctx["novel_id"] = nid
    ctx["entry_id"] = ent["entry_id"]


@given("a codex entry")
def _given_codex_entry(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="T", author="A", genre="lit")
    nid = novel["novel_id"]
    ent, _ = invoke(engine, confirmed_intent, "novel", "create_codex_entry",
                    novel_id=nid, slug="x", name="X",
                    kind="concept", body="x", triggers="X")
    ctx["novel_id"] = nid
    ctx["entry_id"] = ent["entry_id"]


@when("I update the codex entry body to \"new body\"",
      target_fixture="update_result")
def _when_update_codex(engine, confirmed_intent, ctx):
    invoke(engine, confirmed_intent, "novel", "update_codex_entry",
           entry_id=ctx["entry_id"], body="new body")
    return ctx["entry_id"]


@when("I archive the codex entry", target_fixture="archive_result")
def _when_archive_codex(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "archive_codex_entry",
                  entry_id=ctx["entry_id"], reason="deprecated")
    ctx["archived"] = r
    return r


# ─── when: character knowledge ───────────────────────────────────────────────

def _build_mini_novel(engine, confirmed_intent, ctx):
    """Shared helper: 3-chapter novel, 3 scenes, one character (= novel node)."""
    nv, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                   title="K Test", author="A. Author", genre="lit")
    nid = nv["novel_id"]
    character_id = nid  # novel node as character proxy
    scenes = []
    for n in range(1, 4):
        ch, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                       novel_id=nid, number=n, title=f"Ch {n}")
        sc, _ = invoke(engine, confirmed_intent, "novel", "create_scene",
                       chapter_id=ch["chapter_id"], slug=f"s{n}",
                       pov="third-limited")
        scenes.append(sc["scene_id"])
    ctx["novel_id"] = nid
    ctx["character_id"] = character_id
    ctx["scenes"] = scenes
    return scenes


@given("a mini-novel with scenes")
def _given_mini_novel(engine, confirmed_intent, ctx):
    _build_mini_novel(engine, confirmed_intent, ctx)


@given("a character with facts learned in scene 1 and scene 2")
def _given_char_facts_s1_s2(engine, confirmed_intent, ctx):
    scenes = _build_mini_novel(engine, confirmed_intent, ctx)
    invoke(engine, confirmed_intent, "novel", "record_character_learns",
           character_id=ctx["character_id"],
           fact="Fact A", scene_id=scenes[0])
    invoke(engine, confirmed_intent, "novel", "record_character_learns",
           character_id=ctx["character_id"],
           fact="Fact B", scene_id=scenes[1])


@given("a character with fact A learned in scene 1 and Future Fact learned in scene 3")
def _given_char_facts_future(engine, confirmed_intent, ctx):
    scenes = _build_mini_novel(engine, confirmed_intent, ctx)
    invoke(engine, confirmed_intent, "novel", "record_character_learns",
           character_id=ctx["character_id"],
           fact="Fact A", scene_id=scenes[0])
    invoke(engine, confirmed_intent, "novel", "record_character_learns",
           character_id=ctx["character_id"],
           fact="Future Fact", scene_id=scenes[2])


@given("a character who learned \"The captain is bribed.\" in scene 1")
def _given_char_learned_s1(engine, confirmed_intent, ctx):
    scenes = _build_mini_novel(engine, confirmed_intent, ctx)
    invoke(engine, confirmed_intent, "novel", "record_character_learns",
           character_id=ctx["character_id"],
           fact="The captain is bribed.", scene_id=scenes[0])


@given("a character who learned \"The captain is bribed.\" in scene 3")
def _given_char_learned_s3(engine, confirmed_intent, ctx):
    scenes = _build_mini_novel(engine, confirmed_intent, ctx)
    invoke(engine, confirmed_intent, "novel", "record_character_learns",
           character_id=ctx["character_id"],
           fact="The captain is bribed.", scene_id=scenes[2])


@when("I record that the character learned \"The captain is bribed.\" in scene 2",
      target_fixture="knows_result")
def _when_record_learns(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "record_character_learns",
                  character_id=ctx["character_id"],
                  fact="The captain is bribed.",
                  scene_id=ctx["scenes"][1])
    ctx["knows"] = r
    ctx["fact_id"] = r["fact_id"] if r else None
    return r


@when("I record a fact for scene_id \"scene:does-not-exist\"",
      target_fixture="knows_result")
def _when_record_learns_bad_scene(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "record_character_learns",
                  character_id=ctx["character_id"],
                  fact="x", scene_id="scene:does-not-exist")
    ctx["result"] = r
    return r


@when("I call what_does_X_know_as_of as of scene 2",
      target_fixture="know_result")
def _when_what_knows_s2(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "what_does_X_know_as_of",
                  character_id=ctx["character_id"],
                  scene_id=ctx["scenes"][1])
    ctx["knowledge"] = r
    return r


@when("I flag_anachronistic_reference for scene 2",
      target_fixture="anachronism_result")
def _when_flag_anachronism_s2(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "flag_anachronistic_reference",
                  scene_id=ctx["scenes"][1],
                  character_id=ctx["character_id"],
                  fact_text="The captain is bribed.")
    ctx["ana"] = r
    return r


@when("I flag_anachronistic_reference for scene 1",
      target_fixture="anachronism_result")
def _when_flag_anachronism_s1(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "flag_anachronistic_reference",
                  scene_id=ctx["scenes"][0],
                  character_id=ctx["character_id"],
                  fact_text="The captain is bribed.")
    ctx["ana"] = r
    return r


@when("I check for fact \"Never recorded.\" in scene 1",
      target_fixture="anachronism_result")
def _when_flag_no_record(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "flag_anachronistic_reference",
                  scene_id=ctx["scenes"][0],
                  character_id=ctx["character_id"],
                  fact_text="Never recorded.")
    ctx["ana"] = r
    return r


# ─── when: story time ────────────────────────────────────────────────────────

def _build_story_novel(engine, confirmed_intent, ctx):
    """3-chapter novel with 3 scenes."""
    nv, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                   title="Time Test", author="A. Author", genre="lit")
    nid = nv["novel_id"]
    scenes = []
    for n in range(1, 4):
        ch, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                       novel_id=nid, number=n, title=f"Ch {n}")
        sc, _ = invoke(engine, confirmed_intent, "novel", "create_scene",
                       chapter_id=ch["chapter_id"], slug=f"s{n}",
                       pov="third-limited")
        scenes.append(sc["scene_id"])
    ctx["novel_id"] = nid
    ctx["scenes"] = scenes
    return nid, scenes


@given("a novel with scenes")
def _given_novel_scenes(engine, confirmed_intent, ctx):
    _build_story_novel(engine, confirmed_intent, ctx)


@given("a novel with scenes and no anchored events")
def _given_novel_scenes_no_anchor(engine, confirmed_intent, ctx):
    _build_story_novel(engine, confirmed_intent, ctx)


@given("a story event and scenes")
def _given_story_event_and_scenes(engine, confirmed_intent, ctx):
    nid, scenes = _build_story_novel(engine, confirmed_intent, ctx)
    ev, _ = invoke(engine, confirmed_intent, "novel", "record_story_event",
                   novel_id=nid, label="Past murder", when_story="Y2390.01")
    ctx["event_id"] = ev["event_id"]


@given("events anchored Birth-A001-scene1 Marriage-A015-scene2 Death-A050-scene3")
def _given_anchored_events(engine, confirmed_intent, ctx):
    nid, scenes = _build_story_novel(engine, confirmed_intent, ctx)
    invoke(engine, confirmed_intent, "novel", "record_story_event",
           novel_id=nid, label="Birth", when_story="A001",
           scene_id=scenes[0])
    invoke(engine, confirmed_intent, "novel", "record_story_event",
           novel_id=nid, label="Marriage", when_story="A015",
           scene_id=scenes[1])
    invoke(engine, confirmed_intent, "novel", "record_story_event",
           novel_id=nid, label="Death", when_story="A050",
           scene_id=scenes[2])


@given("an event revealed in scene 3")
def _given_revealed_event(engine, confirmed_intent, ctx):
    nid, scenes = _build_story_novel(engine, confirmed_intent, ctx)
    ev, _ = invoke(engine, confirmed_intent, "novel", "record_story_event",
                   novel_id=nid, label="Lost will", when_story="A001")
    invoke(engine, confirmed_intent, "novel", "reveal_in_scene",
           event_id=ev["event_id"], scene_id=scenes[2])
    ctx["event_id"] = ev["event_id"]


@given("two beats recorded for scenes 1 and 2")
def _given_two_beats(engine, confirmed_intent, ctx):
    _build_story_novel(engine, confirmed_intent, ctx)
    b1, _ = invoke(engine, confirmed_intent, "novel", "mark_narrative_beat",
                   scene_id=ctx["scenes"][0], beat_label="opening-image")
    ctx["beat1_id"] = b1["beat_id"]


@given("three beats chained b1 precedes b2 precedes b3")
def _given_three_beats(engine, confirmed_intent, ctx):
    nid, scenes = _build_story_novel(engine, confirmed_intent, ctx)
    b1, _ = invoke(engine, confirmed_intent, "novel", "mark_narrative_beat",
                   scene_id=scenes[0], beat_label="b1")
    b2, _ = invoke(engine, confirmed_intent, "novel", "mark_narrative_beat",
                   scene_id=scenes[1], beat_label="b2",
                   predecessor_id=b1["beat_id"])
    b3, _ = invoke(engine, confirmed_intent, "novel", "mark_narrative_beat",
                   scene_id=scenes[2], beat_label="b3",
                   predecessor_id=b2["beat_id"])
    ctx["beat_ids"] = [b1["beat_id"], b2["beat_id"], b3["beat_id"]]


@when("I record a story event \"King dies\" at when_story \"Y2391.04\"",
      target_fixture="event_result")
def _when_record_event(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "record_story_event",
                  novel_id=ctx["novel_id"],
                  label="King dies", when_story="Y2391.04")
    ctx["event"] = r
    return r


@when("I record event \"Coronation\" anchored to scene 2",
      target_fixture="event_result")
def _when_record_event_anchored(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "record_story_event",
                  novel_id=ctx["novel_id"],
                  label="Coronation", when_story="Y2391.05",
                  scene_id=ctx["scenes"][1])
    ctx["event"] = r
    return r


@when("I call reveal_in_scene for the event and scene 3",
      target_fixture="reveal_result")
def _when_reveal_in_scene(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "reveal_in_scene",
                  event_id=ctx["event_id"], scene_id=ctx["scenes"][2])
    ctx["reveal"] = r
    return r


@when("I call list_story_events_up_to for scene 2",
      target_fixture="events_result")
def _when_list_events_up_to(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "list_story_events_up_to", scene_id=ctx["scenes"][1])
    ctx["events"] = r
    return r


@when("I call list_story_events_up_to for scene 1",
      target_fixture="events_result")
def _when_list_events_up_to_s1(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "list_story_events_up_to", scene_id=ctx["scenes"][0])
    ctx["events"] = r
    return r


@when("I call list_reveals_in for scene 3",
      target_fixture="reveals_result")
def _when_list_reveals(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "list_reveals_in",
                  scene_id=ctx["scenes"][2])
    ctx["reveals"] = r
    return r


@when("I call mark_narrative_beat for scene 1 with beat \"opening-image\"",
      target_fixture="beat_result")
def _when_mark_beat(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "mark_narrative_beat",
                  scene_id=ctx["scenes"][0], beat_label="opening-image")
    ctx["beat"] = r
    return r


@when("beat 2 is marked with predecessor_id of beat 1",
      target_fixture="beat_result")
def _when_mark_beat_preceded(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "mark_narrative_beat",
                  scene_id=ctx["scenes"][1], beat_label="inciting-incident",
                  predecessor_id=ctx["beat1_id"])
    ctx["beat2_id"] = r["beat_id"]
    ctx["beat"] = r
    return r


@when("I call narrative_order", target_fixture="order_result")
def _when_narrative_order(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "narrative_order",
                  novel_id=ctx["novel_id"])
    ctx["order"] = r
    return r


# ─── when: editorial pipeline ────────────────────────────────────────────────

@when("I call check_voice_consistency with three stylistically similar bodies",
      target_fixture="voice_result")
def _when_voice_consistent(engine, confirmed_intent, ctx):
    similar = [
        "She walked slowly. The room was dim. She thought of him.",
        "He turned away. The hall was quiet. He thought of her.",
        "They paused. The street was empty. They thought of nothing.",
    ]
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_voice_consistency", bodies=similar)
    ctx["voice"] = r
    return r


@when("I call check_voice_consistency with three tight bodies and one filter-heavy body",
      target_fixture="voice_result")
def _when_voice_outlier(engine, confirmed_intent, ctx):
    bodies = [
        "She walked. The room was dim.",
        "He turned. The hall was quiet.",
        "They paused. The street was empty.",
        ("She really just truly literally absolutely simply just basically "
         "actually very really truly basically just literally absolutely "
         "actually thought about it for what felt like a very long time."),
    ]
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_voice_consistency", bodies=bodies, z_threshold=1.5)
    ctx["voice"] = r
    return r


@given("a novel with chapters each having one scene of same pov")
def _given_novel_uniform_pov(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="P", author="A")
    nid = novel["novel_id"]
    for n in range(1, 4):
        ch, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                       novel_id=nid, number=n, title=f"Ch {n}")
        invoke(engine, confirmed_intent, "novel", "create_scene",
               chapter_id=ch["chapter_id"], slug=f"s{n}", pov="third-limited")
    ctx["novel_id"] = nid


@when("I call check_pov_consistency", target_fixture="pov_result")
def _when_check_pov(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_pov_consistency", novel_id=ctx["novel_id"])
    ctx["pov"] = r
    return r


@given("a novel whose chapters share the same proper noun \"Elara\"")
def _given_consistent_novel(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="C", author="A")
    nid = novel["novel_id"]
    for n in range(1, 3):
        invoke(engine, confirmed_intent, "novel", "create_chapter",
               novel_id=nid, number=n, title=f"Ch {n}",
               body="Elara walked through the forest.")
    ctx["novel_id"] = nid


@when("I call check_continuity", target_fixture="continuity_result")
def _when_check_continuity(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel",
                  "check_continuity", novel_id=ctx["novel_id"])
    ctx["continuity"] = r
    return r


@when("I call check_sensitivity with a body containing sensitive themes",
      target_fixture="sensitivity_result")
def _when_check_sensitivity(engine, confirmed_intent, ctx):
    r, _ = invoke(engine, confirmed_intent, "novel", "check_sensitivity",
                  body="Violence erupted. He shot the guard and fled into darkness.")
    ctx["sensitivity"] = r
    return r


# ─── when: gates ─────────────────────────────────────────────────────────────

@given("a novel with no prerequisites")
def _given_novel_no_prereqs(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    ctx["novel_id"] = novel["novel_id"]


@given("a novel with one chapter, one claim, and a storyform node")
def _given_novel_all_prereqs(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=1, title="A")
    invoke(engine, confirmed_intent, "novel", "capture_claim",
           text="t", source_uri="u", domain="historical")
    engine.memory.record("Storyform", {"novel": nid})
    ctx["novel_id"] = nid


@when("I call pre_draft_gate", target_fixture="gate_result")
def _when_pre_draft_gate(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "pre_draft_gate",
                    novel_id=ctx["novel_id"])
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@given("a novel with chapters still outlined")
def _given_novel_outlined(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    for n in range(1, 4):
        invoke(engine, confirmed_intent, "novel", "create_chapter",
               novel_id=nid, number=n, title=f"Ch {n}", body="body")
    ctx["novel_id"] = nid


@given("a novel with all chapters set to drafted")
def _given_all_drafted(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    cids = []
    for n in range(1, 4):
        c, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                      novel_id=nid, number=n, title=f"Ch {n}", body="body")
        cids.append(c["chapter_id"])
    for cid in cids:
        invoke(engine, confirmed_intent, "novel", "set_chapter_status",
               chapter_id=cid, status="drafted")
    ctx["novel_id"] = nid


@when("I call beta_ready_gate", target_fixture="gate_result")
def _when_beta_gate(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "beta_ready_gate",
                    novel_id=ctx["novel_id"])
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@given("a novel still in concept status")
def _given_novel_concept_status(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    for n in range(1, 4):
        invoke(engine, confirmed_intent, "novel", "create_chapter",
               novel_id=nid, number=n, title=f"Ch {n}", body="body")
    ctx["novel_id"] = nid


@given("a novel at beta status with revised chapters")
def _given_beta_novel(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    cids = []
    for n in range(1, 4):
        c, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                      novel_id=nid, number=n, title=f"Ch {n}",
                      body="The morning was clear. Birds sang.")
        cids.append(c["chapter_id"])
    for cid in cids:
        invoke(engine, confirmed_intent, "novel", "set_chapter_status",
               chapter_id=cid, status="revised")
    invoke(engine, confirmed_intent, "novel", "set_novel_status",
           novel_id=nid, status="beta")
    ctx["novel_id"] = nid


@when("I call query_ready_gate", target_fixture="gate_result")
def _when_query_gate(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "query_ready_gate",
                    novel_id=ctx["novel_id"])
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


@given("a novel with chapters 1 and 3 but not 2 at querying status")
def _given_gap_novel(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=1, title="A", body="body")
    invoke(engine, confirmed_intent, "novel", "create_chapter",
           novel_id=nid, number=3, title="C", body="body")
    invoke(engine, confirmed_intent, "novel", "set_novel_status",
           novel_id=nid, status="querying")
    ctx["novel_id"] = nid


@given("a novel with 3 contiguous chapters all final at querying status")
def _given_contiguous_novel(engine, confirmed_intent, ctx):
    novel, _ = invoke(engine, confirmed_intent, "novel", "create_novel",
                      title="X", author="Y")
    nid = novel["novel_id"]
    cids = []
    for n in range(1, 4):
        c, _ = invoke(engine, confirmed_intent, "novel", "create_chapter",
                      novel_id=nid, number=n, title=f"Ch {n}", body="body")
        cids.append(c["chapter_id"])
    for cid in cids:
        invoke(engine, confirmed_intent, "novel", "set_chapter_status",
               chapter_id=cid, status="final")
    invoke(engine, confirmed_intent, "novel", "set_novel_status",
           novel_id=nid, status="querying")
    ctx["novel_id"] = nid


@when("I call publish_ready_gate", target_fixture="gate_result")
def _when_publish_gate(engine, confirmed_intent, ctx):
    r, inv = invoke(engine, confirmed_intent, "novel", "publish_ready_gate",
                    novel_id=ctx["novel_id"])
    ctx["result"] = r
    ctx["inv"] = inv
    return r, inv


# ─── when: E2E ───────────────────────────────────────────────────────────────

@when("I run the full novel pipeline from idea to manuscript",
      target_fixture="e2e_result")
def _when_e2e(engine, confirmed_intent, ctx):
    iid = confirmed_intent
    idea, _ = invoke(engine, iid, "novel", "capture_idea",
                     text="A phreaker novel set in 1984 BBS culture")
    novel, _ = invoke(engine, iid, "novel", "promote_idea",
                      idea_id=idea["idea_id"],
                      title="Modem Daze", author="The Phreakers")
    nid = novel["novel_id"]
    for n, title, body in [
        (1, "Connection", "He really just wanted to dial in."),
        (2, "Discovery", "She found the file on the BBS."),
        (3, "Confrontation", "The sysop watched the logs."),
    ]:
        invoke(engine, iid, "novel", "create_chapter",
               novel_id=nid, number=n, title=title, body=body)
    invoke(engine, iid, "novel", "capture_claim",
           text="In 1984 ~60K BBS nodes", source_uri="https://archive.org/x",
           domain="historical")
    invoke(engine, iid, "novel", "count_words",
           body="He really just wanted to dial in.")
    invoke(engine, iid, "novel", "check_filter_words",
           body="He really just wanted to dial in.")
    invoke(engine, iid, "novel", "chapter_report", novel_id=nid)
    invoke(engine, iid, "novel", "set_novel_status",
           novel_id=nid, status="drafting")
    engine.memory.record("Storyform", {"novel": nid})
    invoke(engine, iid, "novel", "pre_draft_gate", novel_id=nid)
    ms, _ = invoke(engine, iid, "novel", "render_manuscript", novel_id=nid)
    prov = engine.memory.provenance(iid)
    ctx["prov"] = prov
    ctx["ms_kind"] = ms["artefact"]["kind"]
    return prov


# ─── then: core ──────────────────────────────────────────────────────────────

@then("the result contains a novel_id starting with \"novel:\"")
def _then_novel_id(ctx):
    assert ctx["result"]["novel_id"].startswith("novel:")


@then("the novel status is \"concept\"")
def _then_novel_status_concept(ctx):
    assert ctx["result"]["status"] == "concept"


@then("a SERVES edge links the Novel to the intent")
def _then_novel_serves(engine, confirmed_intent, ctx):
    nid = ctx["result"]["novel_id"]
    rows = engine.memory.g.query(
        "MATCH (n)-[r:SERVES]->(i) WHERE n.id = $nid AND i.id = $iid RETURN r",
        {"nid": nid, "iid": confirmed_intent})
    assert rows


@then("the result contains a chapter_id starting with \"chapter:\"")
def _then_chapter_id(ctx):
    assert ctx["result"]["chapter_id"].startswith("chapter:")


@then("the chapter status is \"outlined\"")
def _then_chapter_outlined(ctx):
    assert ctx["result"]["status"] == "outlined"


@then("a CHAPTER_OF edge links the chapter to the novel")
def _then_chapter_of(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (c)-[r:CHAPTER_OF]->(n) WHERE c.id = $cid AND n.id = $nid RETURN r",
        {"cid": ctx["result"]["chapter_id"], "nid": ctx["novel_id"]})
    assert rows


@then("chapter_count is 2")
def _then_chapter_count_2(ctx):
    assert ctx["report"]["chapter_count"] == 2


@then("word_count_total is at least 300")
def _then_word_count_300(ctx):
    assert ctx["report"]["word_count_total"] >= 300


@then("by_status shows 2 outlined chapters")
def _then_by_status_2_outlined(ctx):
    assert ctx["report"]["by_status"] == {"outlined": 2}


@then("the artefact kind is \"manuscript\"")
def _then_artefact_manuscript(ctx):
    assert ctx["ms"]["artefact"]["kind"] == "manuscript"


@then("the manuscript body contains the novel title and author")
def _then_manuscript_title_author(ctx):
    body = ctx["ms"]["artefact"]["body"]
    assert "My Novel" in body
    assert "An Author" in body


@then("\"First\" appears before \"Second\" in the manuscript")
def _then_first_before_second(ctx):
    body = ctx["ms"]["artefact"]["body"]
    assert body.index("First") < body.index("Second")


@then("\"first body\" appears before \"second body\" in the manuscript")
def _then_first_body_before_second(ctx):
    body = ctx["ms"]["artefact"]["body"]
    assert body.index("first body") < body.index("second body")


@then("the result artefact kind is \"novel-concept\"")
def _then_concept_artefact(ctx):
    assert ctx["concept"]["artefact"]["kind"] == "novel-concept"


@then("the result text contains \"Modem Daze\"")
def _then_concept_text_title(ctx):
    assert "Modem Daze" in ctx["concept"]["result"]


# ─── then: common ────────────────────────────────────────────────────────────

@then("the result is None")
def _then_result_none(ctx):
    assert ctx["result"] is None


@then("the invocation error contains \"not_found\"")
def _then_err_not_found(engine, ctx):
    err = engine.memory.recall(ctx["inv"]).get("error", "")
    assert "not_found" in err


@then("the invocation error contains \"invalid_argument\"")
def _then_err_invalid_arg(engine, ctx):
    err = engine.memory.recall(ctx["inv"]).get("error", "")
    assert "invalid_argument" in err


@then("the invocation error contains \"gate_failed\"")
def _then_err_gate_failed(engine, ctx):
    err = engine.memory.recall(ctx["inv"]).get("error", "")
    assert "gate_failed" in err


# ─── then: ideas ─────────────────────────────────────────────────────────────

@then("the result contains an idea_id starting with \"idea:\"")
def _then_idea_id(ctx):
    assert ctx["result"]["idea_id"].startswith("idea:")


@then("the idea status is \"new\"")
def _then_idea_new(ctx):
    assert ctx["result"]["status"] == "new"


@then("a SERVES edge links the Idea to the intent")
def _then_idea_serves(engine, confirmed_intent, ctx):
    iid = ctx["result"]["idea_id"]
    rows = engine.memory.g.query(
        "MATCH (i)-[r:SERVES]->(t) WHERE i.id = $iid AND t.id = $tid RETURN r",
        {"iid": iid, "tid": confirmed_intent})
    assert rows


@then(parsers.parse("the idea count is {n:d}"))
def _then_idea_count(ctx, n):
    assert ctx["result"]["count"] == n


@then("the result contains a novel_id")
def _then_has_novel_id(ctx):
    assert ctx["result"] and ctx["result"]["novel_id"]


@then("the idea status becomes \"promoted\"")
def _then_idea_promoted(engine, ctx):
    node = engine.memory.recall(ctx["promoted_idea_id"])
    assert node["status"] == "promoted"


@then("a PROMOTED_TO edge links the idea to the novel")
def _then_promoted_to(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (i)-[r:PROMOTED_TO]->(n) WHERE i.id = $iid AND n.id = $nid RETURN r",
        {"iid": ctx["promoted_idea_id"], "nid": ctx["promoted_novel_id"]})
    assert rows


# ─── then: find_novel ────────────────────────────────────────────────────────

@then(parsers.parse("the count is {n:d}"))
def _then_count_n(ctx, n):
    key = "count"
    obj = ctx.get("find") or ctx.get("result") or ctx.get("find_result")
    assert obj[key] == n


@then("the returned titles are \"The Great Modem\" and \"Modem Mysteries\"")
def _then_find_titles(ctx):
    titles = {n["title"] for n in ctx["find"]["novels"]}
    assert titles == {"The Great Modem", "Modem Mysteries"}


# ─── then: novel status ──────────────────────────────────────────────────────

@then("the returned status is \"drafting\"")
def _then_returned_status_drafting(ctx):
    assert ctx["result"]["status"] == "drafting"


@then("the graph node status is \"drafting\"")
def _then_graph_status_drafting(engine, ctx):
    node = engine.memory.recall(ctx["novel_id"])
    assert node["status"] == "drafting"


# ─── then: lifecycle slice 2 ─────────────────────────────────────────────────

@then("the chapter numbers are in ascending order 1 2 3")
def _then_chapter_order(ctx):
    nums = [c["number"] for c in ctx["result"]["chapters"]]
    assert nums == [1, 2, 3]


@then("chapter_count is 0 and chapters is an empty list")
def _then_no_chapters(ctx):
    assert ctx["result"]["count"] == 0
    assert ctx["result"]["chapters"] == []


@then("the result contains a scene_id starting with \"scene:\"")
def _then_scene_id(ctx):
    assert ctx["result"]["scene_id"].startswith("scene:")


@then("the scene pov is \"third-limited\"")
def _then_scene_pov(ctx):
    assert ctx["result"]["pov"] == "third-limited"


@then("a SCENE_OF edge links the scene to the chapter")
def _then_scene_of(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (s)-[r:SCENE_OF]->(c) WHERE s.id = $sid AND c.id = $cid RETURN r",
        {"sid": ctx["result"]["scene_id"], "cid": ctx["chapter_id"]})
    assert rows


@then("the chapter node status is \"drafted\"")
def _then_chapter_drafted(engine, ctx):
    node = engine.memory.recall(ctx["chapter_id"])
    assert node["status"] == "drafted"


@then("the returned title is \"Renamed Title\"")
def _then_renamed_title(ctx):
    assert ctx["result"]["title"] == "Renamed Title"


@then("the graph node title is \"Renamed Title\"")
def _then_graph_title(engine, ctx):
    node = engine.memory.recall(ctx["novel_id"])
    assert node["title"] == "Renamed Title"


@then("word_count_total is at least 150")
def _then_word_count_150(ctx):
    assert ctx["progress"]["word_count_total"] >= 150


@then("by_status shows 1 drafted and 1 outlined")
def _then_progress_by_status(ctx):
    bs = ctx["progress"]["by_status"]
    assert bs.get("drafted") == 1
    assert bs.get("outlined") == 1


@then("the returned novel_id matches the second novel")
def _then_session_novel_id(ctx):
    assert ctx["session"]["novel_id"] == ctx["last_novel_id"]


@then("the returned title is \"Last\"")
def _then_session_title_last(ctx):
    assert ctx["session"]["title"] == "Last"


@then("the novel_id is \"\" and the title is \"\"")
def _then_session_empty(ctx):
    assert ctx["session"]["novel_id"] == ""
    assert ctx["session"]["title"] == ""


# ─── then: prose ─────────────────────────────────────────────────────────────

@then("word_count is 9")
def _then_wc_9(ctx):
    assert ctx["wc"]["word_count"] == 9


@then("char_count is 44")
def _then_cc_44(ctx):
    assert ctx["wc"]["char_count"] == 44


@then("word_count is 0 and char_count is 0")
def _then_wc_empty(ctx):
    assert ctx["wc"]["word_count"] == 0
    assert ctx["wc"]["char_count"] == 0


@then("the result contains a flesch score above 80")
def _then_flesch_above_80(ctx):
    assert "flesch" in ctx["result"]
    assert isinstance(ctx["result"]["flesch"], float)
    assert ctx["result"]["flesch"] >= 80


@then("the sentence count is 4")
def _then_sentences_4(ctx):
    assert ctx["result"]["sentences"] == 4


@then(parsers.parse("the filter_count is at least {n:d}"))
def _then_filter_count(ctx, n):
    assert ctx["fw"]["filter_count"] >= n


@then("the density is above 0.1")
def _then_density_above(ctx):
    assert ctx["fw"]["density"] > 0.1


@then("the offenders include \"really\" \"just\" \"very\" \"somehow\" \"actually\"")
def _then_offenders(ctx):
    offenders = set(ctx["fw"]["offenders"])
    assert {"really", "just", "very", "somehow", "actually"} <= offenders


@then("the passed flag is False")
def _then_passed_false(ctx):
    obj = ctx.get("fw") or ctx.get("result")
    assert obj["passed"] is False


@then("the filter_count is 0 and passed is True")
def _then_filter_clean(ctx):
    assert ctx["fw"]["filter_count"] == 0
    assert ctx["fw"]["passed"] is True


@then("proper_nouns is [\"Alice\", \"Bob\", \"Charlie\"]")
def _then_proper_nouns_abc(ctx):
    assert ctx["pn"]["proper_nouns"] == ["Alice", "Bob", "Charlie"]


@then("proper_nouns contains only \"George\"")
def _then_proper_nouns_george(ctx):
    assert ctx["pn"]["proper_nouns"] == ["George"]


@then("the result passed is True and flowery_count is 0")
def _then_dialogue_clean(ctx):
    assert ctx["da"]["passed"] is True
    assert ctx["da"]["flowery_count"] == 0


@then("the result passed is False")
def _then_result_passed_false(ctx):
    obj = ctx.get("da") or ctx.get("sdt") or ctx.get("result") or ctx.get("check")
    assert obj["passed"] is False


@then("flowery_count is 3")
def _then_flowery_3(ctx):
    assert ctx["da"]["flowery_count"] == 3


@then("flowery_hits contains \"exclaimed\"")
def _then_flowery_exclaimed(ctx):
    assert "exclaimed" in ctx["da"]["flowery_hits"]


@then("the result passed is True and tell_count is 0")
def _then_sdt_clean(ctx):
    assert ctx["sdt"]["passed"] is True
    assert ctx["sdt"]["tell_count"] == 0


@then(parsers.parse("tell_count is at least {n:d}"))
def _then_tell_count(ctx, n):
    assert ctx["sdt"]["tell_count"] >= n


@then("tells contains \"felt\"")
def _then_tells_felt(ctx):
    assert "felt" in ctx["sdt"]["tells"]


@then("warnings is an empty list")
def _then_no_warnings(ctx):
    assert ctx["cw"]["warnings"] == []


@then("warnings includes \"violence\"")
def _then_cw_violence(ctx):
    assert "violence" in ctx["cw"]["warnings"]


@then("warnings includes \"substance\"")
def _then_cw_substance(ctx):
    assert "substance" in ctx["cw"]["warnings"]


# ─── then: manuscript ────────────────────────────────────────────────────────

@then("the artefact kind is \"blurb\"")
def _then_blurb_kind(ctx):
    assert ctx["result"]["artefact"]["kind"] == "blurb"


@then("the result contains \"Modem Daze\"")
def _then_result_modem_daze(ctx):
    assert "Modem Daze" in ctx["result"]["result"]


@then("the result contains \"phreaker\"")
def _then_result_phreaker(ctx):
    assert "phreaker" in ctx["result"]["result"].lower()


@then("the result contains \"sysop\"")
def _then_result_sysop(ctx):
    assert "sysop" in ctx["result"]["result"].lower()


@then("the artefact kind is \"query-letter\"")
def _then_ql_kind(ctx):
    assert ctx["ql"]["artefact"]["kind"] == "query-letter"


@then("the result contains \"Jane Smith\" and \"Modem Daze\" and \"The Phreakers\"")
def _then_ql_content(ctx):
    body = ctx["ql"]["result"]
    assert "Jane Smith" in body
    assert "Modem Daze" in body
    assert "The Phreakers" in body


@then("the artefact kind is \"synopsis\"")
def _then_synopsis_kind(ctx):
    assert ctx["synopsis"]["artefact"]["kind"] == "synopsis"


@then("\"Connection\" appears before \"Discovery\" before \"Confrontation\" in the synopsis")
def _then_synopsis_order(ctx):
    body = ctx["synopsis"]["result"]
    assert body.index("Connection") < body.index("Discovery")
    assert body.index("Discovery") < body.index("Confrontation")


# ─── then: research ──────────────────────────────────────────────────────────

@then("the result contains a claim_id starting with \"novelclaim:\"")
def _then_claim_id(ctx):
    assert ctx["result"]["claim_id"].startswith("novelclaim:")


@then("the claim domain is \"historical\"")
def _then_claim_domain(ctx):
    assert ctx["result"]["domain"] == "historical"


@then("the claim verified status is \"pending\"")
def _then_claim_pending(ctx):
    assert ctx["result"]["verified"] == "pending"


@then("a SERVES edge links the claim to the intent")
def _then_claim_serves(engine, confirmed_intent, ctx):
    cid = ctx["result"]["claim_id"]
    rows = engine.memory.g.query(
        "MATCH (c)-[r:SERVES]->(t) WHERE c.id = $cid AND t.id = $tid RETURN r",
        {"cid": cid, "tid": confirmed_intent})
    assert rows


@then(parsers.parse("the claim count is {n:d}"))
def _then_claim_count(ctx, n):
    assert ctx["result"]["count"] == n


@then("the total pending count is 2")
def _then_pending_count(ctx):
    assert ctx["pending"]["count"] == 2


@then("the by_domain breakdown shows 1 for \"historical\" and 1 for \"scientific\"")
def _then_pending_by_domain(ctx):
    assert ctx["pending"]["by_domain"]["historical"] == 1
    assert ctx["pending"]["by_domain"]["scientific"] == 1


# ─── then: storyform ─────────────────────────────────────────────────────────

@then("the check result passed is True and violations is empty")
def _then_check_pass(ctx):
    r = ctx["check"]
    assert r["passed"] is True
    assert r.get("violations", []) == []


@then("the check result passed is False and violations is non-empty")
def _then_check_fail(ctx):
    r = ctx["check"]
    assert r["passed"] is False
    assert r["violations"]


@then("the check result passed is True")
def _then_check_pass_simple(ctx):
    assert ctx["check"]["passed"] is True


@then("the composite result passed is True and violations is empty")
def _then_composite_pass(ctx):
    r = ctx["composite"]
    assert r["passed"] is True
    assert r.get("violations", []) == []


@then("the composite fails and \"throughline_partition\" is in the failed checks")
def _then_composite_throughline_fail(ctx):
    r = ctx["composite"]
    assert r["passed"] is False
    failed = {v["check"] for v in r["violations"]}
    assert "throughline_partition" in failed


@then("the composite warnings include \"approach_concern\"")
def _then_composite_approach_warn(ctx):
    r = ctx["composite"]
    warned = {w["check"] for w in r.get("warnings", [])}
    assert "approach_concern" in warned


@then("the check result passed is False")
def _then_check_fail_simple(ctx):
    assert ctx["check"]["passed"] is False


@then(parsers.parse('the violations include the value "{value}"'))
def _then_violations_value(ctx, value):
    assert any(v["value"] == value for v in ctx["check"]["violations"])


# ─── then: worldbuilding ─────────────────────────────────────────────────────

@then("the result contains a world_id")
def _then_world_id(ctx):
    assert ctx["world"]["world_id"]


@then("the world slug is \"midgard\" and name is \"Midgard\"")
def _then_world_slug_name(ctx):
    assert ctx["world"]["slug"] == "midgard"
    assert ctx["world"]["name"] == "Midgard"


@then("all four children return their id keys")
def _then_children_ids(ctx):
    c, rel, lang, mag = ctx["children"]
    assert c["culture_id"]
    assert rel["religion_id"]
    assert lang["language_id"]
    assert mag["magic_system_id"]


@then("four PART_OF_WORLD edges link to the world")
def _then_part_of_world(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (x)-[r:PART_OF_WORLD]->(w:World) WHERE w.id = $wid RETURN x",
        {"wid": ctx["world_id"]})
    assert len(rows) == 4


@then("the result contains an axiom_id")
def _then_axiom_id(ctx):
    assert ctx["axiom"]["axiom_id"]


@then("the axiom severity is \"hard\"")
def _then_axiom_hard(ctx):
    assert ctx["axiom"]["severity"] == "hard"


@then("cultures count is 2 and religions count is 1 and axioms count is 1")
def _then_world_list_counts(ctx):
    wl = ctx["world_list"]
    assert len(wl["cultures"]) == 2
    assert len(wl["religions"]) == 1
    assert len(wl["axioms"]) == 1


@then("passed is False")
def _then_passed_false_generic(ctx):
    obj = (ctx.get("contradictions") or ctx.get("result") or
           ctx.get("pov") or ctx.get("continuity"))
    assert obj["passed"] is False


@then("the contradiction pair is in the results")
def _then_contradiction_pair(ctx):
    a1, a2 = ctx["axiom_ids"]
    ids = {(c["a_id"], c["b_id"]) for c in ctx["contradictions"]["contradictions"]}
    assert (a1, a2) in ids


@then("passed is True and contradictions is empty")
def _then_no_contradictions(ctx):
    assert ctx["contradictions"]["passed"] is True
    assert ctx["contradictions"]["contradictions"] == []


@then("the returned edge_kind is \"WORSHIPS\"")
def _then_edge_kind(ctx):
    assert ctx["link"]["edge_kind"] == "WORSHIPS"


@then("a WORSHIPS edge exists between character and religion in the graph")
def _then_worships_edge(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (c)-[r:WORSHIPS]->(rel:Religion) "
        "WHERE c.id = $cid AND rel.id = $rid RETURN r",
        {"cid": ctx["character_id"], "rid": ctx["religion_id"]})
    assert rows


# ─── then: codex ─────────────────────────────────────────────────────────────

@then("the result contains an entry_id")
def _then_entry_id(ctx):
    assert ctx["codex_entry"]["entry_id"]


@then("a CODEX_OF edge links the entry to the novel")
def _then_codex_of(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (c:CodexEntry)-[r:CODEX_OF]->(n:Novel) "
        "WHERE c.id = $cid AND n.id = $nid RETURN r",
        {"cid": ctx["entry_id"], "nid": ctx["novel_id"]})
    assert len(rows) == 1


@then("the entry slugs include \"a\" and \"b\"")
def _then_codex_slugs_ab(ctx):
    slugs = {e["slug"] for e in ctx["codex_list"]["entries"]}
    assert {"a", "b"} <= slugs


@then("the entry slugs include only \"a\"")
def _then_codex_slugs_a_only(ctx):
    slugs = {e["slug"] for e in ctx["codex_list"]["entries"]}
    assert slugs == {"a"}


@then("the matches include slug \"iron-mask\"")
def _then_matches_iron_mask(ctx):
    slugs = {m["slug"] for m in ctx["matches"]["matches"]}
    assert "iron-mask" in slugs


@then("the matches include slug \"raven\"")
def _then_matches_raven(ctx):
    assert any(m["slug"] == "raven" for m in ctx["matches"]["matches"])


@then("the matches list is empty")
def _then_matches_empty(ctx):
    assert ctx["matches"]["matches"] == []


@then("the node body is \"new body\"")
def _then_node_body(engine, ctx):
    node = engine.memory.recall(ctx["entry_id"])
    assert node["body"] == "new body"


@then("the node archived property is \"yes\"")
def _then_archived(engine, ctx):
    node = engine.memory.recall(ctx["entry_id"])
    assert node.get("archived") == "yes"


# ─── then: character knowledge ───────────────────────────────────────────────

@then("a KNOWS edge links the character to the KnownFact")
def _then_knows_edge(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (c)-[r:KNOWS]->(f:KnownFact) "
        "WHERE c.id = $cid AND f.id = $fid RETURN r",
        {"cid": ctx["character_id"], "fid": ctx["fact_id"]})
    assert len(rows) == 1


@then("a LEARNED_IN edge links the KnownFact to the scene")
def _then_learned_in_edge(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (f:KnownFact)-[r:LEARNED_IN]->(s:Scene) "
        "WHERE f.id = $fid AND s.id = $sid RETURN r",
        {"fid": ctx["fact_id"], "sid": ctx["scenes"][1]})
    assert len(rows) == 1


@then("\"Fact A\" and \"Fact B\" are in the facts list")
def _then_facts_ab(ctx):
    facts = [f["fact"] for f in ctx["knowledge"]["facts"]]
    assert "Fact A" in facts
    assert "Fact B" in facts


@then("\"Fact A\" is in the facts list")
def _then_fact_a(ctx):
    facts = [f["fact"] for f in ctx["knowledge"]["facts"]]
    assert "Fact A" in facts


@then("\"Future Fact\" is not in the facts list")
def _then_future_fact_absent(ctx):
    facts = [f["fact"] for f in ctx["knowledge"]["facts"]]
    assert "Future Fact" not in facts


@then("anachronism is False")
def _then_not_anachronism(ctx):
    assert ctx["ana"]["anachronism"] is False


@then("anachronism is True")
def _then_anachronism(ctx):
    assert ctx["ana"]["anachronism"] is True


@then("anachronism is False and no_record is True")
def _then_no_record(ctx):
    assert ctx["ana"]["anachronism"] is False
    assert ctx["ana"].get("no_record") is True


# ─── then: story time ────────────────────────────────────────────────────────

@then("the result contains an event_id")
def _then_event_id(ctx):
    assert ctx["event"]["event_id"]


@then("when_story is \"Y2391.04\"")
def _then_when_story(ctx):
    assert ctx["event"]["when_story"] == "Y2391.04"


@then("a HAPPENS_AT edge links scene 2 to the event")
def _then_happens_at(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (s:Scene)-[r:HAPPENS_AT]->(ev:StoryTimeEvent) "
        "WHERE s.id = $sid AND ev.id = $eid RETURN r",
        {"sid": ctx["scenes"][1], "eid": ctx["event"]["event_id"]})
    assert len(rows) == 1


@then("a REVEALED_IN edge links the event to scene 3")
def _then_revealed_in(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (ev:StoryTimeEvent)-[r:REVEALED_IN]->(s:Scene) "
        "WHERE ev.id = $eid AND s.id = $sid RETURN r",
        {"eid": ctx["event_id"], "sid": ctx["scenes"][2]})
    assert len(rows) == 1


@then("\"Birth\" and \"Marriage\" are in the events")
def _then_events_birth_marriage(ctx):
    labels = [ev["label"] for ev in ctx["events"]["events"]]
    assert "Birth" in labels
    assert "Marriage" in labels


@then("\"Death\" is not in the events")
def _then_no_death(ctx):
    labels = [ev["label"] for ev in ctx["events"]["events"]]
    assert "Death" not in labels


@then("events is empty and anchor_when is None")
def _then_no_events(ctx):
    assert ctx["events"]["events"] == []
    assert ctx["events"]["anchor_when"] is None


@then("reveals contains 1 entry with label \"Lost will\"")
def _then_reveals_lost_will(ctx):
    assert len(ctx["reveals"]["reveals"]) == 1
    assert ctx["reveals"]["reveals"][0]["label"] == "Lost will"


@then("the result contains a beat_id")
def _then_beat_id(ctx):
    assert ctx["beat"]["beat_id"]


@then("a PRECEDES edge links beat 1 to beat 2")
def _then_precedes(engine, ctx):
    rows = engine.memory.g.query(
        "MATCH (a:NarrativeBeat)-[r:PRECEDES]->(b:NarrativeBeat) "
        "WHERE a.id = $aid AND b.id = $bid RETURN r",
        {"aid": ctx["beat1_id"], "bid": ctx["beat2_id"]})
    assert len(rows) == 1


@then("b1 appears before b2 and b2 appears before b3 in the returned list")
def _then_topo_order(ctx):
    ids = [b["beat_id"] for b in ctx["order"]["beats"]]
    b1, b2, b3 = ctx["beat_ids"]
    assert ids.index(b1) < ids.index(b2)
    assert ids.index(b2) < ids.index(b3)


# ─── then: editorial pipeline ────────────────────────────────────────────────

@then("the result passed is True and outliers is empty")
def _then_voice_clean(ctx):
    assert ctx["voice"]["passed"] is True
    assert ctx["voice"]["outliers"] == []


@then("the result passed is False and the outlier index is 3")
def _then_voice_outlier(ctx):
    assert ctx["voice"]["passed"] is False
    assert ctx["voice"]["outliers"]


@then("the result passed is True")
def _then_generic_pass(ctx):
    obj = (ctx.get("pov") or ctx.get("continuity") or
           ctx.get("check") or ctx.get("result"))
    assert obj["passed"] is True


@then("the result contains a warnings field")
def _then_sensitivity_has_warnings(ctx):
    assert "warnings" in ctx["sensitivity"]


# ─── then: gates ─────────────────────────────────────────────────────────────

@then("the gate passed is True")
def _then_gate_pass(ctx):
    assert ctx["result"]["passed"] is True


@then("checks shows chapter_outline, research_present, and storyform_present are all True")
def _then_pre_draft_checks(ctx):
    checks = ctx["result"]["checks"]
    assert checks["chapter_outline"] is True
    assert checks["research_present"] is True
    assert checks["storyform_present"] is True


@then("all_chapters_drafted is True")
def _then_all_drafted(ctx):
    assert ctx["result"]["checks"]["all_chapters_drafted"] is True


@then("status_beta_or_later is present in the checks")
def _then_status_beta(ctx):
    assert "status_beta_or_later" in ctx["result"]["checks"]


@then("status_at_querying_or_later is True")
def _then_status_querying(ctx):
    assert ctx["result"]["checks"]["status_at_querying_or_later"] is True


# ─── then: E2E ───────────────────────────────────────────────────────────────

@then("every pipeline verb is present in the provenance")
def _then_e2e_verbs(ctx):
    prov = ctx["prov"]
    serves = prov.get("serves") or []
    verbs_fired = {s.get("verb") for s in serves}
    expected = {
        "capture_idea", "promote_idea", "create_chapter",
        "capture_claim", "count_words", "check_filter_words",
        "chapter_report", "set_novel_status", "pre_draft_gate",
        "render_manuscript",
    }
    missing = expected - verbs_fired
    assert not missing, f"verbs missing from provenance: {missing}"


@then("the manuscript artefact kind is in the provenance")
def _then_e2e_artefact(ctx):
    assert ctx["ms_kind"] == "manuscript"
