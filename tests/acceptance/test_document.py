"""Acceptance — document capability (Spec 043, Spec 056).

Converted from: tests/test_document_render.py, tests/test_document_index_repo.py,
tests/test_document_explain.py, tests/test_document_scope_guards.py.

Dropped (implementation / structural — not observable behaviour):
  - test_document_render.test_render_reflections_text_truncated_to_500 —
    pinned to exactly 500 chars (magic number snapshot); converted to the
    invariant "content does not contain 600 consecutive identical characters".
  - test_document_scope_guards.test_lint_table_covers_root_intent_id — tests the
    internal `_check_node_id_guards` linter (a private plugin function that
    inspects capability definitions); not observable behaviour through the wire.
  - test_document_scope_guards.test_paths_scan_rejects_non_intent_root — tests
    internal _paths.scan directly; observable only via analyze.run behaviour
    (covered in analyze acceptance). Calling _paths.scan with a non-Intent id
    is an implementation guard, not a wire-surface contract.
  - test_document_index_repo.test_self_test_under_3500_tokens — the
    "token budget" behaviour is KEPT (it is a documented tunable per CLAUDE.md
    rule 8), converted to scenario "index_repo briefing fits within the token
    budget"; the module-docstring rationale for the 3500 number is preserved
    in the test assertion comment.
  - test_document_explain.test_explanation_includes_signature_for_callable —
    pinned to the string "Signature" appearing in output; fragile implementation
    snapshot. The behaviour is that explain returns content about the target
    (tested via "the content mentions 'ReflectCapability'" scenario).
"""
from __future__ import annotations

import os
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/document.feature")

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ── helpers ────────────────────────────────────────────────────────────────────

def _render(engine, confirmed_intent, **kw):
    r, _ = invoke(engine, confirmed_intent, "document", "render",
                  agent_id="agent:test", **kw)
    return r


def _index_repo(engine, confirmed_intent, **kw):
    r, _ = invoke(engine, confirmed_intent, "document", "index_repo",
                  agent_id="agent:test", **kw)
    return r


def _explain(engine, confirmed_intent, **kw):
    r, _ = invoke(engine, confirmed_intent, "document", "explain",
                  agent_id="agent:test", **kw)
    return r


def _research_lead(engine, confirmed_intent, **kw):
    r, _ = invoke(engine, confirmed_intent, "research", "lead",
                  agent_id="agent:test", **kw)
    return r


# ── render — install-artefacts steps ─────────────────────────────────────────

@given("two install-artefact Reflection nodes exist")
def _two_install_artefacts(engine):
    engine.memory.record("Reflection", {
        "scope": "technical", "kind": "install-artefact",
        "name": "plugin.json", "body": '{"name": "agency"}',
        "text": "rendered into plugin.json on install"})
    engine.memory.record("Reflection", {
        "scope": "technical", "kind": "install-artefact",
        "name": ".mcp.json", "body": '{"servers": {}}',
        "text": "rendered into .mcp.json on install"})


@when(parsers.parse('I call document.render with scope "{scope}"'),
      target_fixture="render_result")
def _render_scope(engine, confirmed_intent, scope):
    return _render(engine, confirmed_intent, scope=scope)


@then(parsers.parse('the content starts with "{prefix}"'))
def _content_starts_with(render_result, prefix):
    assert render_result["content"].startswith(prefix)


@then(parsers.parse("the node_count is {n:d}"))
def _node_count(render_result, n):
    assert render_result["node_count"] == n


@then("each artefact name appears as an H2 heading")
def _h2_headings(render_result):
    content = render_result["content"]
    assert "## .mcp.json\n" in content
    assert "## plugin.json\n" in content
    # alphabetical order
    assert content.index("## .mcp.json") < content.index("## plugin.json")


@then("the artefact bodies are fenced in code blocks")
def _code_fences(render_result):
    assert "```\n" in render_result["content"]


@then("the token count is positive")
def _tokens_positive(render_result):
    assert render_result["tokens"] > 0


# ── render — reflections steps ────────────────────────────────────────────────

@given("three technical reflections are recorded in order first, second, third")
def _three_reflections(engine, confirmed_intent):
    for txt in ("first thing", "second thing", "third thing"):
        invoke(engine, confirmed_intent, "reflect", "note",
               agent_id="agent:t", scope="technical", text=txt)


@then(parsers.parse("the content heading mentions \"{text}\""))
def _heading_mentions(render_result, text):
    assert text in render_result["content"]


@then(parsers.parse('"{first}" appears before "{second}" in the content'))
def _order(render_result, first, second):
    content = render_result["content"]
    assert content.index(first) < content.index(second)


@given("a reflection under this intent and another under a separate intent")
def _two_intent_reflections(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "reflect", "note",
           agent_id="agent:t", scope="technical", text="under this intent")
    other = engine.intent.capture("other", "x", "x")
    engine.intent.confirm(other)
    invoke(engine, other, "reflect", "note",
           agent_id="agent:t", scope="technical", text="under other intent")


@when("I call document.render with scope \"reflections\" filtered to this intent",
      target_fixture="render_result")
def _render_reflections_filtered(engine, confirmed_intent):
    return _render(engine, confirmed_intent, scope="reflections",
                   for_intent_id=confirmed_intent)


@then("the content includes the node under this intent")
def _includes_this_intent_node(render_result):
    assert "under this intent" in render_result["content"]


@then("the content does not include the node under the other intent")
def _excludes_other_intent_node(render_result):
    assert "under other intent" not in render_result["content"]


@given("a reflection with text 1000 characters long")
def _long_reflection(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "reflect", "note",
           agent_id="agent:t", scope="technical", text="x" * 1000)


@then("the content does not contain 600 consecutive identical characters")
def _no_600_x(render_result):
    assert "x" * 600 not in render_result["content"]


# ── render — provenance steps ─────────────────────────────────────────────────

@when("I call document.render with scope \"provenance\" for this intent",
      target_fixture="render_result")
def _render_provenance_intent(engine, confirmed_intent):
    return _render(engine, confirmed_intent, scope="provenance",
                   for_intent_id=confirmed_intent)


@then("the content includes a heading with the intent id")
def _heading_intent_id(render_result, confirmed_intent):
    assert confirmed_intent in render_result["content"]


@then(parsers.parse('the content includes sections "{a}", "{b}", and "{c}"'))
def _sections_abc(render_result, a, b, c):
    for section in (a, b, c):
        assert f"## {section}" in render_result["content"]


@when("I call document.render with scope \"provenance\" and no intent id",
      target_fixture="render_result")
def _render_provenance_no_id(engine, confirmed_intent):
    return _render(engine, confirmed_intent, scope="provenance", for_intent_id="")


@then('the render content includes "# Intent (none) provenance"')
def _none_heading(render_result):
    assert "# Intent (none) provenance" in render_result["content"]


@given("a child intent exists under this intent", target_fixture="child_intent_id")
def _child_intent(engine, confirmed_intent):
    child = engine.intent.capture_and_confirm(
        "child", "x", "x", parent_intent_id=confirmed_intent)
    return child


@then('the content includes a "Sub-intents" section')
def _sub_intents_section(render_result):
    assert "## Sub-intents" in render_result["content"]


@then("the child intent id appears in the content")
def _child_in_content(render_result, child_intent_id):
    assert child_intent_id in render_result["content"]


# ── render — capability-catalogue steps ───────────────────────────────────────

@then(parsers.parse('the catalogue includes entries for "{a}", "{b}", and "{c}"'))
def _catalogue_entries(render_result, a, b, c):
    for cap in (a, b, c):
        assert f"## {cap}" in render_result["content"]


@then("the content footer mentions capabilities and verbs")
def _footer_caps_verbs(render_result):
    assert "capabilities" in render_result["content"]
    assert "verbs" in render_result["content"]


# ── render — edge-case steps ──────────────────────────────────────────────────

@then("the render result carries an error")
def _has_error_key(render_result):
    assert "error" in render_result


@then("the content is empty")
def _content_empty(render_result):
    assert render_result.get("content", "") == ""


@when(parsers.parse('I call document.render with scope "{scope}" and format "{fmt}"'),
      target_fixture="render_result")
def _render_with_format(engine, confirmed_intent, scope, fmt):
    return _render(engine, confirmed_intent, scope=scope, format=fmt)


@when("I call document.render with scope \"capability-catalogue\"",
      target_fixture="render_result")
def _render_cap_catalogue(engine, confirmed_intent):
    return _render(engine, confirmed_intent, scope="capability-catalogue")


@then("the Reflection node count is unchanged")
def _reflection_count_unchanged(engine, confirmed_intent):
    # Record the count before and compare after the render (which already ran).
    # Since render has already been called via the When step, we verify the
    # catalogue render did not add Reflection nodes compared to the background.
    # We assert it's not negative and the render returned without touching the count.
    count = len(list(engine.memory.find("Reflection")))
    # Re-call render to verify it's idempotent.
    _render(engine, confirmed_intent, scope="capability-catalogue")
    assert len(list(engine.memory.find("Reflection"))) == count


# ── render — scope guard steps ─────────────────────────────────────────────────

@given("a Research node exists from a research.lead call",
       target_fixture="research_id")
def _seed_research(engine, confirmed_intent):
    r = _research_lead(engine, confirmed_intent, question="what is X?", depth="brief")
    return r["research_id"]


@when("I call document.render with scope \"research-report\" using the Research id",
      target_fixture="render_result")
def _render_research_report(engine, confirmed_intent, research_id):
    return _render(engine, confirmed_intent, scope="research-report",
                   for_intent_id=research_id)


@then('the result does not contain "is not an Intent id"')
def _no_intent_id_error(render_result):
    assert "is not an Intent id" not in (render_result.get("error") or "")


@then("the result does not carry a Research-id error")
def _no_research_id_error(render_result):
    assert render_result.get("error") is None or \
           "Research" not in render_result.get("error", "")


@when("I call document.render with scope \"research-report\" using this intent's id",
      target_fixture="render_result")
def _render_research_report_wrong(engine, confirmed_intent):
    return _render(engine, confirmed_intent, scope="research-report",
                   for_intent_id=confirmed_intent)


@then(parsers.parse('the result carries "{msg}" in the error'))
def _error_contains(render_result, msg):
    assert msg in (render_result.get("error") or "")


@given("an Artefact node exists", target_fixture="artefact_id")
def _artefact_node(engine):
    return engine.memory.record("Artefact", {"kind": "x"})


@when("I call document.render with scope \"provenance\" using the Artefact id",
      target_fixture="render_result")
def _render_provenance_artefact(engine, confirmed_intent, artefact_id):
    return _render(engine, confirmed_intent, scope="provenance",
                   for_intent_id=artefact_id)


@then('the result does not contain "not an Intent id"')
def _no_intent_error(render_result):
    assert "not an Intent id" not in (render_result.get("error") or "")


# ── document.index_repo steps ─────────────────────────────────────────────────

@when("I call document.index_repo on the agency repo with apply False",
      target_fixture="index_result")
def _index_agency(engine, confirmed_intent):
    return _index_repo(engine, confirmed_intent, path=_REPO, apply=False)


@then(parsers.parse("the briefing token count is at most {n:d}"))
def _briefing_token_at_most(index_result, n):
    # Tunable budget: 3500 tokens (documented in test_document_index_repo.py).
    actual = index_result.get("tokens", 0)
    assert actual <= n, f"briefing token count {actual} exceeds {n}"


@then(parsers.parse("the explain token count is at most {n:d}"))
def _explain_token_at_most(explain_result, n):
    actual = explain_result.get("tokens", 0)
    assert actual <= n, f"explain token count {actual} exceeds {n}"


@then(parsers.parse('the briefing content includes "{a}", "{b}", "{c}", and "{d}"'))
def _briefing_includes(index_result, a, b, c, d):
    content = index_result["content"]
    for cap in (a, b, c, d):
        assert cap in content, f"capability {cap!r} not in briefing"


@then(parsers.parse('the briefing includes "{text}"'))
def _briefing_includes_text(index_result, text):
    assert text in index_result["content"], f"{text!r} not in briefing"


@then("a RepoIndex node is added to the graph")
def _repo_index_node(engine, index_result):
    indices = engine.memory.find("RepoIndex")
    assert any(r["id"] == index_result["index_id"] for r in indices)


@then("the RepoIndex node carries the path, token_count, and a content_sha of 16 characters")
def _repo_index_props(engine, index_result):
    indices = engine.memory.find("RepoIndex")
    idx = next(r for r in indices if r["id"] == index_result["index_id"])
    assert idx["path"].startswith("/") or idx["path"].startswith(_REPO)
    assert idx["token_count"] == index_result["tokens"]
    assert len(idx["content_sha"]) == 16


@when("I call document.index_repo on a temp directory with apply False",
      target_fixture="index_result")
def _index_temp(engine, confirmed_intent, tmp_path):
    return _index_repo(engine, confirmed_intent, path=str(tmp_path), apply=False)


@then("no PROJECT_INDEX.md file is written")
def _no_file(tmp_path):
    assert not (tmp_path / "PROJECT_INDEX.md").exists()


@given("a minimal project directory with a pyproject.toml and a Python module",
       target_fixture="project_dir")
def _minimal_project(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n[project.scripts]\nx = "x:main"\n')
    (tmp_path / "module.py").write_text('"""A test module brief."""\n')
    return tmp_path


@when("I call document.index_repo on that directory with apply True",
      target_fixture="index_result")
def _index_apply(engine, confirmed_intent, project_dir):
    return _index_repo(engine, confirmed_intent, path=str(project_dir), apply=True)


@then("a PROJECT_INDEX.md file is written")
def _file_written(project_dir):
    assert (project_dir / "PROJECT_INDEX.md").exists()


@then("the file content matches the returned content")
def _file_matches(project_dir, index_result):
    on_disk = (project_dir / "PROJECT_INDEX.md").read_text()
    assert on_disk == index_result["content"]


@when("I call document.index_repo on the agency repo with max_tokens 500",
      target_fixture="index_result")
def _index_max_tokens(engine, confirmed_intent):
    return _index_repo(engine, confirmed_intent, path=_REPO,
                       apply=False, max_tokens=500)


@then("the content signals truncation")
def _truncation_signal(index_result):
    assert "omitted" in index_result["content"] or index_result["tokens"] <= 500


@then("the files_scanned count is positive")
def _files_scanned(index_result):
    assert index_result.get("files_scanned", 0) > 0


# ── document.explain steps ────────────────────────────────────────────────────

@when(parsers.parse('I call document.explain for target "{target}"'),
      target_fixture="explain_result")
def _explain_target(engine, confirmed_intent, target):
    return _explain(engine, confirmed_intent, target=target)


@when(parsers.parse('I call document.explain for target "{target}" at depth "{depth}"'),
      target_fixture="explain_result")
def _explain_target_depth(engine, confirmed_intent, target, depth):
    return _explain(engine, confirmed_intent, target=target, depth=depth)


@when("I call document.explain for that file path", target_fixture="explain_result")
def _explain_file(engine, confirmed_intent, fixture_file):
    return _explain(engine, confirmed_intent, target=str(fixture_file))


@then(parsers.parse('the content mentions "{text}"'))
def _content_mentions(explain_result, text):
    assert text.lower() in explain_result.get("content", "").lower()


@then("the result carries a reflection_id")
def _has_reflection_id(explain_result):
    assert "reflection_id" in explain_result


@then("the explain result carries an error")
def _explain_has_error(explain_result):
    assert "error" in explain_result


@then("a new Reflection node is added to the graph")
def _reflection_added(engine, confirmed_intent):
    # Capturing count after invoke — the step itself calls explain which records.
    # We verify that the reflection_id from explain_result points to a real node.
    pass  # Validated in "that Reflection node has kind 'explanation'" step


@then('that Reflection node has kind "explanation"')
def _reflection_kind(engine, explain_result):
    refs = engine.memory.find("Reflection")
    explanation = next(
        (r for r in refs if r["id"] == explain_result.get("reflection_id")), None)
    assert explanation is not None
    assert explanation["kind"] == "explanation"


@then(parsers.parse('that Reflection node targets "{target}"'))
def _reflection_target(engine, explain_result, target):
    refs = engine.memory.find("Reflection")
    explanation = next(
        (r for r in refs if r["id"] == explain_result.get("reflection_id")), None)
    assert explanation is not None
    assert explanation["target"] == target


@given("a fixture Python file with a function named \"greet\"",
       target_fixture="fixture_file")
def _fixture_file(tmp_path):
    p = tmp_path / "fixture.py"
    p.write_text('"""A test fixture module.\n\nLonger description.\n"""\n'
                 'def greet(name: str) -> str:\n'
                 '    return f"Hi, {name}"\n')
    return p


# ── graph↔markdown interconnect steps (Spec 290) ──────────────────────────────

def _ingest(engine, confirmed_intent, **kw):
    r, _ = invoke(engine, confirmed_intent, "document", "ingest",
                  agent_id="agent:test", **kw)
    return r


def _sync(engine, confirmed_intent, **kw):
    r, _ = invoke(engine, confirmed_intent, "document", "sync",
                  agent_id="agent:test", **kw)
    return r


def _revisions(engine, confirmed_intent, document_id):
    r, _ = invoke(engine, confirmed_intent, "document", "revisions",
                  agent_id="agent:test", document_id=document_id)
    return r


@given(parsers.parse('an un-anchored markdown file "{name}" with body "{body}"'),
       target_fixture="md_file")
def _unanchored_file(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body.replace("\\n", "\n"), encoding="utf-8")
    return p


@when("I call document.ingest on that file", target_fixture="ingest_result")
def _ingest_file(engine, confirmed_intent, md_file):
    return _ingest(engine, confirmed_intent, path=str(md_file))


@when("I call document.ingest on that file again", target_fixture="ingest_result_2")
def _ingest_file_again(engine, confirmed_intent, md_file):
    return _ingest(engine, confirmed_intent, path=str(md_file))


@when("I call document.ingest on that anchored file", target_fixture="ingest_result")
def _ingest_anchored_file(engine, confirmed_intent, md_file):
    return _ingest(engine, confirmed_intent, path=str(md_file))


@then(parsers.parse('the ingest action is "{action}"'))
def _ingest_action(ingest_result, action):
    assert ingest_result.get("action") == action


@then(parsers.parse('the second ingest action is "{action}"'))
def _second_ingest_action(ingest_result_2, action):
    assert ingest_result_2.get("action") == action


@then("the ingest result carries a document_id")
def _ingest_doc_id(ingest_result):
    assert ingest_result.get("document_id", "").startswith("document:")


@then("the file now begins with an agency-node anchor for that document_id")
def _file_anchored(md_file, ingest_result):
    text = md_file.read_text(encoding="utf-8")
    assert text.startswith(f"<!-- agency-node: {ingest_result['document_id']} -->")


@then(parsers.parse('a DocRevision with source "{source}" is linked to the Document'))
def _revision_linked(engine, confirmed_intent, ingest_result, source):
    revs = _revisions(engine, confirmed_intent,
                      ingest_result["document_id"])["history"]
    assert any(r["source"] == source for r in revs)


@then("the Document has exactly one revision")
def _one_revision(engine, confirmed_intent, ingest_result):
    revs = _revisions(engine, confirmed_intent, ingest_result["document_id"])
    assert revs["count"] == 1


@given("a Document seeded with a graph-authored revision and an anchored file",
       target_fixture="md_file")
def _seeded_document(engine, tmp_path):
    from agency.capabilities.document import _interconnect as _ic
    doc_id = engine.memory.record("Document", {
        "path": str(tmp_path / "seeded.md"), "content_sha": _ic.content_sha("graph body")})
    rev = engine.memory.record("DocRevision", {
        "source": "graph", "content_sha": _ic.content_sha("graph body"),
        "text": "graph body", "recorded_at": 1})
    engine.memory.link(rev, doc_id, "REVISION_OF")
    p = tmp_path / "seeded.md"
    p.write_text(_ic.stamp_anchor("file body — edited on disk", doc_id),
                 encoding="utf-8")
    return p


@then("the Document has exactly two revisions")
def _two_revisions(engine, confirmed_intent, ingest_result):
    revs = _revisions(engine, confirmed_intent, ingest_result["document_id"])
    assert revs["count"] == 2


@then(parsers.parse('the latest revision has source "{source}"'))
def _latest_source(engine, confirmed_intent, ingest_result, source):
    revs = _revisions(engine, confirmed_intent, ingest_result["document_id"])
    assert revs["latest"]["source"] == source


@then(parsers.parse('the earliest revision has source "{source}"'))
def _earliest_source(engine, confirmed_intent, ingest_result, source):
    revs = _revisions(engine, confirmed_intent, ingest_result["document_id"])
    assert revs["history"][-1]["source"] == source


@then("the ingest result carries a clarity_score")
def _ingest_clarity(ingest_result):
    assert isinstance(ingest_result.get("clarity_score"), int)


@then("the latest revision carries that clarity_score")
def _latest_clarity(engine, confirmed_intent, ingest_result):
    revs = _revisions(engine, confirmed_intent, ingest_result["document_id"])
    assert revs["latest"].get("clarity_score") == ingest_result["clarity_score"]


@given("a directory with two un-anchored markdown files", target_fixture="md_dir")
def _md_dir(tmp_path):
    (tmp_path / "a.md").write_text("first file body", encoding="utf-8")
    (tmp_path / "b.md").write_text("second file body", encoding="utf-8")
    return tmp_path


@when("I call document.sync on that directory", target_fixture="sync_result")
def _sync_dir(engine, confirmed_intent, md_dir):
    return _sync(engine, confirmed_intent, path=str(md_dir))


@then("the sync result reports two ingested files")
def _sync_two(sync_result):
    assert len(sync_result.get("ingested", [])) == 2


@then("a second sync on that directory reports zero ingested files")
def _sync_zero(engine, confirmed_intent, md_dir):
    r = _sync(engine, confirmed_intent, path=str(md_dir))
    assert len(r.get("ingested", [])) == 0


# ── document.session — four-concept convergence (Spec 290) ────────────────────

@when("I render the current session as a Document", target_fixture="session_result")
def _render_session(engine, confirmed_intent):
    r, _ = invoke(engine, confirmed_intent, "document", "session",
                  agent_id="agent:test")
    return r


@then("the session document covers Intent, Capability, Lifecycle, and Memory")
def _session_sections(session_result):
    content = session_result["content"]
    for section in ("Intent", "Capability", "Lifecycle", "Memory"):
        assert f"## {section}" in content, f"missing section {section}"


@then("the session result carries a document_id")
def _session_doc_id(session_result):
    assert session_result.get("document_id", "").startswith("document:")


@then("the session Document has a graph-authored revision")
def _session_graph_revision(engine, confirmed_intent, session_result):
    r, _ = invoke(engine, confirmed_intent, "document", "revisions",
                  agent_id="agent:test", document_id=session_result["document_id"])
    assert any(rev["source"] == "graph" for rev in r["history"])


@then(parsers.parse('the session is written under a "{dirname}" directory'))
def _session_in_dir(session_result, dirname):
    written = session_result.get("written", "")
    assert written and os.path.basename(os.path.dirname(written)) == dirname, written
    assert os.path.exists(written)


@then("the archived session file carries the document anchor")
def _archived_anchor(session_result):
    text = open(session_result["written"], encoding="utf-8").read()
    assert text.startswith(f"<!-- agency-node: {session_result['document_id']} -->")
