"""Acceptance — Spec 380 §judgment: the subagent walks the Brooks review chain.

The judgment subagent is driven by the vendored, mode-aware Brooks REVIEW CHAIN
(the ordered review methodology), not a flat risk-dump. The chain travels inside
the `llm_delegate` envelope's prompt, so with no inference backend the returned
envelope carries the active mode's chain. Deterministic: no network — the env is
stripped of keys and no sampling host is bound, forcing the delegate branch.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from agency._host_bridge import bind_host_context, reset_host_context
from agency.capabilities.analyze._quality import _FUNC_LOC_LIMIT
from conftest import invoke

scenarios("features/quality_chain.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


def _fixture(tmp_path) -> str:
    over = _FUNC_LOC_LIMIT + 10
    (tmp_path / "m.py").write_text(
        "def big():\n    total = 0\n" + "    total += 1\n" * over + "    return total\n")
    return str(tmp_path)


@given("a fixture file and no inference backend", target_fixture="setup")
def _fixture_no_backend(tmp_path, request, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    token = bind_host_context(None)                      # no sampling/elicit host
    request.addfinalizer(lambda: reset_host_context(token))
    return {"dir": _fixture(tmp_path)}


@when(parsers.parse('analyze.review runs in "{mode}" mode with no completion'),
      target_fixture="prompt")
def _run_review(setup, engine_iid, mode):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "review", path=setup["dir"], mode=mode)
    env = result.get("llm_delegate")
    assert env is not None and env.get("kind") == "llm_delegate", result
    parts = [env.get("system", "")] + [
        str(m.get("content", "")) for m in env.get("messages", [])]
    return "\n".join(parts)


@then(parsers.parse('the delegate prompt contains the chain title "{text}"'))
def _contains_title(prompt, text):
    assert text in prompt, prompt[:600]


@then(parsers.parse('the delegate prompt contains the chain step "{text}"'))
def _contains_step(prompt, text):
    assert text in prompt, prompt[:600]


@then(parsers.parse('the delegate prompt contains the chain methodology marker "{text}"'))
def _contains_methodology(prompt, text):
    assert text in prompt, prompt[:600]


@then(parsers.parse('the delegate prompt excludes the chain step "{text}"'))
def _excludes_step(prompt, text):
    assert text not in prompt, prompt[:600]


# ── grounding invariant (rule 8 — derive, assert subset) ─────────────────────

@then("every review-chain step code is a real decay-risk code")
def _codes_grounded():
    from agency.capabilities.analyze._review import load_review_chain
    from agency.capabilities.analyze import _decay
    chain = load_review_chain()
    valid = set(_decay.load_risks())
    chain_codes = {c for mode in chain.values() if isinstance(mode, dict)
                   for step in mode.get("steps", [])
                   for c in step.get("risks", [])}
    orphans = chain_codes - valid
    assert not orphans, f"chain references non-existent risk codes: {orphans}"


@then("every quality mode has a non-empty chain")
def _all_modes_present():
    from agency.capabilities.analyze._review import load_review_chain
    chain = load_review_chain()
    modes = {m for m in chain if not m.startswith("_")}
    expected = {"review", "audit", "debt", "test", "health", "sweep"}
    assert expected <= modes, f"missing chains: {expected - modes}"
    for m in expected:
        assert chain[m].get("steps"), f"mode {m!r} has no steps"


# ── Spec 380 — the brooks + decay-risks develop references (on-demand how-to) ──

def test_brooks_reference_resolves(engine, iid):
    r, _ = invoke(engine, iid, "develop", "reference", topic="brooks")
    doc = r["result"]["doc"]
    assert "Iron Law" in doc, doc[:200]
    assert "develop.review" in doc and "analyze.review" in doc, doc[-400:]


def test_decay_risks_reference_lists_the_live_registry(engine, iid):
    """Computed reference (rule 2): every live decay-risk code appears — derived
    from decay-risks.json, so it can't drift from what the scanners/judgment read."""
    from agency.capabilities.analyze import _decay
    r, _ = invoke(engine, iid, "develop", "reference", topic="decay-risks")
    doc = r["result"]["doc"]
    for code in _decay.load_risks():
        assert code in doc, f"{code} missing from decay-risks reference"


def test_brooks_and_decay_risks_are_discoverable(engine, iid):
    r, _ = invoke(engine, iid, "develop", "reference", topic="__nope__")
    avail = r["result"]["available"]
    assert {"brooks", "decay-risks"} <= set(avail), avail


# ── Spec 380 — first-class, selectable judgment driver ────────────────────────

def test_wet_corpus_covers_every_judgment_risk():
    """Spec 383 Slice 2b coverage invariant (keyless — runs in normal CI): the
    `-m wet` fixtures cover EXACTLY the judgment-only risk set, DERIVED from the
    registry (rule 8) — adding a judgment risk forces a paired wet fixture."""
    from agency.capabilities.analyze._review import judgment_risks
    from agency.capabilities.analyze import _decay
    from test_quality_wet import JUDGMENT_FIXTURES
    judgment_only = set(judgment_risks(_decay.load_risks()))
    covered = set(JUDGMENT_FIXTURES)
    assert covered == judgment_only, (
        f"wet corpus drift — missing: {judgment_only - covered}; "
        f"extra: {covered - judgment_only}")


def test_judgment_driver_is_selectable(engine, iid, tmp_path, monkeypatch):
    """develop.review(driver=…) tags the delegate envelope so the host fulfils it
    via the chosen backend (subagent default | jules | openrouter), one seam."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    token = bind_host_context(None)                      # no sampling/elicit host
    try:
        d = _fixture(tmp_path)
        for chosen in ("jules", "subagent"):
            r, _ = invoke(engine, iid, "develop", "review", scope=d, driver=chosen)
            env = r.get("llm_delegate")
            assert env and env.get("model_hint") == chosen, (chosen, r)
    finally:
        reset_host_context(token)
