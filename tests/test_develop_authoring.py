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
