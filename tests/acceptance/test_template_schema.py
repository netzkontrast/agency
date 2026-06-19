"""Acceptance — template and schema bootstrap/lint/coverage behaviour.

Converted from:
  tests/test_template_bootstrap_wireup.py (Spec 060 Phase 1 — bootstrap wire-up)
  tests/test_template_folder_lint.py      (Spec 060 Phase 4 — lint rule)
  tests/test_template_schema_coverage.py  (Spec 153 — coverage audit)

Dropped as implementation/structural (not observable behaviour):
  test_path_safety.py — exercises an internal helper `_safe_path` that
    validates path-traversal guards inside the template loader. The loader's
    safety is a structural property reviewed in code; what matters here is
    the observable bootstrap outcome (templates are available) and lint output.
  Schema-discovery helpers (schema_paths, schema_labels with tmp_path
    construction): unit tests of the audit library's internal functions.
    The BEHAVIOUR is the CoverageReport returned by audit_schemas, which
    is covered by the scenario group below.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from pytest_bdd import scenarios, then, when

scenarios("features/template_schema.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_cap_with_template(tmp_path: Path, filename: str, content: str):
    from agency.capability import CapabilityBase, OntologyExtension, RenderTemplates, verb

    class _Cap(CapabilityBase):
        name = "tpl_test"
        home = "memory"
        ontology = OntologyExtension(nodes={})
        render_templates = RenderTemplates(folder=tmp_path / "templates")

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "templates" / filename).write_text(content)
    return _Cap


def _make_cap_no_templates():
    from agency.capability import CapabilityBase, OntologyExtension, verb

    class _Cap(CapabilityBase):
        name = "tpl_none"
        home = "memory"
        ontology = OntologyExtension(nodes={})

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    return _Cap


# ── Given steps — template bootstrap ─────────────────────────────────────────

@pytest.fixture
def bootstrap_ctx(tmp_path):
    """Bootstrap context: holds the tmp_path; engine built lazily per scenario."""
    return {"tmp_path": tmp_path}


@when("I boot the engine with that capability")
def _noop_boot():
    """Placeholder — engine is built inside the Then step using bootstrap_ctx."""


# ── Given/When steps — template bootstrap ────────────────────────────────────

@pytest.fixture
def template_engine_ctx(tmp_path):
    """A bootstrapped engine with a capability whose templates folder
    contains 'greeting.md' with an AGENT instruction block."""
    from agency.capability import CapabilityBase, OntologyExtension, RenderTemplates, ArtefactSchemas, verb
    from agency.engine import Engine

    templates_dir = tmp_path / "templates"
    schemas_dir = tmp_path / "schemas"
    templates_dir.mkdir()
    schemas_dir.mkdir()
    (templates_dir / "greeting.md").write_text(
        "# Hello $name\n<!-- AGENT: greet the user warmly. -->\n")
    (schemas_dir / "greeter-payload.json").write_text(
        '{"required": ["name", "session_id"]}')

    class _Cap(CapabilityBase):
        name = "bootstrap_test"
        home = "memory"
        ontology = OntologyExtension(nodes={})
        render_templates = RenderTemplates(folder=templates_dir)
        artefact_schemas = ArtefactSchemas(folder=schemas_dir)

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    e = Engine(tempfile.mktemp(suffix=".db"),
               extra_capabilities=[_Cap.as_capability()], _require_skill_doc=False)
    yield e
    e.memory.close()


# ── Given steps — template bootstrap (features) ───────────────────────────────
# pytest-bdd matches these as the Background step in template_schema.feature
# Background: "Given a fresh agency engine in code-mode" is handled by conftest.
# The bootstrap scenarios use template_engine_ctx directly.

pytest.fixture(name="given an extra capability with a templates folder containing \"greeting.md\"")(lambda: None)

# ── Then steps — template bootstrap ──────────────────────────────────────────

@then("\"greeting\" is reachable via the engine ontology templates")
def _greeting_in_templates(template_engine_ctx):
    assert "greeting" in template_engine_ctx.ontology.templates


@then("\"greeter-payload\" is reachable via the engine ontology schemas")
def _schema_in_ontology(template_engine_ctx):
    assert "greeter-payload" in template_engine_ctx.ontology.schemas


@then("ctx.template(\"greeting\") returns a template with the expected body")
def _ctx_template_works(template_engine_ctx):
    from agency.capability import CapabilityContext
    e = template_engine_ctx
    iid = e.intent.capture_and_confirm("t", "x", "x", owner="user")
    ctx = CapabilityContext(
        memory=e.memory, ontology=e.ontology, registry=e.registry,
        intent_id=iid, agent_id="agent:test", engine=e)
    tpl = ctx.template("greeting")
    body = tpl.template if hasattr(tpl, "template") else str(tpl)
    assert "Hello $name" in body


@then("ctx.template(\"missing\") raises KeyError")
def _ctx_template_missing_raises(template_engine_ctx):
    from agency.capability import CapabilityContext
    e = template_engine_ctx
    iid = e.intent.capture_and_confirm("t", "x", "x", owner="user")
    ctx = CapabilityContext(
        memory=e.memory, ontology=e.ontology, registry=e.registry,
        intent_id=iid, agent_id="agent:test", engine=e)
    with pytest.raises(KeyError, match="missing"):
        ctx.template("missing")


@then("bootstrapping the engine raises ValueError mentioning the collision")
def _collision_raises(tmp_path):
    from agency.capability import CapabilityBase, OntologyExtension, ArtefactSchemas, verb
    from agency.engine import Engine

    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "collide.json").write_text('{"required": ["x"]}')

    class _CollideCap(CapabilityBase):
        name = "collide_test"
        home = "memory"
        ontology = OntologyExtension(nodes={}, schemas={"collide": ["y"]})
        artefact_schemas = ArtefactSchemas(folder=schemas_dir)

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    with pytest.raises(ValueError, match=r"collide.*declared both"):
        Engine(tempfile.mktemp(suffix=".db"),
               extra_capabilities=[_CollideCap.as_capability()],
               _require_skill_doc=False)


# ── Given steps — we don't need explicit Given steps for bootstrap scenarios
# because the feature Background is "a fresh agency engine in code-mode",
# satisfied by conftest. The template_engine_ctx fixture is used directly.

# pytest-bdd Given hooks for the "Given an extra capability..." lines
from pytest_bdd import given  # noqa: E402

@given("an extra capability with a templates folder containing \"greeting.md\"",
       target_fixture="template_engine_ctx")
def _given_greeting(tmp_path):
    """Build engine fixture inline when the Given step appears in a scenario."""
    from agency.capability import CapabilityBase, OntologyExtension, RenderTemplates, ArtefactSchemas, verb
    from agency.engine import Engine

    templates_dir = tmp_path / "templates"
    schemas_dir = tmp_path / "schemas"
    templates_dir.mkdir()
    schemas_dir.mkdir()
    (templates_dir / "greeting.md").write_text(
        "# Hello $name\n<!-- AGENT: greet the user warmly. -->\n")
    (schemas_dir / "greeter-payload.json").write_text(
        '{"required": ["name", "session_id"]}')

    class _Cap(CapabilityBase):
        name = "bootstrap_test2"
        home = "memory"
        ontology = OntologyExtension(nodes={})
        render_templates = RenderTemplates(folder=templates_dir)
        artefact_schemas = ArtefactSchemas(folder=schemas_dir)

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    e = Engine(tempfile.mktemp(suffix=".db"),
               extra_capabilities=[_Cap.as_capability()], _require_skill_doc=False)
    yield e
    e.memory.close()


@given("an extra capability with a schemas folder containing \"greeter-payload.json\"",
       target_fixture="template_engine_ctx")
def _given_schema(tmp_path):
    from agency.capability import CapabilityBase, OntologyExtension, RenderTemplates, ArtefactSchemas, verb
    from agency.engine import Engine

    templates_dir = tmp_path / "templates"
    schemas_dir = tmp_path / "schemas"
    templates_dir.mkdir()
    schemas_dir.mkdir()
    (templates_dir / "greeting.md").write_text(
        "# Hello $name\n<!-- AGENT: greet the user warmly. -->\n")
    (schemas_dir / "greeter-payload.json").write_text(
        '{"required": ["name", "session_id"]}')

    class _Cap(CapabilityBase):
        name = "bootstrap_test3"
        home = "memory"
        ontology = OntologyExtension(nodes={})
        render_templates = RenderTemplates(folder=templates_dir)
        artefact_schemas = ArtefactSchemas(folder=schemas_dir)

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    e = Engine(tempfile.mktemp(suffix=".db"),
               extra_capabilities=[_Cap.as_capability()], _require_skill_doc=False)
    yield e
    e.memory.close()


@given("an extra capability with a colliding schema in both OntologyExtension and file")
def _given_collision():
    """No-op: the collision is exercised inside the Then step."""


# ── Given steps — template folder lint ───────────────────────────────────────

def _lint_cap(name, folder, filename, content):
    from agency.capability import CapabilityBase, OntologyExtension, RenderTemplates, verb
    from agency.capabilities.plugin import lint_capability

    (folder / "templates").mkdir(exist_ok=True, parents=True)
    if filename:
        (folder / "templates" / filename).write_text(content)

    class _Cap(CapabilityBase):
        pass
    _Cap.name = name
    _Cap.home = "memory"
    _Cap.ontology = OntologyExtension(nodes={})
    _Cap.render_templates = RenderTemplates(folder=folder / "templates")

    @verb(role="transform")
    def ping(self) -> dict:
        """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
        return {"ok": True}
    _Cap.ping = ping
    return lint_capability(_Cap.as_capability())


@given("a capability whose template \"greeting.md\" has an AGENT instruction block",
       target_fixture="lint_result")
def _cap_with_agent_block(tmp_path):
    return _lint_cap("tpl_good", tmp_path, "greeting.md",
                     "# Hello\n<!-- AGENT: greet warmly -->\n")


@given("a capability whose template \"silent.md\" has no AGENT instruction block",
       target_fixture="lint_result")
def _cap_without_agent_block(tmp_path):
    return _lint_cap("tpl_silent", tmp_path, "silent.md", "# Hello world\n")


@given("a capability whose template is named \"BadName.md\" with an AGENT block",
       target_fixture="lint_result")
def _cap_bad_filename(tmp_path):
    return _lint_cap("tpl_bad", tmp_path, "BadName.md",
                     "# x\n<!-- AGENT: do thing -->\n")


@given("a capability whose render_templates points to a nonexistent folder",
       target_fixture="lint_result")
def _cap_missing_folder(tmp_path):
    from agency.capability import CapabilityBase, OntologyExtension, RenderTemplates, verb
    from agency.capabilities.plugin import lint_capability

    class _Cap(CapabilityBase):
        pass
    _Cap.name = "tpl_missing"
    _Cap.home = "memory"
    _Cap.ontology = OntologyExtension(nodes={})
    _Cap.render_templates = RenderTemplates(folder=tmp_path / "does_not_exist")

    @verb(role="transform")
    def ping(self) -> dict:
        """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
        return {"ok": True}
    _Cap.ping = ping
    return lint_capability(_Cap.as_capability())


@given("a capability with no render_templates attribute", target_fixture="lint_result")
def _cap_no_render_templates():
    from agency.capability import CapabilityBase, OntologyExtension, verb
    from agency.capabilities.plugin import lint_capability

    class _Cap(CapabilityBase):
        name = "tpl_none"
        home = "memory"
        ontology = OntologyExtension(nodes={})

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.\n\nInputs: none.\nReturns: ``{ok}``.\nchain_next: terminal.\n"""
            return {"ok": True}

    return lint_capability(_Cap.as_capability())


# ── Then steps — template folder lint ────────────────────────────────────────

@then("lint_capability reports no template_folder findings")
def _no_template_findings(lint_result):
    findings = [v for v in (lint_result["violations"] + lint_result["warnings"])
                if v.get("kind") == "template_folder"]
    assert findings == []


@then("lint_capability reports a template_folder finding mentioning \"silent.md\"")
def _finding_silent(lint_result):
    findings = [v for v in (lint_result["violations"] + lint_result["warnings"])
                if v.get("kind") == "template_folder"]
    assert findings
    assert any("silent.md" in v["verb"] for v in findings)


@then("lint_capability reports a template_folder finding about kebab-case")
def _finding_kebab(lint_result):
    findings = [v for v in (lint_result["violations"] + lint_result["warnings"])
                if v.get("kind") == "template_folder" and "kebab-case" in v["msg"]]
    assert findings


@then("lint_capability reports a template_folder finding about missing folder")
def _finding_missing(lint_result):
    findings = [v for v in (lint_result["violations"] + lint_result["warnings"])
                if v.get("kind") == "template_folder" and "does not exist" in v["msg"]]
    assert findings


# ── Given steps — schema coverage ────────────────────────────────────────────

@given("a schemas folder with \"intent.json\" and ontology labels {\"Intent\", \"Reflection\"}",
       target_fixture="audit_ctx")
def _audit_setup(tmp_path):
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "intent.json").write_text(
        '{"title": "Intent"}')
    return {"root": tmp_path, "ontology": {"Intent", "Reflection"}}


@given("an empty ontology labels set", target_fixture="audit_ctx")
def _audit_empty(tmp_path):
    return {"root": tmp_path, "ontology": set()}


@given("a schemas folder with \"wire.json\" titled \"GateOutcome\" and ontology labels {\"Gate\"}",
       target_fixture="audit_ctx")
def _audit_non_node(tmp_path):
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "wire.json").write_text(
        '{"title": "GateOutcome"}')
    return {"root": tmp_path, "ontology": {"Gate"}}


@given("a mix of node and non-node schemas in the folder", target_fixture="audit_ctx")
def _audit_mixed(tmp_path):
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "intent.json").write_text(
        '{"title": "Intent"}')
    (tmp_path / "capabilities" / "a" / "schemas" / "wire.json").write_text(
        '{"title": "GateOutcome"}')
    return {"root": tmp_path, "ontology": {"Intent"}}


# ── When steps — schema coverage ─────────────────────────────────────────────

@when("I run the schema coverage audit", target_fixture="coverage_report")
def _run_audit(audit_ctx):
    from scripts.check_schema_coverage import audit_schemas
    return audit_schemas(audit_ctx["root"], ontology_labels=audit_ctx["ontology"])


@when("I run the schema coverage audit against the live agency tree",
      target_fixture="coverage_report")
def _run_live_audit():
    from agency.engine import Engine
    from scripts.check_schema_coverage import audit_schemas, truly_inline_schemas
    repo = Path(__file__).parent.parent.parent
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
        merged = dict(e.ontology.schemas)
    finally:
        e.memory.close()
    inline = truly_inline_schemas(repo / "agency", merged)
    return audit_schemas(repo / "agency", ontology_labels=ontology,
                         ontology_schemas=inline)


@when("I run the live audit and compare to the committed baseline",
      target_fixture="coverage_report")
def _run_baseline_audit(monkeypatch):
    from agency.engine import Engine
    from scripts.check_schema_coverage import (
        audit_schemas, truly_inline_schemas, load_schema_baseline,
        compare_uncovered_to_baseline)
    monkeypatch.chdir(Path(__file__).parent.parent.parent)
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
        merged = dict(e.ontology.schemas)
    finally:
        e.memory.close()
    root = Path("agency")
    inline = truly_inline_schemas(root, merged)
    rep = audit_schemas(root, ontology_labels=ontology, ontology_schemas=inline)
    baseline = load_schema_baseline(
        Path("Plan/_planning/schema-coverage-baseline.txt"))
    res = compare_uncovered_to_baseline(rep, baseline)
    return res


# ── Then steps — schema coverage ─────────────────────────────────────────────

@then("\"Intent\" is covered and \"Reflection\" is uncovered")
def _intent_covered(coverage_report):
    assert "Intent" in coverage_report.covered
    assert "Reflection" in coverage_report.uncovered


@then("the coverage fraction is between 0.0 and 1.0")
def _fraction_range(coverage_report):
    assert 0.0 <= coverage_report.coverage_fraction <= 1.0


@then("the coverage fraction is 1.0")
def _full_coverage(coverage_report):
    assert coverage_report.coverage_fraction == 1.0


@then("\"GateOutcome\" is in non_node_schemas and coverage is 0.0")
def _non_node_schema(coverage_report):
    assert "GateOutcome" in coverage_report.non_node_schemas
    assert coverage_report.coverage_fraction == 0.0


@then("the covered set is a subset of the ontology labels")
def _subset_invariant(audit_ctx, coverage_report):
    assert coverage_report.covered <= audit_ctx["ontology"]


@then("the result is a CoverageReport with valid covered, uncovered, and fraction fields")
def _live_report_valid(coverage_report):
    from scripts.check_schema_coverage import CoverageReport
    assert isinstance(coverage_report, CoverageReport)
    assert isinstance(coverage_report.covered, set)
    assert isinstance(coverage_report.uncovered, set)
    assert 0.0 <= coverage_report.coverage_fraction <= 1.0


@then("there are no new uncovered labels")
def _no_new_uncovered(coverage_report):
    assert coverage_report.new_uncovered == set(), (
        "live audit produced uncovered labels NOT in the baseline.\n"
        + "\n".join(f"  {l}" for l in sorted(coverage_report.new_uncovered)))


@then("there are no newly-covered labels still in the baseline")
def _no_fixed_in_baseline(coverage_report):
    assert coverage_report.fixed_uncovered == set(), (
        "baseline lists labels now covered — trim them.\n"
        + "\n".join(f"  {l}" for l in sorted(coverage_report.fixed_uncovered)))


# The named set of core provenance node types — the substrate spine every
# session writes (Intent → Invocation performed-by Agent; Gate decisions;
# the steward's own MaintenanceRun). Spec 153 Slice 6 backfills schemas for
# these highest-traffic labels first (doctor `priority_uncovered` ranking).
# A named contract set, not a snapshot count (CLAUDE.md rule 8).
CORE_PROVENANCE_LABELS = {"Intent", "Agent", "Invocation", "MaintenanceRun", "Gate"}


@then("the core provenance labels are all schema-covered")
def _core_provenance_covered(coverage_report):
    missing = CORE_PROVENANCE_LABELS - coverage_report.covered
    assert not missing, (
        "core substrate provenance labels lack a Schema (Spec 153 Slice 6):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@when("I boot the live engine", target_fixture="loaded_schema_titles")
def _boot_engine_schema_titles():
    """A schema FILE counted by the glob audit is dormant unless its
    capability DECLARES `artefact_schemas` so the engine loads it. This
    asserts the stronger invariant: the engine ontology actually carries
    each core schema (guards the Slice 6 declaration regression)."""
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        titles = {v.get("title") for v in e.ontology.schemas.values()
                  if isinstance(v, dict)}
    finally:
        e.memory.close()
    return titles


@then("the core provenance labels each have a loaded ontology schema")
def _core_provenance_loaded(loaded_schema_titles):
    missing = CORE_PROVENANCE_LABELS - loaded_schema_titles
    assert not missing, (
        "core provenance schemas are on disk but NOT loaded by the engine "
        "(declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


# The document-convergence set: Artefact (PRODUCES spine), Document (the
# universal convergence artefact — Spec 292), Session (session graph node),
# AcceptanceCriterion (VALIDATES-edged fulfilment node — Spec 317).
# Spec 153 Slice 6 continuation — next highest-traffic uncovered labels.
# A named contract set, not a snapshot count (CLAUDE.md rule 8).
DOC_CONVERGENCE_LABELS = {"AcceptanceCriterion", "Artefact", "Session", "Document"}


@then("the document convergence labels are all schema-covered")
def _doc_convergence_covered(coverage_report):
    missing = DOC_CONVERGENCE_LABELS - coverage_report.covered
    assert not missing, (
        "document-convergence labels lack a Schema (Spec 153 Slice 6 cont.):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@then("the document convergence labels each have a loaded ontology schema")
def _doc_convergence_loaded(loaded_schema_titles):
    missing = DOC_CONVERGENCE_LABELS - loaded_schema_titles
    assert not missing, (
        "document-convergence schemas are on disk but NOT loaded by the engine "
        "(declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


# The workflow-spine set: Lifecycle (pillar concept), Event (substrate hooks,
# Spec 076), Phase (skill-walk progression), Skill (capability-skill surface),
# ClarificationQuestion (discover/clarify node, Spec 311).
# Spec 153 Slice 6 continuation — next coverage wave targeting the four-pillar
# surface. A named contract set, not a snapshot count (CLAUDE.md rule 8).
WORKFLOW_SPINE_LABELS = {"Lifecycle", "Event", "Phase", "Skill", "ClarificationQuestion"}


@then("the workflow spine labels are all schema-covered")
def _workflow_spine_covered(coverage_report):
    missing = WORKFLOW_SPINE_LABELS - coverage_report.covered
    assert not missing, (
        "workflow-spine labels lack a Schema (Spec 153 Slice 6 — workflow-spine wave):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@then("the workflow spine labels each have a loaded ontology schema")
def _workflow_spine_loaded(loaded_schema_titles):
    missing = WORKFLOW_SPINE_LABELS - loaded_schema_titles
    assert not missing, (
        "workflow-spine schemas are on disk but NOT loaded by the engine "
        "(declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


# ── Slice 4: engine-load intersection gate ───────────────────────────────────

@given("a capability with a schema file for \"Dormant\" but no artefact_schemas declaration",
       target_fixture="dormant_audit_ctx")
def _given_dormant_schema(tmp_path):
    """A schema file on disk whose cap never declares artefact_schemas — the
    engine won't load it, so the intersection gate must move it to dormant_schemas."""
    (tmp_path / "capabilities" / "a" / "schemas").mkdir(parents=True)
    (tmp_path / "capabilities" / "a" / "schemas" / "dormant.json").write_text(
        '{"title": "Dormant"}')
    return {"root": tmp_path, "ontology": {"Dormant"}, "engine_loaded": set()}


@when("I run the schema coverage audit with engine_loaded_titles excluding \"Dormant\"",
      target_fixture="dormant_report")
def _run_dormant_audit(dormant_audit_ctx):
    from agency._schema_coverage import audit_schemas
    return audit_schemas(
        dormant_audit_ctx["root"],
        ontology_labels=dormant_audit_ctx["ontology"],
        engine_loaded_titles=dormant_audit_ctx["engine_loaded"],
    )


@then("\"Dormant\" is in dormant_schemas and not in covered")
def _dormant_in_dormant_not_covered(dormant_report):
    assert "Dormant" in dormant_report.dormant_schemas, (
        "expected 'Dormant' in dormant_schemas")
    assert "Dormant" not in dormant_report.covered, (
        "expected 'Dormant' NOT in covered (it is file-backed but engine-undeclared)")


@when("I run the live schema audit with engine-load intersection",
      target_fixture="live_dormant_report")
def _run_live_dormant_audit():
    from agency.engine import Engine
    from agency._schema_coverage import (audit_schemas, truly_inline_schemas,
                                         engine_loaded_schema_titles)
    repo = Path(__file__).parent.parent.parent
    e = Engine(":memory:")
    try:
        ontology = set(e.ontology.nodes)
        merged = dict(e.ontology.schemas)
        engine_loaded = engine_loaded_schema_titles(merged)
    finally:
        e.memory.close()
    inline = truly_inline_schemas(repo / "agency", merged)
    return audit_schemas(repo / "agency", ontology_labels=ontology,
                         ontology_schemas=inline,
                         engine_loaded_titles=engine_loaded)


@then("there are no dormant schemas")
def _no_dormant_schemas(live_dormant_report):
    assert live_dormant_report.dormant_schemas == set(), (
        "these schema files match an ontology label but are NOT declared "
        "by their capability (add `artefact_schemas` to the owning cap):\n"
        + "\n".join(f"  {l}" for l in sorted(live_dormant_report.dormant_schemas)))


# ── Slice 6: discover-prompt wave ────────────────────────────────────────────
# FeasibilitySignal + IntentRefinement (discover cap; already has artefact_schemas)
# Template (document cap; already has artefact_schemas)
# PromptFramework (prompt cap; artefact_schemas added this wave)
DISCOVER_PROMPT_LABELS = {"FeasibilitySignal", "IntentRefinement", "Template", "PromptFramework"}


@then("the discover-prompt labels are all schema-covered")
def _discover_prompt_covered(coverage_report):
    missing = DISCOVER_PROMPT_LABELS - coverage_report.covered
    assert not missing, (
        "discover-prompt labels lack a Schema (Spec 153 Slice 6 — discover-prompt wave):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@then("the discover-prompt labels each have a loaded ontology schema")
def _discover_prompt_loaded(loaded_schema_titles):
    missing = DISCOVER_PROMPT_LABELS - loaded_schema_titles
    assert not missing, (
        "discover-prompt schemas are on disk but NOT loaded by the engine "
        "(declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


# ── Slice 6: prompt-dossier + document + jules wave ──────────────────────────
# BriefAudit/CatalogModule/ResearchIntent/AntiPattern (prompt cap)
# DocRevision (document cap) + JulesAlias (jules cap)
# All owning caps already have artefact_schemas declared.
PROMPT_DOSSIER_DOC_JULES_LABELS = {
    "BriefAudit", "CatalogModule", "ResearchIntent", "AntiPattern",
    "DocRevision", "JulesAlias",
}


@then("the prompt-dossier-document-jules labels are all schema-covered")
def _prompt_dossier_doc_jules_covered(coverage_report):
    missing = PROMPT_DOSSIER_DOC_JULES_LABELS - coverage_report.covered
    assert not missing, (
        "prompt-dossier+document+jules labels lack a Schema "
        "(Spec 153 Slice 6 — prompt-dossier+doc+jules wave):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@then("the prompt-dossier-document-jules labels each have a loaded ontology schema")
def _prompt_dossier_doc_jules_loaded(loaded_schema_titles):
    missing = PROMPT_DOSSIER_DOC_JULES_LABELS - loaded_schema_titles
    assert not missing, (
        "prompt-dossier+document+jules schemas are on disk but NOT loaded by "
        "the engine (declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


# ── analyze + select wave ─────────────────────────────────────────────────────
# Analysis/Finding (analyze cap) + Selection (select cap)
ANALYZE_SELECT_LABELS = {"Analysis", "Finding", "Selection"}


@then("the analyze-select labels are all schema-covered")
def _analyze_select_covered(coverage_report):
    missing = ANALYZE_SELECT_LABELS - coverage_report.covered
    assert not missing, (
        "analyze+select labels lack a Schema "
        "(Spec 153 Slice 6 — analyze+select wave):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@then("the analyze-select labels each have a loaded ontology schema")
def _analyze_select_loaded(loaded_schema_titles):
    missing = ANALYZE_SELECT_LABELS - loaded_schema_titles
    assert not missing, (
        "analyze+select schemas are on disk but NOT loaded by "
        "the engine (declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


# ── research + develop-extras wave ───────────────────────────────────────────
# Research/ResearchClaim (research cap) + Plan/PlanStep/ModeShift/SessionLifecycle (develop cap)
# Both caps already declare artefact_schemas — only schemas needed.
RESEARCH_DEVELOP_EXTRAS_LABELS = {
    "Research", "ResearchClaim",
    "Plan", "PlanStep", "ModeShift", "SessionLifecycle",
}


@then("the research-develop-extras labels are all schema-covered")
def _research_develop_extras_covered(coverage_report):
    missing = RESEARCH_DEVELOP_EXTRAS_LABELS - coverage_report.covered
    assert not missing, (
        "research+develop-extras labels lack a Schema "
        "(Spec 153 Slice 6 — research+develop-extras wave):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))


@then("the research-develop-extras labels each have a loaded ontology schema")
def _research_develop_extras_loaded(loaded_schema_titles):
    missing = RESEARCH_DEVELOP_EXTRAS_LABELS - loaded_schema_titles
    assert not missing, (
        "research+develop-extras schemas are on disk but NOT loaded by "
        "the engine (declare `artefact_schemas` on the owning capability):\n"
        + "\n".join(f"  {l}" for l in sorted(missing)))
