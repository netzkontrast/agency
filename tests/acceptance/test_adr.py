"""Acceptance — ADR ontology + capability, author & validate (Spec 354 Slice 1).

Behaviour through the real Engine registry (records provenance like any verb):
- the `adr` capability registers (drop-in bar);
- `adr.draft` mints a WH(Y) `Decision` that SERVES the intent;
- the ontology rejects a malformed Decision (missing WH(Y) field / bad status);
- `adr.validate` returns decidable WHY findings (WHY-001 / WHY-003) and an ok flag.
"""
from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke, served, tool_names

scenarios("features/adr.feature")


_GOOD = dict(
    context="the bi-temporal graph store",
    facing="cross-session persistence with full history",
    decision="a single append-only GraphQLite graph",
    neglected="a relational mirror, an event log, a document store",
    benefits="one-traversal provenance and keep-both reconciliation",
    tradeoffs="every read must be supersession-aware (as_of)",
)


@given(parsers.parse('an adr theme "{layer}"'), target_fixture="theme_id")
def _theme(engine, confirmed_intent, layer):
    res, _ = invoke(engine, confirmed_intent, "adr", "theme",
                    layer=layer, title=f"{layer} decisions", scope=layer)
    return res.get("id")


@when("I draft a well-formed decision under that theme",
      target_fixture="decision_ctx")
def _draft_good(engine, confirmed_intent, theme_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **_GOOD)
    return res


@when(parsers.parse('I draft a decision with an empty "{field}" field under that theme'),
      target_fixture="decision_ctx")
def _draft_empty(engine, confirmed_intent, theme_id, field):
    fields = dict(_GOOD)
    fields[field] = ""
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **fields)
    return res


@when(parsers.parse('I draft a decision whose "{field}" field is "{value}" under that theme'),
      target_fixture="decision_ctx")
def _draft_value(engine, confirmed_intent, theme_id, field, value):
    fields = dict(_GOOD)
    fields[field] = value
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **fields)
    return res


@when(parsers.parse('I draft a decision with an over-long "{field}" field under that theme'),
      target_fixture="decision_ctx")
def _draft_overlong(engine, confirmed_intent, theme_id, field):
    fields = dict(_GOOD)
    fields[field] = "x" * 500          # well over any WH(Y) maxLength budget
    res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                    theme_id=theme_id, **fields)
    return res


@when(parsers.parse('I create a Decision node missing the "{field}" field'),
      target_fixture="adr_result")
def _create_missing(engine, confirmed_intent, field):
    props = dict(_GOOD, status="proposed")
    props.pop(field, None)
    res, _ = invoke(engine, confirmed_intent, "manage", "create",
                    label="Decision", props=props)
    return res


@when(parsers.parse('I create a Decision node with status "{status}"'),
      target_fixture="adr_result")
def _create_bad_status(engine, confirmed_intent, status):
    props = dict(_GOOD, status=status)
    res, _ = invoke(engine, confirmed_intent, "manage", "create",
                    label="Decision", props=props)
    return res


@when("I validate that decision", target_fixture="validate_result")
def _validate(engine, confirmed_intent, decision_ctx):
    res, _ = invoke(engine, confirmed_intent, "adr", "validate",
                    decision_id=decision_ctx.get("id"))
    return res


@then(parsers.parse('a wire tool name contains "{frag}"'))
def _wire_contains(engine, frag):
    # The full per-verb wire surface is the non-code-mode build (code-mode
    # deliberately exposes only search/get_schema/execute — Goal 5).
    names = tool_names(engine, codemode=False)
    assert any(frag in n for n in names), sorted(names)


@then(parsers.parse('the decision result has status "{status}"'))
def _status_is(decision_ctx, status):
    assert decision_ctx.get("status") == status, decision_ctx


@then("the decision serves the intent")
def _serves(engine, confirmed_intent):
    assert served(engine, confirmed_intent, "Decision") >= 1


@then("the adr result is an error")
def _is_error(adr_result):
    assert adr_result.get("error"), adr_result


@then("the decision result is an error")
def _decision_is_error(decision_ctx):
    assert decision_ctx.get("error"), decision_ctx


@then(parsers.parse('the validate findings include rule "{rule}" with severity "{sev}"'))
def _finding_present(validate_result, rule, sev):
    findings = validate_result.get("findings") or []
    assert any(f.get("rule") == rule and f.get("severity") == sev for f in findings), findings


@then("the validate result is not ok")
def _not_ok(validate_result):
    assert validate_result.get("ok") is False, validate_result


@then("the validate result is ok")
def _ok(validate_result):
    assert validate_result.get("ok") is True, validate_result


# ── Slice 2 — link / supersede / theme_status / impact / render ───────────────

@when(parsers.parse('I draft decisions "{a}" and "{b}" under that theme'),
      target_fixture="decisions")
def _draft_two(engine, confirmed_intent, theme_id, a, b):
    out: dict[str, str] = {}
    for name in (a, b):
        res, _ = invoke(engine, confirmed_intent, "adr", "draft",
                        theme_id=theme_id,
                        **dict(_GOOD, decision=f"{name}: {_GOOD['decision']}"))
        out[name] = res.get("id")
    return out


@when(parsers.parse('I link "{a}" DEPENDS_ON "{b}"'), target_fixture="link_result")
def _link(engine, confirmed_intent, decisions, a, b):
    res, _ = invoke(engine, confirmed_intent, "adr", "link",
                    source_id=decisions[a], dependency_type="DEPENDS_ON",
                    target_id=decisions[b])
    return res


@when(parsers.parse('I set "{name}" to status "{status}"'))
def _set_status(engine, confirmed_intent, decisions, name, status):
    # The DOMAIN mutator — adr.update, not the generic manage tool.
    invoke(engine, confirmed_intent, "adr", "update",
           decision_id=decisions[name], status=status)


@when(parsers.parse('I supersede "{name}" with a new decision'),
      target_fixture="supersede_result")
def _supersede(engine, confirmed_intent, decisions, name):
    res, _ = invoke(engine, confirmed_intent, "adr", "supersede",
                    old_id=decisions[name],
                    **dict(_GOOD, decision="revised: " + _GOOD["decision"]))
    return res


@when("I check the theme status", target_fixture="status_result")
def _theme_status(engine, confirmed_intent, theme_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "theme_status",
                    theme_id=theme_id)
    return res


@when("I render that theme", target_fixture="render_result")
def _render(engine, confirmed_intent, theme_id):
    res, _ = invoke(engine, confirmed_intent, "adr", "render", theme_id=theme_id)
    return res


@then("the link result is linked")
def _link_ok(link_result):
    assert link_result.get("linked") is True, link_result


@then(parsers.parse('the impact of "{name}" includes at least one dependent'))
def _impact_has(engine, confirmed_intent, decisions, name):
    res, _ = invoke(engine, confirmed_intent, "adr", "impact",
                    decision_id=decisions[name])
    assert res.get("total", 0) >= 1, res


@then(parsers.parse('the link result is an error with rule "{rule}"'))
def _link_err(link_result, rule):
    assert link_result.get("error"), link_result
    assert link_result.get("rule") == rule, link_result


@then("the supersede result has a new decision id")
def _supersede_new(supersede_result):
    assert supersede_result.get("new_id"), supersede_result


@then(parsers.parse('the superseded decision "{name}" now has status "{status}"'))
def _old_superseded(engine, confirmed_intent, decisions, name, status):
    res, _ = invoke(engine, confirmed_intent, "adr", "read",
                    decision_id=decisions[name])
    assert res.get("status") == status, res


@then(parsers.parse('the aggregate status is "{agg}"'))
def _agg_is(status_result, agg):
    assert status_result.get("status") == agg, status_result


@then(parsers.parse('the render reports {n:d} active and {m:d} superseded decisions'))
def _render_counts(render_result, n, m):
    assert render_result.get("active") == n, render_result
    assert render_result.get("superseded") == m, render_result


@then("re-rendering produces the same content hash")
def _render_idempotent(engine, confirmed_intent, theme_id, render_result):
    res, _ = invoke(engine, confirmed_intent, "adr", "render", theme_id=theme_id)
    assert res.get("content_sha") == render_result.get("content_sha"), res


# ── Slice 3 — catalogue ───────────────────────────────────────────────────────

@when("I list the adr catalogue", target_fixture="catalogue")
def _catalogue(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "adr", "catalogue")
    return res


@then(parsers.parse("the catalogue has {n:d} theme with {m:d} decisions"))
def _catalogue_counts(catalogue, n, m):
    assert catalogue.get("total_themes") == n, catalogue
    assert catalogue.get("total_decisions") == m, catalogue


# ── Spec 353/354 — the architecture digest (adr.architecture) ─────────────────

@when("I rebuild the architecture digest over two thematic adr files",
      target_fixture="arch_result")
def _architecture(engine, confirmed_intent):
    import tempfile, pathlib
    d = pathlib.Path(tempfile.mkdtemp())
    # datalayer: 2 live decisions; substrate: 1 live + a superseded appendix
    # (excluded) — also exercises the leading Spec-292 anchor strip.
    (d / "adr-datalayer.md").write_text(
        "<!-- agency-node: adr-theme-datalayer -->\n---\nkind: adr-theme\n"
        "layer: datalayer\ntitle: \"Datalayer\"\nscope: \"state\"\n---\n\n"
        "# Datalayer\n\n## one store for every concept\nx\n\n"
        "## keep-both reconciliation\ny\n", encoding="utf-8")
    (d / "adr-substrate.md").write_text(
        "---\nkind: adr-theme\nlayer: substrate\ntitle: \"Substrate\"\n---\n\n"
        "# Substrate\n\n## three wire verbs\nz\n\n"
        "## Superseded / history\n- old-one\n", encoding="utf-8")
    (d / "README.md").write_text("# index — not a theme\n", encoding="utf-8")
    res, _ = invoke(engine, confirmed_intent, "adr", "architecture",
                    adr_dir=str(d), apply=False)
    return res


@then(parsers.parse("the digest covers {n:d} layers with {m:d} decisions"))
def _architecture_counts(arch_result, n, m):
    assert len(arch_result.get("layers", [])) == n, arch_result
    assert arch_result.get("decisions") == m, arch_result
    # the superseded appendix line must NOT count as a decision
    assert "old-one" not in arch_result.get("body", ""), arch_result
