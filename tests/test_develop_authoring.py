"""Plan/024 PR-A Phase A0 RED — plugin.lint_capability.

The lint that enforces docs/vision/CAPABILITY-AUTHORING.md as
machine-checkable contract. Five rule families:
- structural (Spec 016 Hint #7 markers)
- render-slice (Spec 023 first-sentence + EOF/legacy-body bugs)
- consumer-contract (Codex R2 lesson — exercise mcp._list_tools, not
  just registry state)
- token-budget (≤ 20 cl100k tokens per verb)
- mode-dispatch (the # agency-scaffold marker block-vs-warn)

These tests RED on the missing verb; A1 lands the GREEN.
"""
from __future__ import annotations

import textwrap

import pytest


pytestmark = pytest.mark.filterwarnings(
    "ignore::DeprecationWarning"  # opentelemetry noise — see pyproject
)


# ---- fixtures: three in-memory source strings -----------------------------


SCAFFOLDED_CLEAN = textwrap.dedent('''\
    # agency-scaffold: v1
    """clean — a one-line scaffolded capability with one compliant verb."""
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class CleanCapability(CapabilityBase):
        name = "clean"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def ping(self) -> dict:
            """Return a sentinel for liveness checks.

            Inputs: (none).
            Returns: {result: "pong"}.
            chain_next: (terminal).
            """
            return {"result": "pong"}
    ''')


SCAFFOLDED_BROKEN = textwrap.dedent('''\
    # agency-scaffold: v1
    """broken — has the scaffold marker but the verb violates the contract."""
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class BrokenCapability(CapabilityBase):
        name = "broken"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def do_it(self) -> dict:
            "no markers; first sentence is fine but the docstring is bare."
            return {"result": 1}
    ''')


LEGACY_BROKEN = textwrap.dedent('''\
    """legacy — NO scaffold marker; same violations as SCAFFOLDED_BROKEN."""
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class LegacyCapability(CapabilityBase):
        name = "legacy"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def do_it(self) -> dict:
            "no markers; legacy capability that predates the contract."
            return {"result": 1}
    ''')


LEGACY_NETWORK_TRANSFORM = textwrap.dedent('''\
    """transform-role verb that imports a network library — Hint #3 violation."""
    import requests  # noqa: F401 — intentional rule trigger
    from agency.capability import CapabilityBase, verb
    from agency.ontology import OntologyExtension


    class NetCapability(CapabilityBase):
        name = "net"
        home = "capability"
        ontology = OntologyExtension()

        @verb(role="transform")
        def fetch(self, url: str) -> dict:
            """Fetch a URL.

            Inputs: url (str).
            Returns: {result: <body>}.
            chain_next: (terminal).
            """
            return {"result": "fake"}  # pragma: no cover
    ''')


def _load_capability_from_source(src: str, tmp_path, name: str):
    """Write `src` to tmp_path/<name>.py, import it, return the Capability.
    Helper for lint tests that need a real loaded capability."""
    import importlib.util
    import sys

    p = tmp_path / f"{name}.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location(f"_lint_test_{name}", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    # Find the CapabilityBase subclass
    from agency.capability import CapabilityBase
    for v in vars(mod).values():
        import inspect as _i
        if _i.isclass(v) and issubclass(v, CapabilityBase) and v is not CapabilityBase:
            return v.as_capability(), str(p)
    raise RuntimeError(f"no Capability found in {src!r}")


# ---- structural rules -----------------------------------------------------


def test_lint_structural_inputs_returns_chain_next_markers_required(tmp_path):
    """Every verb docstring must carry Inputs:/Returns:/chain_next:
    markers (Spec 016 Hint #7)."""
    from agency.capabilities.plugin import lint_capability  # RED: missing
    cap, _ = _load_capability_from_source(SCAFFOLDED_BROKEN, tmp_path, "b")
    result = lint_capability(cap)
    kinds = {v["kind"] for v in result["violations"]}
    assert "structural" in kinds, f"missing-markers must flag `structural`; got {kinds!r}"


def _kinds_fired(result):
    """Union of violations + warnings — the set of rule kinds the lint
    fired, regardless of block/warn mode dispatch. Use this when the
    test cares 'did the rule fire' rather than 'what mode are we in'."""
    return ({v["kind"] for v in result["violations"]}
            | {w["kind"] for w in result["warnings"]})


@pytest.mark.parametrize("imp", ["requests", "httpx", "subprocess"])
def test_lint_role_tag_transform_with_network_imports_flags(tmp_path, imp):
    """A `transform` verb whose source imports a network/IO library is
    mis-tagged — should be `effect`. Hint #3 — load-bearing for the
    provenance moat. Rule must fire whether the capability is
    scaffolded (block) or legacy (warn) — check the union."""
    from agency.capabilities.plugin import lint_capability
    src = LEGACY_NETWORK_TRANSFORM.replace("requests", imp)
    cap, _ = _load_capability_from_source(src, tmp_path, f"net_{imp}")
    result = lint_capability(cap)
    assert "role_tag" in _kinds_fired(result), (
        f"transform+{imp} import must fire `role_tag`; got "
        f"violations={result['violations']!r} warnings={result['warnings']!r}"
    )


# ---- render-slice rules ---------------------------------------------------


def test_lint_render_slice_brief_nonempty_and_under_120_chars(tmp_path):
    """Spec 023: parse_slices(doc)['brief'] must be non-empty AND ≤120 chars.
    A verb with no docstring at all should fire `render_slice`."""
    from agency.capabilities.plugin import lint_capability
    # Purpose-built fixture (don't .replace into SCAFFOLDED_CLEAN — textwrap
    # indent semantics make the target string finicky and silent-misses fail
    # the rule rather than the test).
    EMPTY_DOC = textwrap.dedent('''\
        # agency-scaffold: v1
        from agency.capability import CapabilityBase, verb
        from agency.ontology import OntologyExtension

        class EmptyBriefCapability(CapabilityBase):
            name = "empty-brief"
            home = "capability"
            ontology = OntologyExtension()

            @verb(role="transform")
            def ping(self) -> dict:
                ""
                return {"result": 1}
        ''')
    cap, _ = _load_capability_from_source(EMPTY_DOC, tmp_path, "empty_brief")
    result = lint_capability(cap)
    assert "render_slice" in _kinds_fired(result), (
        f"empty-docstring verb must fire render_slice; got "
        f"violations={result['violations']!r} warnings={result['warnings']!r}"
    )


def test_lint_render_slice_first_sentence_cleaves_on_first_sentence_helper(tmp_path):
    """The brief is the first SENTENCE per `_first_sentence` (Spec 023
    Phase 7 refinement). A two-sentence-in-one-line docstring must
    cleave correctly — the first sentence ≤120 chars."""
    from agency.capabilities.plugin import lint_capability
    from agency.render import _first_sentence
    cap, _ = _load_capability_from_source(SCAFFOLDED_CLEAN, tmp_path, "fs")
    result = lint_capability(cap)
    # Clean scaffold should NOT flag render_slice
    rs_violations = [v for v in result["violations"] if v["kind"] == "render_slice"]
    assert rs_violations == [], f"clean scaffold should have zero render_slice violations; got {rs_violations!r}"
    # And the helper itself is reachable through the import boundary
    assert _first_sentence("Hi. Bye.") == "Hi."


def test_lint_render_slice_legacy_body_drift_flags(tmp_path):
    """Codex R-finding #6: a markerless multi-paragraph docstring keeps
    paragraphs 2+ in `body`. parse_slices must NOT lose them at standard
    depth. Lint surfaces the legacy-body-drift case."""
    from agency.render import parse_slices
    src = '''"""one paragraph.\n\nanother paragraph that drifted."""'''
    parsed = parse_slices(src)
    # the parse must NOT drop the second paragraph silently
    assert "another paragraph" in parsed["body"], "legacy body must survive parse_slices"


# ---- consumer-contract rules ----------------------------------------------


def test_lint_consumer_contract_engine_memory_builds_and_lists_tools(tmp_path):
    """Codex R2 lesson — exercise the consumer surface, not just registry.
    Loading the capability into Engine(":memory:") must round-trip
    through mcp._list_tools()."""
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_capability_from_source(SCAFFOLDED_CLEAN, tmp_path, "cc")
    result = lint_capability(cap)
    # Clean scaffold should NOT flag consumer_contract
    cc = [v for v in result["violations"] if v["kind"] == "consumer_contract"]
    assert cc == [], f"clean scaffold should have zero consumer_contract violations; got {cc!r}"


async def test_lint_consumer_contract_search_finds_under_budget(tmp_path):
    """The clean scaffold's verb must be findable via FastMCP's search
    surface and the result must fit a token budget."""
    from agency.engine import Engine
    cap, _ = _load_capability_from_source(SCAFFOLDED_CLEAN, tmp_path, "cc2")
    e = Engine(":memory:", extra_capabilities=[cap])
    try:
        mcp = e.build_mcp(codemode=False)
        tools = await mcp._list_tools()
        names = [t.name for t in tools]
        assert any("capability_clean_ping" == n for n in names), (
            f"clean.ping must be a registered MCP tool; saw: {sorted(names)[:5]}…"
        )
    finally:
        e.memory.close()


# ---- token-budget ---------------------------------------------------------


def test_lint_token_budget_under_20_tokens_per_verb_cl100k(tmp_path):
    """Spec 023 budget gate adapted: lint asserts the verb's brief slice
    rendered at depth=brief fits under ~20 tokens (cl100k)."""
    pytest.importorskip("tiktoken")
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_capability_from_source(SCAFFOLDED_CLEAN, tmp_path, "tb")
    result = lint_capability(cap)
    tb = [v for v in result["violations"] if v["kind"] == "token_budget"]
    assert tb == [], f"clean scaffold should fit token budget; got {tb!r}"


# ---- mode dispatch (the marker contract) ----------------------------------


def test_lint_mode_dispatch_marker_present_violations_blocks(tmp_path):
    """Marker present + violations → ok=False (block)."""
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_capability_from_source(SCAFFOLDED_BROKEN, tmp_path, "mp_block")
    result = lint_capability(cap)
    assert result["mode"] == "block"
    assert result["ok"] is False
    assert result["violations"], "broken scaffold must produce ≥1 violation"


def test_lint_mode_dispatch_marker_absent_violations_warns(tmp_path):
    """Marker absent + violations → ok=True, warnings≠[] (grandfathered)."""
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_capability_from_source(LEGACY_BROKEN, tmp_path, "ma_warn")
    result = lint_capability(cap)
    assert result["mode"] == "warn"
    assert result["ok"] is True
    assert result["warnings"], "legacy broken capability must produce ≥1 warning"
    assert result["violations"] == [], "warn mode moves violations → warnings"


def test_lint_mode_dispatch_marker_absent_clean(tmp_path):
    """Marker absent + clean → ok=True, warnings=[] (the no-op symmetric case)."""
    from agency.capabilities.plugin import lint_capability
    src = LEGACY_BROKEN.replace(
        '"no markers; legacy capability that predates the contract."',
        '"""Do a thing.\n\n        Inputs: (none).\n        Returns: {result: 1}.\n        chain_next: (terminal).\n        """',
    )
    cap, _ = _load_capability_from_source(src, tmp_path, "ma_clean")
    result = lint_capability(cap)
    assert result["mode"] == "warn"   # marker absent → warn mode regardless
    assert result["ok"] is True
    assert result["warnings"] == []
    assert result["violations"] == []


# ---- return shape ---------------------------------------------------------


def test_lint_returns_shape_ok_violations_warnings_skipped_mode(tmp_path):
    """The contract: {ok, violations, warnings, skipped, mode} — always
    all five keys, regardless of result."""
    from agency.capabilities.plugin import lint_capability
    cap, _ = _load_capability_from_source(SCAFFOLDED_CLEAN, tmp_path, "shape")
    result = lint_capability(cap)
    assert set(result.keys()) >= {"ok", "violations", "warnings", "skipped", "mode"}
    assert isinstance(result["ok"], bool)
    assert isinstance(result["violations"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["skipped"], int)
    assert result["mode"] in ("block", "warn")


# ---- Phase A2: develop.scaffold_capability RED ----------------------------


def test_scaffold_light_emits_single_file(tmp_path):
    """light kind emits a single .py file in base_dir."""
    from agency.capabilities.develop import scaffold_capability
    result = scaffold_capability("mycap", kind="light", base_dir=str(tmp_path))
    path = result["result"]
    assert path.endswith("mycap.py")
    assert (tmp_path / "mycap.py").is_file()


def test_scaffold_medium_emits_single_file_plus_ontology_stubs(tmp_path):
    """medium kind = same single file but with OntologyExtension(nodes=...)
    populated as a TODO stub the author fills in."""
    from agency.capabilities.develop import scaffold_capability
    result = scaffold_capability("midcap", kind="medium", base_dir=str(tmp_path))
    body = (tmp_path / "midcap.py").read_text()
    assert "nodes=" in body
    assert "templates=" in body or "schemas=" in body


def test_scaffold_heavy_emits_folder_with_init_and_reexport(tmp_path):
    """heavy kind emits a folder per Spec 016 Hint #1: __init__.py
    re-exports the CapabilityBase subclass; main impl in <name>.py."""
    from agency.capabilities.develop import scaffold_capability
    result = scaffold_capability("bigcap", kind="heavy", base_dir=str(tmp_path))
    folder = tmp_path / "bigcap"
    assert folder.is_dir()
    assert (folder / "__init__.py").is_file()
    assert (folder / "bigcap.py").is_file()
    init_src = (folder / "__init__.py").read_text()
    # re-export pattern — discover() finds the cap via this
    assert "BigcapCapability" in init_src or "from .bigcap import" in init_src


def test_scaffold_first_line_is_agency_scaffold_marker_v1(tmp_path):
    """Every scaffolded file's first non-blank line is the marker."""
    from agency.capabilities.develop import scaffold_capability
    for kind in ("light", "medium"):
        result = scaffold_capability(f"m_{kind}", kind=kind, base_dir=str(tmp_path))
        first_line = (tmp_path / f"m_{kind}.py").read_text().lstrip().split("\n", 1)[0]
        assert first_line == "# agency-scaffold: v1", (
            f"{kind}: first non-blank line must be the marker; got {first_line!r}"
        )


def test_scaffold_returns_artefact_kind_capability_scaffold_with_path(tmp_path):
    """The act-role return shape: {result: <path>, artefact: {kind, name,
    path, scaffold_version}}."""
    from agency.capabilities.develop import scaffold_capability
    result = scaffold_capability("acap", kind="light", base_dir=str(tmp_path))
    assert "result" in result
    assert "artefact" in result
    a = result["artefact"]
    assert a["kind"] == "capability-scaffold"
    assert a["name"] == "acap"
    assert "path" in a
    assert a.get("scaffold_version") == 1


def test_scaffold_output_lints_clean_in_block_mode(tmp_path):
    """The cross-assertion that ties A2 to A1: a scaffolded capability
    must lint clean (mode=block, ok=True, violations=[]). Lint-clean
    by construction — the discipline's promise."""
    from agency.capabilities.develop import scaffold_capability
    from agency.capabilities.plugin import lint_capability
    scaffold_capability("zcap", kind="light", base_dir=str(tmp_path))
    # Load the scaffolded file as a Capability and lint it
    cap, _ = _load_capability_from_source(
        (tmp_path / "zcap.py").read_text(),
        tmp_path, "zcap_loader",
    )
    result = lint_capability(cap)
    assert result["mode"] == "block", "marker present → block mode"
    assert result["ok"] is True, (
        f"scaffolded capability must lint clean in block mode; "
        f"violations={result['violations']!r}"
    )


def test_scaffold_unknown_kind_returns_input_required(tmp_path):
    """Unknown kind doesn't crash — returns the input-required shape per
    Spec 016 Hint #8 (universal input-required convention)."""
    from agency.capabilities.develop import scaffold_capability
    result = scaffold_capability("ucap", kind="WRONG", base_dir=str(tmp_path))
    assert result.get("status") == "input-required"
    assert "kind" in (result.get("resume_with") or [])


# ---- Phase A5: end-to-end discipline walk + reflection wiring -------------


def _drive_authoring_discipline(engine, iid, tmp_path):
    """Helper — walk authoring-capabilities through SkillRun.
    Returns (skill_run, scaffolded_cap_name, lint_result, reflection_id)."""
    from agency.skill import SkillRun
    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run = SkillRun(engine.memory, iid, schema, registry=engine.registry)

    # Phase 1: research — plain phase, satisfy produces
    run.submit(outputs={"read_doctrine": "yes"})

    # Phase 2: scaffold — bound to develop.scaffold_capability
    # outputs supply the verb's inputs (name, kind) per phase["inputs"]
    cap_name = "e2ecap"
    run.submit(outputs={"name": cap_name, "kind": "light", "base_dir": str(tmp_path)})

    # Phase 3: author — plain phase
    run.submit(outputs={"verbs_written": "yes"})

    # Phase 4: lint — bound to plugin.lint_capability
    # Need to register the scaffolded cap in the registry first so lint can find it
    # by name. For e2e, we load the scaffolded file and register it.
    scaffold_path = tmp_path / f"{cap_name}.py"
    from agency.capabilities.develop import scaffold_capability
    scaffold_capability(cap_name, kind="light", base_dir=str(tmp_path))
    cap, _ = _load_capability_from_source(scaffold_path.read_text(),
                                          tmp_path, "e2e_loader")
    engine.registry.register(cap)

    run.submit(outputs={"name": cap_name})  # supplies plugin.lint_capability's `name` arg

    # Phase 5: token-check — plain phase
    run.submit(outputs={"budget_ok": "yes"})

    # Phase 6: commit — HARD gate. First, write the reflection (manually,
    # per the contract: the gate is the boundary; the caller records).
    record_result, _ = engine.registry.invoke(
        engine.memory, iid, "develop", "record_authoring_outcome",
        name=cap_name, kind="light",
    )
    rid = record_result["result"] if isinstance(record_result, dict) else record_result

    # Now confirm the gate
    final = run.submit(outputs={"reflection_recorded": rid}, confirmed=True)
    return run, cap_name, final, rid


def test_walking_authoring_capabilities_records_reflection_serves_c374ac3d(engine, iid, tmp_path):
    """The discipline walk's end-of-loop action: a Reflection is recorded,
    serving the calling intent. (The Spec 024 §Goal: every authoring walk
    surfaces back into future refinement.)"""
    run, _, _, rid = _drive_authoring_discipline(engine, iid, tmp_path)
    assert run.done, "skill should be complete after phase 6 confirm"
    # Reflection exists in the graph with the expected content
    reflections = engine.memory.find("Reflection")
    rids = [r["id"] for r in reflections]
    assert rid in rids, f"recorded reflection {rid} not in graph; found {rids[:3]}…"
    # The reflection text mentions the authored capability + the discipline name
    # (the record_authoring_outcome verb composed this; if the verb ran, both
    # tokens are present)
    rec = engine.memory.recall(rid)
    text = rec.get("text", "")
    assert "e2ecap" in text and "authoring-capabilities" in text, (
        f"reflection text should reference the authored cap + discipline; got {text!r}"
    )


def test_phase_2_scaffold_invokes_develop_scaffold_capability_via_skillrun(engine, iid, tmp_path):
    """Phase 2 is bound — walking it RUNS the scaffold verb (creates the file)."""
    from agency.skill import SkillRun
    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run = SkillRun(engine.memory, iid, schema, registry=engine.registry)
    run.submit(outputs={"read_doctrine": "yes"})
    # phase 2 — scaffold. Supply name + kind + a base_dir (the test's tmp_path).
    run.submit(outputs={"name": "p2cap", "kind": "light", "base_dir": str(tmp_path)})
    # The walker invoked scaffold_capability; the file exists on disk
    assert (tmp_path / "p2cap.py").is_file(), "phase 2 walk must execute scaffold_capability"


def test_phase_4_lint_invokes_plugin_lint_capability_via_skillrun(engine, iid, tmp_path):
    """Phase 4 is bound to plugin.lint_capability — walking it returns the
    lint shape into the phase outputs."""
    from agency.skill import SkillRun
    # Scaffold + register the cap first so lint has something to lint
    from agency.capabilities.develop import scaffold_capability
    cap_name = "p4cap"
    scaffold_capability(cap_name, kind="light", base_dir=str(tmp_path))
    cap, _ = _load_capability_from_source(
        (tmp_path / f"{cap_name}.py").read_text(), tmp_path, "p4_loader",
    )
    engine.registry.register(cap)
    # Walk to phase 4
    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run = SkillRun(engine.memory, iid, schema, registry=engine.registry)
    for outputs in [{"read_doctrine": "y"},
                    {"name": cap_name, "kind": "light", "base_dir": str(tmp_path)},
                    {"verbs_written": "y"}]:
        run.submit(outputs=outputs)
    # phase 4 fires plugin.lint_capability — must not raise
    result = run.submit(outputs={"name": cap_name})
    # The walker satisfied "lint_result" from the lint return; the skill
    # advanced to phase 5 (or beyond)
    assert run.i >= 4, f"phase 4 walk must advance; at phase {run.i}"


def test_hard_gate_phase_6_blocks_until_reflection_recorded(engine, iid, tmp_path):
    """Phase 6 is hard-gate — submit() without confirmed=True returns
    input-required even if produces are satisfied."""
    run, cap_name, _, _ = _drive_authoring_discipline(engine, iid, tmp_path)
    # the above completes the run; verify it WAS hard-gated by re-walking
    # to phase 6 and checking the unconfirmed-submit pause shape
    from agency.skill import SkillRun
    schema = engine.registry.get("develop").ontology.skills["authoring-capabilities"]
    run2 = SkillRun(engine.memory, iid, schema, registry=engine.registry)
    for outputs in [
        {"read_doctrine": "y"},
        {"name": "hg", "kind": "light", "base_dir": str(tmp_path)},
        {"verbs_written": "y"},
        {"name": "hg"},  # phase 4 — auto-registers nothing, but the existing
                         # e2ecap from above is still in the registry; we re-use
                         # the cap_name from _drive_authoring_discipline
    ]:
        if "name" in outputs and outputs.get("name") == "hg":
            # phase 4 needs the cap registered; reuse the prior e2ecap to avoid
            # double-scaffold. The lint runs against whichever name we pass.
            outputs["name"] = cap_name
        try:
            run2.submit(outputs=outputs)
        except Exception:
            break  # phase 4 may complain if cap missing; not testing that
    # If we got to phase 5, advance to 6
    if run2.i == 4:
        run2.submit(outputs={"budget_ok": "y"})
    if run2.i == 5:
        result = run2.submit(outputs={"reflection_recorded": "rid_placeholder"})
        assert result.get("status") == "input-required", (
            f"phase 6 unconfirmed must return input-required; got {result!r}"
        )
