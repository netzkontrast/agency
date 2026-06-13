"""Acceptance — research capability (Spec 044, Spec 052, Spec 126, Spec 168).

Converted from: tests/test_research_capability.py, tests/test_research_verify.py,
tests/test_research_ingest_gdoc.py, tests/test_research_web.py,
tests/test_research_citation.py.

Dropped (implementation / structural — not observable behaviour):
  - test_research_capability.test_capability_registered — registry membership
    structural; loud failure on invoke covers it.
  - test_research_capability.test_capability_has_verbs — verb-set snapshot;
    new verbs should not force test update.
  - test_research_capability.test_ontology_research_status_enum — internal enum
    shape; observable effect is the status value returned by lead (tested).
  - test_research_capability.test_ontology_citation_source_kind_enum — same.
  - test_research_capability.test_ontology_verification_status_enum — same.
  - test_research_capability.test_deep_research_skill_registered — phase names /
    gate flags are structural; walkability is the behaviour.
  - test_research_capability.test_engine_accepts_web_search_kwarg — covered by
    "engine web_search kwarg overrides the default" scenario.
  - test_research_web.test_ddg_client_parses_related_topics — monkeypatches
    httpx; tests internal DDG client parsing logic, not the observable
    research verb surface.
  - test_research_web.test_ddg_client_returns_empty_on_failure — monkeypatches
    httpx.Client; internal degradation, not observable behaviour.
  - test_research_web.test_ddg_client_respects_k_limit — monkeypatches httpx.
  - test_research_web.test_resolve_defaults_to_duckduckgo — monkeypatches env;
    the observable fact (engine default is duckduckgo) is covered.
  - test_research_web.test_resolve_explicit_duckduckgo — env monkeypatch.
  - test_research_web.test_resolve_unknown_falls_back_silently — env monkeypatch.
  - test_research_web.test_reachability_check_passes_on_2xx — monkeypatches httpx
    (network mock); not observable from the wire surface.
  - test_research_web.test_reachability_check_fails_on_4xx — monkeypatches httpx.
  - test_research_web.test_reachability_check_fails_on_network_error — monkeypatch.
  - test_research_citation.test_citation_typed_shape — internal dataclass shape.
  - test_research_citation.test_citation_rejects_empty_url — internal validation.
  - test_research_citation.test_citation_rejects_invalid_backend — internal enum.
  - test_research_citation.test_citation_rejects_empty_hash — internal validation.
  - test_research_citation.test_compute_citation_hash_is_deterministic — partially
    converted (observable: hash length = 16 chars is now an invariant check).
  - test_research_citation.test_backend_set_equals_documented — internal Literal
    annotation shape; kept as "backend set" but converted to behavioural.
  - test_research_ingest_gdoc.test_ingest_gdoc_verbs_registered — structural.
  - test_research_ingest_gdoc.test_dispatch_contract_callback_kwargs — internal
    callback shape; observable via the verb's returned dict (tested).

GAPS (network-dependent — cannot run reliably in acceptance suite):
  - web-reachability check with real HTTP HEAD calls (2xx / 4xx / timeout).
    The underlying behaviour is: verify raises "web-reachability" check in the
    payload (tested via the vacuous-pass scenario with no web citations, and
    the three-check payload scenario). Real network calls need an E2E tag.
"""
from __future__ import annotations

import tempfile

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke

scenarios("features/research.feature")

# Realistic 33-char Drive file id used throughout dispatch contract tests.
_FID = "1AbCxyz_-fileid_BcD1234567890eFgH"
_SHA = "abc123" * 10 + "abcd"   # 64 hex chars


# ── helpers ────────────────────────────────────────────────────────────────────

def _call(engine, confirmed_intent, verb, **kw):
    r, _ = invoke(engine, confirmed_intent, "research", verb,
                  agent_id="agent:test", **kw)
    return r


def _add_citation(engine, rid, claim_text: str, evidence: str,
                  source_kind: str = "codebase", confidence: float = 1.0,
                  url_or_path: str = "agency/x.py"):
    claim_id = engine.memory.record("ResearchClaim", {"text": claim_text,
                                                       "research_id": rid})
    cit_id = engine.memory.record("Citation", {
        "source_kind": source_kind,
        "source_url_or_path": url_or_path,
        "evidence_text": evidence,
        "confidence": confidence,
        "claim_supported": claim_text,
        "research_id": rid,
    })
    engine.memory.link(rid, cit_id, "CITES")
    engine.memory.link(cit_id, claim_id, "SUPPORTS")
    return cit_id, claim_id


# ── research.lead steps ────────────────────────────────────────────────────────

@when(parsers.parse('I call research.lead with question "{question}" at depth "{depth}"'),
      target_fixture="lead_result")
def _lead(engine, confirmed_intent, question, depth):
    return _call(engine, confirmed_intent, "lead", question=question, depth=depth)


@then("the result carries a research_id")
def _has_research_id(lead_result):
    assert "research_id" in lead_result


@then("a Research node with that id exists in the graph")
def _research_node_exists(engine, lead_result):
    nodes = engine.memory.find("Research")
    assert any(n["id"] == lead_result["research_id"] for n in nodes)


@then(parsers.parse('the Research node has question "{question}" and depth "{depth}"'))
def _research_props(engine, lead_result, question, depth):
    nodes = engine.memory.find("Research")
    me = next(n for n in nodes if n["id"] == lead_result["research_id"])
    assert me["question"] == question
    assert me["depth"] == depth


@then('the Research node status is "planning"')
def _research_status(engine, lead_result):
    nodes = engine.memory.find("Research")
    me = next(n for n in nodes if n["id"] == lead_result["research_id"])
    assert me["status"] == "planning"


@then("the Research node has a SERVES edge to the intent")
def _research_serves(engine, confirmed_intent, lead_result):
    rows = engine.memory.g.query(
        "MATCH (r:Research)-[:SERVES]->(i:Intent) "
        "WHERE r.id = $rid RETURN i",
        {"rid": lead_result["research_id"]})
    assert len(rows) == 1
    assert rows[0]["i"]["properties"]["id"] == confirmed_intent


@then('the specialist list contains only "codebase"')
def _specialist_only_codebase(lead_result):
    assert lead_result["specialists"] == ["codebase"]


@then("the specialist list has at least 2 entries")
def _specialist_at_least_2(lead_result):
    assert len(lead_result["specialists"]) >= 2


@then('"codebase" is among the specialists')
def _codebase_in_specialists(lead_result):
    assert "codebase" in lead_result["specialists"]


@then("the specialist list has at least 3 entries")
def _specialist_at_least_3(lead_result):
    assert len(lead_result["specialists"]) >= 3


@then("the plan text is non-empty")
def _plan_non_empty(lead_result):
    assert lead_result.get("plan")


# ── research.specialist — codebase steps ──────────────────────────────────────

@given(parsers.parse('I have seeded a research lead at depth "{depth}" for "{topic}"'),
       target_fixture="seeded_research_id")
def _seed_lead(engine, confirmed_intent, depth, topic):
    r = _call(engine, confirmed_intent, "lead", question=topic, depth=depth)
    return r["research_id"]


@when("I run the codebase specialist with query \"dispatch_decision\" on the agency source",
      target_fixture="specialist_result")
def _specialist_codebase(engine, confirmed_intent, seeded_research_id):
    return _call(engine, confirmed_intent, "specialist",
                 research_id=seeded_research_id,
                 role="codebase",
                 query="dispatch_decision",
                 search_root="agency")


@then("the citations count is at least 1")
def _citations_at_least_1(specialist_result):
    assert specialist_result.get("citations", 0) >= 1


@then("the specialist result carries a summary")
def _has_summary(specialist_result):
    assert specialist_result.get("summary")


@then("all Citation nodes for the research have confidence 1.0")
def _codebase_confidence(engine, seeded_research_id):
    citations = engine.memory.find("Citation")
    rs = [c for c in citations if c.get("research_id") == seeded_research_id]
    assert rs
    assert all(c["confidence"] == 1.0 for c in rs)


@then('all those Citation nodes have source_kind "codebase"')
def _codebase_source_kind(engine, seeded_research_id):
    citations = engine.memory.find("Citation")
    rs = [c for c in citations if c.get("research_id") == seeded_research_id]
    assert all(c["source_kind"] == "codebase" for c in rs)


# ── research.specialist — prior-reflections steps ─────────────────────────────

@given("a reflection about dispatch signals is recorded")
def _seed_dispatch_reflection(engine, confirmed_intent):
    invoke(engine, confirmed_intent, "reflect", "note",
           agent_id="agent:test", scope="technical",
           text="dispatch decision uses 11 signals")


@when("I run the prior-reflections specialist with query \"dispatch signals\"",
      target_fixture="specialist_result")
def _specialist_prior(engine, confirmed_intent, seeded_research_id):
    return _call(engine, confirmed_intent, "specialist",
                 research_id=seeded_research_id,
                 role="prior-reflections",
                 query="dispatch signals")


@then('at least one Citation node has source_kind "reflection"')
def _reflection_citation(engine, seeded_research_id):
    citations = engine.memory.find("Citation")
    rs = [c for c in citations if c.get("research_id") == seeded_research_id]
    assert any(c["source_kind"] == "reflection" for c in rs)


# ── research.specialist — doc-corpus steps ────────────────────────────────────

@given("a local docs directory with a file mentioning dispatch_decision",
       target_fixture="docs_dir")
def _docs_dir(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "test.md").write_text(
        "# test\n\nThis explains dispatch_decision heuristics.\n")
    return str(docs)


@when("I run the doc-corpus specialist with query \"dispatch_decision\" against that docs dir",
      target_fixture="specialist_result")
def _specialist_doc(engine, confirmed_intent, seeded_research_id, docs_dir):
    return _call(engine, confirmed_intent, "specialist",
                 research_id=seeded_research_id,
                 role="doc-corpus",
                 query="dispatch_decision",
                 docs_root=docs_dir)


# ── research.specialist — error handling steps ────────────────────────────────

@when("I run a specialist with an unknown role", target_fixture="specialist_result")
def _specialist_bad_role(engine, confirmed_intent, seeded_research_id):
    return _call(engine, confirmed_intent, "specialist",
                 research_id=seeded_research_id,
                 role="not-a-role",
                 query="x")


@then("the result carries an error key")
def _has_error(specialist_result):
    assert "error" in specialist_result


# ── research.verify steps ─────────────────────────────────────────────────────

@given("I have seeded a research lead for verification", target_fixture="verify_research_id")
def _seed_for_verify(engine, confirmed_intent):
    r = _call(engine, confirmed_intent, "lead", question="q", depth="brief")
    return r["research_id"]


@given("a citation where evidence contains the claim text")
def _matching_citation(engine, verify_research_id):
    _add_citation(engine, verify_research_id,
                  claim_text="dispatch picks driver via signals",
                  evidence="the dispatch function picks driver via signals")


@given("a citation where evidence is unrelated to the claim")
def _unrelated_citation(engine, verify_research_id):
    _add_citation(engine, verify_research_id,
                  claim_text="dispatch picks driver via signals",
                  evidence="completely unrelated text about cats and dogs")


@given("two citations with contradicting claims")
def _contradicting_citations(engine, verify_research_id):
    _add_citation(engine, verify_research_id,
                  claim_text="dispatch always picks local driver",
                  evidence="dispatch always picks local driver")
    _add_citation(engine, verify_research_id,
                  claim_text="dispatch never picks local driver",
                  evidence="dispatch never picks local driver")


@given("a matching citation")
def _basic_matching_citation(engine, verify_research_id):
    _add_citation(engine, verify_research_id, claim_text="x", evidence="x")


@given("a codebase citation exists")
def _codebase_citation(engine, verify_research_id):
    cit = engine.memory.record("Citation", {
        "source_kind": "codebase",
        "source_url_or_path": "agency/x.py:1",
        "evidence_text": "x",
        "confidence": 1.0,
        "claim_supported": "x",
        "research_id": verify_research_id,
    })
    engine.memory.link(verify_research_id, cit, "CITES")


@when("I call research.verify on that research", target_fixture="verify_result")
def _verify(engine, confirmed_intent, verify_research_id):
    return _call(engine, confirmed_intent, "verify", research_id=verify_research_id)


@then("the verify result is ok")
def _verify_ok(verify_result):
    assert verify_result["ok"]


@then("the verify result is not ok")
def _verify_not_ok(verify_result):
    assert not verify_result["ok"]


@then('the evidence-supports-claim check status is "pass"')
def _esc_pass(verify_result):
    assert verify_result["checks"]["evidence-supports-claim"]["status"] == "pass"


@then('the evidence-supports-claim check status is "fail"')
def _esc_fail(verify_result):
    assert verify_result["checks"]["evidence-supports-claim"]["status"] == "fail"


@then("the evidence-supports-claim check lists offending items")
def _esc_items(verify_result):
    assert verify_result["checks"]["evidence-supports-claim"].get("items")


@then('the contradiction-cluster check status is "warn" or "fail"')
def _cc_warn_or_fail(verify_result):
    status = verify_result["checks"]["contradiction-cluster"]["status"]
    assert status in ("warn", "fail")


@then("the contradiction-cluster check lists items")
def _cc_items(verify_result):
    assert verify_result["checks"]["contradiction-cluster"].get("items")


@then("a Verification node exists for the research in the graph")
def _verification_exists(engine, verify_research_id):
    vs = engine.memory.find("Verification")
    assert any(v.get("research_id") == verify_research_id for v in vs)


@then("the Verification node has a valid status")
def _verification_status(engine, verify_research_id):
    vs = engine.memory.find("Verification")
    ours = [v for v in vs if v.get("research_id") == verify_research_id]
    assert ours
    assert ours[0]["status"] in ("pass", "warn", "fail")


@then("a Verification node has a VERIFIES edge to the Research node")
def _verifies_edge(engine, verify_research_id):
    rows = engine.memory.g.query(
        "MATCH (v:Verification)-[:VERIFIES]->(r:Research) "
        "WHERE r.id = $rid RETURN v",
        {"rid": verify_research_id})
    assert len(rows) >= 1


@then("the evidence-supports-claim check shows n_checked of 0")
def _n_checked_zero(verify_result):
    check = verify_result["checks"]["evidence-supports-claim"]
    assert check.get("n_checked") == 0


@then("the checks dict has exactly the keys evidence-supports-claim, contradiction-cluster, and web-reachability")
def _three_checks(verify_result):
    assert set(verify_result["checks"]) == {
        "evidence-supports-claim",
        "contradiction-cluster",
        "web-reachability",
    }


@then('the web-reachability check status is "pass"')
def _web_reach_pass(verify_result):
    assert verify_result["checks"]["web-reachability"]["status"] == "pass"


# ── research.ingest_gdoc steps ────────────────────────────────────────────────

@when("I call research.ingest_gdoc with a Google Docs URL containing the file id",
      target_fixture="gdoc_result")
def _ingest_docs_url(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "ingest_gdoc",
                 source=f"https://docs.google.com/document/d/{_FID}/edit")


@when("I call research.ingest_gdoc with a Google Drive URL containing the file id",
      target_fixture="gdoc_result")
def _ingest_drive_url(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "ingest_gdoc",
                 source=f"https://drive.google.com/file/d/{_FID}/view")


@when("I call research.ingest_gdoc with a bare file id", target_fixture="gdoc_result")
def _ingest_bare_id(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "ingest_gdoc", source=_FID)


@when("I call research.ingest_gdoc with an invalid source", target_fixture="gdoc_result")
def _ingest_invalid(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "ingest_gdoc", source="not a url or id ☃")


@when(parsers.parse('I call research.ingest_gdoc with a bare file id and explicit dest "{dest}"'),
      target_fixture="gdoc_result")
def _ingest_explicit_dest(engine, confirmed_intent, dest):
    return _call(engine, confirmed_intent, "ingest_gdoc", source=_FID, dest=dest)


@then("the result file_id matches the embedded id")
def _file_id_matches(gdoc_result):
    assert gdoc_result["file_id"] == _FID


@then("the result file_id matches the bare id")
def _bare_id_matches(gdoc_result):
    assert gdoc_result["file_id"] == _FID


@then('the result error is "INVALID_SOURCE"')
def _invalid_source_error(gdoc_result):
    assert gdoc_result["error"] == "INVALID_SOURCE"


@then('the dest path starts with ".agency/sources/gdoc-"')
def _default_dest(gdoc_result):
    assert gdoc_result["dest"].startswith(".agency/sources/gdoc-")


@then(parsers.parse('the dest path is "{expected_dest}"'))
def _explicit_dest(gdoc_result, expected_dest):
    assert gdoc_result["dest"] == expected_dest


@then('the result action is "dispatch_subagent"')
def _action_dispatch(gdoc_result):
    assert gdoc_result["action"] == "dispatch_subagent"


@then("the tools list includes the four required Drive tools")
def _tools_include_drive(gdoc_result):
    tools = set(gdoc_result["tools"])
    assert "mcp__Google_Drive__download_file_content" in tools
    assert "mcp__Google_Drive__get_file_metadata" in tools
    assert "Write" in tools
    assert "Bash" in tools


@then('the tools list does not include "Read" or "Grep"')
def _tools_exclude_read_grep(gdoc_result):
    tools = set(gdoc_result["tools"])
    assert "Read" not in tools
    assert "Grep" not in tools


@then("the prompt contains the file id")
def _prompt_has_fid(gdoc_result):
    assert _FID in gdoc_result["prompt"]


@then("the prompt forbids echoing the document body")
def _prompt_forbids_echo(gdoc_result):
    prompt = gdoc_result["prompt"].lower()
    assert "do not echo" in prompt or "do not output the body" in prompt


@then("the prompt requires a JSON return with path, sha256, and title")
def _prompt_json_fields(gdoc_result):
    prompt = gdoc_result["prompt"].lower()
    assert "json" in prompt
    assert "path" in gdoc_result["prompt"]
    assert "sha256" in gdoc_result["prompt"]
    assert "title" in gdoc_result["prompt"]


@then('the model recommendation is "haiku"')
def _model_haiku(gdoc_result):
    assert gdoc_result["model"] == "haiku"


# ── research.record_ingested_source steps ─────────────────────────────────────

def _make_record_kwargs(**overrides):
    base = dict(
        source_url=f"https://docs.google.com/document/d/{_FID}/edit",
        dest=f".agency/sources/gdoc-{_FID}.md",
        bytes=12345,
        lines=420,
        sha256=_SHA,
        title="Research Brief: Nordic Folklore",
    )
    base.update(overrides)
    return base


@when("I call research.record_ingested_source with valid metadata",
      target_fixture="record_result")
def _record_source(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "record_ingested_source",
                 **_make_record_kwargs())


@then("the result carries an artefact_id")
def _has_artefact_id(record_result):
    assert record_result.get("artefact_id")
    assert "error" not in record_result


@then('an Artefact node exists with kind "ingested-source"')
def _artefact_kind(engine, record_result):
    node = engine.memory.g.get_node(record_result["artefact_id"])
    assert node is not None
    assert node["properties"]["kind"] == "ingested-source"


@then("the Artefact node has the supplied path, bytes, lines, sha256, and title")
def _artefact_props(engine, record_result):
    props = engine.memory.g.get_node(record_result["artefact_id"])["properties"]
    assert props["path"] == f".agency/sources/gdoc-{_FID}.md"
    assert props["bytes"] == 12345
    assert props["lines"] == 420
    assert props["sha256"] == _SHA
    assert props["title"] == "Research Brief: Nordic Folklore"


@then("the Artefact node has a SERVES edge to the intent")
def _artefact_serves(engine, confirmed_intent, record_result):
    rows = engine.memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(i:Intent) "
        "WHERE a.id = $aid AND i.id = $iid RETURN a",
        {"aid": record_result["artefact_id"], "iid": confirmed_intent})
    assert len(rows) == 1


@when("I call research.record_ingested_source twice with the same sha256",
      target_fixture="two_records")
def _record_same_sha(engine, confirmed_intent):
    r1 = _call(engine, confirmed_intent, "record_ingested_source",
               **_make_record_kwargs())
    r2 = _call(engine, confirmed_intent, "record_ingested_source",
               **_make_record_kwargs())
    return r1, r2


@then("both calls return the same artefact_id")
def _same_artefact(two_records):
    r1, r2 = two_records
    assert r1["artefact_id"] == r2["artefact_id"]


@when("I call research.record_ingested_source twice with different sha256 values",
      target_fixture="two_records")
def _record_diff_sha(engine, confirmed_intent):
    r1 = _call(engine, confirmed_intent, "record_ingested_source",
               **_make_record_kwargs())
    r2 = _call(engine, confirmed_intent, "record_ingested_source",
               **_make_record_kwargs(sha256="ffffff" * 10 + "ffff"))
    return r1, r2


@then("the two artefact_ids are different")
def _diff_artefacts(two_records):
    r1, r2 = two_records
    assert r1["artefact_id"] != r2["artefact_id"]


# ── citation hash / backend selection steps ────────────────────────────────────

@when("I compute the citation hash for the same url and snippet twice",
      target_fixture="two_hashes")
def _hash_same(engine, confirmed_intent):
    from agency._research_citation import compute_citation_hash
    a = compute_citation_hash("https://x.com", "snippet")
    b = compute_citation_hash("https://x.com", "snippet")
    return a, b


@then("both hashes are identical")
def _hashes_equal(two_hashes):
    a, b = two_hashes
    assert a == b
    assert len(a) == 16  # 16-char hex prefix (invariant)


@when("I compute the citation hash for two different snippets at the same url",
      target_fixture="two_hashes")
def _hash_diff(engine, confirmed_intent):
    from agency._research_citation import compute_citation_hash
    a = compute_citation_hash("https://x.com", "alpha")
    b = compute_citation_hash("https://x.com", "beta")
    return a, b


@then("the hashes differ")
def _hashes_differ(two_hashes):
    a, b = two_hashes
    assert a != b


@when("I ask for the research backend with no environment variables set",
      target_fixture="selected_backend")
def _backend_no_key(monkeypatch):
    from agency._research_citation import select_backend
    return select_backend({})


@then(parsers.parse('the selected backend is "{name}"'))
def _backend_name(selected_backend, name):
    assert selected_backend == name


@when("I ask for the research backend with key set but AGENCY_RESEARCH_ANTHROPIC=0",
      target_fixture="selected_backend")
def _backend_disabled(engine, confirmed_intent):
    from agency._research_citation import select_backend
    return select_backend({"ANTHROPIC_API_KEY": "sk-...", "AGENCY_RESEARCH_ANTHROPIC": "0"})


# ── web search backend steps ───────────────────────────────────────────────────

@when("I create a fresh engine with no web_search override",
      target_fixture="fresh_engine")
def _fresh_engine_default(monkeypatch):
    import tempfile
    from agency.engine import Engine
    monkeypatch.delenv("AGENCY_WEB_BACKEND", raising=False)
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@then(parsers.parse('the engine web_search name is "{name}"'))
def _engine_ws_name(fresh_engine, name):
    assert fresh_engine.web_search is not None
    assert fresh_engine.web_search.name == name


@when(parsers.parse('I create a fresh engine with a stub web search client named "{name}"'),
      target_fixture="fresh_engine")
def _fresh_engine_stub(name):
    import tempfile
    from agency.engine import Engine

    class _Stub:
        def __init__(self, n):
            self.name = n
        def search(self, q, k=5):
            return []

    e = Engine(tempfile.mktemp(suffix=".db"), web_search=_Stub(name))
    yield e
    e.memory.close()
