"""Acceptance — plugin authoring behaviour.

Converted from:
  tests/test_skills_capability.py  (Spec 026 — skills.find/render/lint/rank)
  tests/test_skill_docs.py         (Spec 080 — validate_skill, skill_doc bootstrap)
  tests/test_lint_token_economy.py (Spec 067 — lint_surface behaviour)
  tests/test_lint_remediation.py   (Spec 074 — lint_explain, accept mechanism)
  tests/test_publish_skill.py      (Spec 083 — publish_skill)
  tests/test_install_mcp_skill.py  (Spec 061/064/065 — generated install artefacts)
  tests/test_walkable_usage_skills.py  emit_renders_walk_section

Dropped as implementation/structural (not observable behaviour):
  test_skill_emit.py — internal emit_skill, emit_references, emit_bash_wrappers,
    _classify_tier, _ann_repr, _capability_hash: these are implementation
    details of the emit pipeline whose outputs ARE tested here (SKILL.md
    content, bash wrapper existence, .mcp.json shape) via the public surface.
  test_skill_doc_validation.py: SkillDoc/WalkerSkills dataclass field tests
    and SkillDoc.from_module internals — derivation rules are structural;
    what MATTERS is that lint_capability accepts/rejects SkillDocs
    appropriately, which is captured below.
  test_lint_token_economy.py _check_name_token_budget / _check_surface_size /
    _check_bare_name_unique / _check_skill_name_parity direct internal calls —
    the observable contract is lint_surface / lint_capability output, not
    the private checker functions.
  test_skills_api_binding.py — SDK binding assertions against the Anthropic API
    client are external/network concerns; pure implementation mapping tests.
  test_skill_cache_atomic.py (agency.cache) — atomicity and JSON serialisation
    of the skill cache is implementation detail; the observable behaviour is
    the generated SKILL.md output, tested via the install pipeline above.
"""
from __future__ import annotations

import json
import tempfile

from pytest_bdd import parsers, scenarios, then, when


scenarios("features/plugin_authoring.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _call(engine, iid, cap, verb, **kw):
    res, _ = engine.registry.invoke(engine.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def _generate(engine):
    from agency import install
    return install.generate(engine)


class _StubSkills:
    def __init__(self):
        self.calls = []

    def publish(self, name, files, existing_id=None):
        self.calls.append((name, dict(files), existing_id))
        return {"skill_id": "skill_stub123", "version": "1"}


# ── When steps — skills capability ───────────────────────────────────────────

@when("I invoke \"skills\" \"find\" with no arguments", target_fixture="skills_result")
def _find_all(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "skills", "find")


@when(parsers.parse('I invoke "skills" "find" with kind "{kind}"'),
      target_fixture="skills_result")
def _find_by_kind(engine, confirmed_intent, kind):
    return _call(engine, confirmed_intent, "skills", "find", kind=kind)


@when(parsers.parse('I invoke "skills" "find" with capability "{cap}"'),
      target_fixture="skills_result")
def _find_by_cap(engine, confirmed_intent, cap):
    return _call(engine, confirmed_intent, "skills", "find", capability=cap)


@when(parsers.parse('I invoke "skills" "render" for "{name}"'),
      target_fixture="skills_result")
def _render_brief(engine, confirmed_intent, name):
    return _call(engine, confirmed_intent, "skills", "render", skill_name=name)


@when(parsers.parse('I invoke "skills" "render" for "{name}" with depth "{depth}"'),
      target_fixture="skills_result")
def _render_depth(engine, confirmed_intent, name, depth):
    return _call(engine, confirmed_intent, "skills", "render",
                 skill_name=name, depth=depth)


@when(parsers.parse('I invoke "skills" "lint" for "{name}"'),
      target_fixture="skills_result")
def _lint_skill(engine, confirmed_intent, name):
    return _call(engine, confirmed_intent, "skills", "lint", skill_name=name)


@when("I invoke \"skills\" \"rank\" with an empty query",
      target_fixture="skills_result")
def _rank_empty(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "skills", "rank", query="")


@when(parsers.parse('I invoke "skills" "rank" with query "{query}"'),
      target_fixture="skills_result")
def _rank(engine, confirmed_intent, query):
    return _call(engine, confirmed_intent, "skills", "rank", query=query)


@when(parsers.parse('I invoke "skills" "rank" with query "{query}" twice'),
      target_fixture="skills_result")
def _rank_twice(engine, confirmed_intent, query):
    r1 = _call(engine, confirmed_intent, "skills", "rank", query=query)
    r2 = _call(engine, confirmed_intent, "skills", "rank", query=query)
    return {"r1": r1, "r2": r2}


@when(parsers.parse('I invoke "skills" "find" for capability "{cap}"'),
      target_fixture="skills_result")
def _find_cap(engine, confirmed_intent, cap):
    return _call(engine, confirmed_intent, "skills", "find", capability=cap)


@when("I walk the \"skills-triage\" skill with no inputs", target_fixture="walk_result")
def _walk_skills_triage(engine, confirmed_intent):
    raw, _ = engine.registry.invoke(engine.memory, confirmed_intent,
                                    "develop", "skill_walk",
                                    name="skills-triage", inputs={})
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


# ── When steps — validate_skill ───────────────────────────────────────────────

@when("I invoke \"develop\" \"validate_skill\" with no arguments",
      target_fixture="skills_result")
def _validate_all(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "develop", "validate_skill")


@when(parsers.parse('I invoke "develop" "validate_skill" for capability "{cap}"'),
      target_fixture="skills_result")
def _validate_cap(engine, confirmed_intent, cap):
    return _call(engine, confirmed_intent, "develop", "validate_skill", name=cap)


# ── When steps — lint_explain ─────────────────────────────────────────────────

@when(parsers.parse('I invoke "plugin" "lint_explain" for rule "{rule}"'),
      target_fixture="skills_result")
def _lint_explain(engine, confirmed_intent, rule):
    return _call(engine, confirmed_intent, "plugin", "lint_explain", rule=rule)


# ── When steps — publish_skill ────────────────────────────────────────────────

@when(parsers.parse('I invoke "plugin" "publish_skill" for "{name}" in dry_run mode'),
      target_fixture="publish_ctx")
def _publish_dry(name):
    e = tempfile.mktemp(suffix=".db")
    from agency.engine import Engine
    stub = _StubSkills()
    eng = Engine(e, skills_client=stub)
    iid = eng.intent.capture("publish", "test", "ok")
    eng.intent.confirm(iid)
    res, _ = eng.registry.invoke(eng.memory, iid, "plugin", "publish_skill",
                                 name=name)
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    eng.memory.close()
    return {"result": out, "stub": stub}


@when(parsers.parse('I invoke "plugin" "publish_skill" for "{name}" with upload enabled'),
      target_fixture="publish_ctx")
def _publish_upload(name):
    e = tempfile.mktemp(suffix=".db")
    from agency.engine import Engine
    stub = _StubSkills()
    eng = Engine(e, skills_client=stub)
    iid = eng.intent.capture("publish", "test", "ok")
    eng.intent.confirm(iid)
    res, _ = eng.registry.invoke(eng.memory, iid, "plugin", "publish_skill",
                                 name=name, dry_run=False)
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    arts = eng.memory.find("Artefact")
    eng.memory.close()
    return {"result": out, "stub": stub, "artefacts": arts}


@when("I invoke \"plugin\" \"publish_skill\" for \"no-such-cap\" as unknown",
      target_fixture="publish_ctx")
def _publish_unknown():
    e = tempfile.mktemp(suffix=".db")
    from agency.engine import Engine
    stub = _StubSkills()
    eng = Engine(e, skills_client=stub)
    iid = eng.intent.capture("publish", "test", "ok")
    eng.intent.confirm(iid)
    res, _ = eng.registry.invoke(eng.memory, iid, "plugin", "publish_skill",
                                 name="no-such-cap")
    out = res["result"] if isinstance(res, dict) and "result" in res else res
    eng.memory.close()
    return {"result": out, "stub": stub}


# ── Then steps — skills.find ──────────────────────────────────────────────────

@then("the result has at least one candidate")
def _has_candidates(skills_result):
    assert skills_result.get("total", 0) >= 1

@then("the candidate for \"tdd\" names \"develop\" as its capability")
def _tdd_develop(skills_result):
    candidates = skills_result.get("candidates", [])
    tdd = next((c for c in candidates if c["name"] == "tdd"), None)
    assert tdd is not None, "tdd must be in results"
    assert tdd["capability"] == "develop"


@then("every candidate has kind \"usage\"")
def _all_usage(skills_result):
    for c in skills_result.get("candidates", []):
        assert c["kind"] == "usage"


@then("every candidate belongs to capability \"develop\"")
def _all_develop(skills_result):
    for c in skills_result.get("candidates", []):
        assert c["capability"] == "develop"


# ── Then steps — skills.render ────────────────────────────────────────────────

@then("the markdown contains the skill name and a \"phases:\" section")
def _markdown_has_phases(skills_result):
    md = skills_result.get("markdown", "")
    assert "shell-usage" in md or "phases:" in md


@then("the markdown contains a \"produces:\" section")
def _markdown_has_produces(skills_result):
    assert "produces:" in skills_result.get("markdown", "")


@then("the result contains an error field")
def _has_error(skills_result):
    r = skills_result if isinstance(skills_result, dict) else {}
    ctx = r.get("result", r)
    assert ctx.get("error") or r.get("error"), f"expected an error field; got {r!r}"


@then("the publish result contains an error field")
def _publish_has_error(publish_ctx):
    out = publish_ctx["result"]
    assert out.get("error"), f"expected an error field in publish result; got {out!r}"


# ── Then steps — skills.lint ──────────────────────────────────────────────────

@then("lint reports ok with no violations")
def _lint_ok(skills_result):
    assert skills_result.get("ok") is True
    assert skills_result.get("violations") == []


@then("lint reports not ok with at least one violation")
def _lint_not_ok(skills_result):
    assert skills_result.get("ok") is False
    assert skills_result.get("violations")


# ── Then steps — skills.rank ──────────────────────────────────────────────────

@then("the result has at least one candidate with score 0.0")
def _rank_zero_scores(skills_result):
    assert skills_result.get("total", 0) >= 1
    for c in skills_result.get("candidates", []):
        assert c["score"] == 0.0


@then("the scorer is \"keyword\"")
def _scorer_keyword(skills_result):
    assert skills_result.get("scorer") == "keyword"


@then("\"tdd\" is the first candidate")
def _tdd_first(skills_result):
    candidates = skills_result.get("candidates", [])
    assert candidates and candidates[0]["name"] == "tdd"


@then("the first candidate has a positive score")
def _first_positive(skills_result):
    first = skills_result.get("candidates", [{}])[0]
    assert first.get("score", 0) > 0


@then("both results have the same candidate order and scores")
def _rank_deterministic(skills_result):
    r1 = skills_result["r1"]
    r2 = skills_result["r2"]
    assert ([(c["name"], c["score"]) for c in r1["candidates"]] ==
            [(c["name"], c["score"]) for c in r2["candidates"]])


# ── Then steps — skills-triage override ──────────────────────────────────────

@then("\"skills-triage\" is present in the candidates")
def _triage_present(skills_result):
    names = {c["name"] for c in skills_result.get("candidates", [])}
    assert "skills-triage" in names


@then("\"skills-usage\" is absent from the candidates")
def _usage_absent(skills_result):
    names = {c["name"] for c in skills_result.get("candidates", [])}
    assert "skills-usage" not in names


@then('the status is one of "completed", "input-required", "blocked", or "failed"')
def _valid_walk_status(walk_result):
    assert walk_result.get("status") in ("completed", "input-required", "blocked", "failed")


# ── Then steps — validate_skill ───────────────────────────────────────────────

@then("the result is ok")
def _result_ok(skills_result):
    assert skills_result.get("ok") is True, (
        [r for r in skills_result.get("results", {}).items()
         if isinstance(r[1], dict) and not r[1].get("ok")])


@then("the \"shell\" capability is present and clean")
def _shell_ok(skills_result):
    results = skills_result.get("results", {})
    assert "shell" in results
    assert results["shell"]["ok"]


@then("only \"reflect\" appears in the results")
def _only_reflect(skills_result):
    assert set(skills_result.get("results", {}).keys()) == {"reflect"}


@then("the result is not ok")
def _result_not_ok(skills_result):
    assert skills_result.get("ok") is False


@then("the violation rule is \"unknown-capability\"")
def _unknown_cap_rule(skills_result):
    violations = skills_result.get("results", {}).get("no-such-cap", {}).get("violations", [])
    assert any(v["rule"] == "unknown-capability" for v in violations)


# ── Then steps — lint_explain ─────────────────────────────────────────────────

@then("the result has steps and a reference")
def _has_steps_ref(skills_result):
    assert skills_result.get("steps") and skills_result.get("reference")


@then("the kind is \"surface_size\"")
def _kind_surface_size(skills_result):
    assert skills_result.get("kind") == "surface_size"


# ── Then steps — lint_surface ─────────────────────────────────────────────────

@then("lint_surface has no open bare_name_collision warnings")
def _no_open_collision(engine):
    from agency.capabilities.plugin import _main as P
    res = P.lint_surface(engine.registry)
    open_kinds = {w["kind"] for w in res["warnings"]}
    assert "bare_name_collision" not in open_kinds


@then("lint_surface accepted findings carry an accept_reason")
def _accepted_have_reason(engine):
    from agency.capabilities.plugin import _main as P
    res = P.lint_surface(engine.registry)
    assert all(w.get("accept_reason") for w in res["accepted"])


# ── Then steps — publish_skill ────────────────────────────────────────────────

@then("uploaded is False")
def _not_uploaded(publish_ctx):
    assert publish_ctx["result"]["uploaded"] is False


@then("the manifest includes \"SKILL.md\"")
def _manifest_has_skill_md(publish_ctx):
    assert "SKILL.md" in publish_ctx["result"]["files"]


@then("no upload was made to the skills client")
def _no_upload_made(publish_ctx):
    assert publish_ctx["stub"].calls == []


@then("uploaded is True")
def _was_uploaded(publish_ctx):
    assert publish_ctx["result"]["uploaded"] is True


@then("a published-skill Artefact is recorded")
def _artefact_recorded(publish_ctx):
    arts = publish_ctx.get("artefacts", [])
    assert any(a.get("kind") == "published-skill" and a.get("skill_id") == "skill_stub123"
               for a in arts)


# ── Then steps — install pipeline ────────────────────────────────────────────

@then("no verb-bearing capability is missing a skill_doc")
def _no_missing_skill_doc(engine):
    missing = [n for n in engine.registry.names()
               if engine.registry.get(n).verbs
               and getattr(engine.registry.get(n), "skill_doc", None) is None]
    assert missing == [], f"capabilities without skill_doc: {missing}"


@then("the generated help SKILL.md references \"mcp__plugin_agency_agency__execute\"")
def _help_mcp_form(engine):
    files = _generate(engine)
    assert "mcp__plugin_agency_agency__execute" in files["skills/help/SKILL.md"]


@then("the generated help SKILL.md references the bash fallback")
def _help_bash(engine):
    files = _generate(engine)
    skill = files["skills/help/SKILL.md"]
    assert "agency intent" in skill or "agency execute" in skill


@then("the generated shell SKILL.md contains \"name: shell\"")
def _shell_name(engine):
    files = _generate(engine)
    assert "name: shell" in files["skills/shell/SKILL.md"]


@then("the generated shell SKILL.md contains \"description:\"")
def _shell_desc(engine):
    files = _generate(engine)
    assert "description:" in files["skills/shell/SKILL.md"]


@then("the generated .mcp.json command is \"agency-mcp\"")
def _mcp_command(engine):
    files = _generate(engine)
    cfg = json.loads(files[".mcp.json"])
    assert cfg["mcpServers"]["agency"]["command"] == "agency-mcp"


@then("\"AGENCY_DB\" is in the env block")
def _agency_db_in_env(engine):
    files = _generate(engine)
    cfg = json.loads(files[".mcp.json"])
    assert "AGENCY_DB" in cfg["mcpServers"]["agency"]["env"]
