"""Acceptance — Spec 383 Slice 2: the paired decidable corpus + coverage matrix.

Grounds every DECIDABLE decay risk (R1/R4/R5 — those with a `decidable` rule-id
mapping) with a positive fixture (the symptom IS flagged with the right risk +
Iron Law) and a negative "What Not to Flag" fixture (the symptom-shaped-but-
legitimate case is NOT flagged — the load-bearing half). Fixtures are real,
compilable code generated from the LIVE thresholds (rule 8 — no frozen snapshot,
mirroring test_decay_risk), exercised through the real `develop.review` path and
asserted on the structured `Finding` (Adzic — not prose Givens).

Behaviour-only (rule 7): a verification/grounding slice over existing behaviour
(Spec 383 §"What this slice does NOT do" — no new findings/score/SARIF). The
judgment-only risks (R2/R3/R6/T1–T6) are the `-m wet` corpus (Slice 2b).
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from agency.capabilities.analyze import _decay
# Thresholds DERIVED from source (rule 8) so a retune never silently flips a
# fixture from positive to negative.
from agency.capabilities.analyze._quality import _FUNC_LOC_LIMIT, _FILE_LOC_LIMIT
from conftest import invoke

scenarios("features/quality_corpus.feature")

# The six quality modes are a documented spec constant (Spec 380 / brooks' six
# skills) — cited, asserted by behaviour (each must run a decidable scan).
_MODES = ("review", "audit", "debt", "test", "health", "sweep")


def _decidable_risks() -> set[str]:
    """The risks deterministically testable today — DERIVED from the registry
    (a risk with a non-empty `decidable` rule-id array), never a literal."""
    return {code for code, e in _decay.load_risks().items() if e.get("decidable")}


# ── the corpus: risk → (positive dir, negative dir, mode) ────────────────────
# Each builder writes real .py code generated from the live thresholds. The
# negative is the brooks "What Not to Flag" guard for that risk. `_CORPUS` is the
# corpus MANIFEST; the coverage meta-test asserts the live decidable set is a
# subset of it (a new decidable rule ⇒ this fails until a builder + Examples row
# is added — the intended drift guard).
_CORPUS = {"R1", "R4", "R5"}


def _build(risk: str, tmp_path) -> tuple[str, str, str]:
    pos = tmp_path / "pos"
    neg = tmp_path / "neg"
    pos.mkdir(parents=True)
    neg.mkdir(parents=True)
    if risk == "R1":  # Q003 — function body over the long-function limit
        over = _FUNC_LOC_LIMIT + 10
        (pos / "m.py").write_text(
            "def big():\n    total = 0\n" + "    total += 1\n" * over + "    return total\n")
        # under the limit — a normal short function: NOT a Long Method
        (neg / "m.py").write_text("def small():\n    total = 0\n    total += 1\n    return total\n")
        return str(pos), str(neg), "review"
    if risk == "R4":  # Q004 — file LOC over the long-file limit
        (pos / "m.py").write_text("x = 0\n" * (_FILE_LOC_LIMIT + 10))
        (neg / "m.py").write_text("x = 0\n" * 10)
        return str(pos), str(neg), "debt"
    if risk == "R5":  # A001/A004 — circular import / high fan-out
        for d in (pos,):
            (d / "__init__.py").write_text("")
            (d / "a.py").write_text("from . import b\nVALUE = 1\n")
            (d / "b.py").write_text("from . import a\nVALUE = 2\n")
        # acyclic, low fan-out: a→b only — a legitimate layered dependency,
        # NOT a cycle and NOT high fan-out (brooks R5 "What Not to Flag").
        (neg / "__init__.py").write_text("")
        (neg / "a.py").write_text("from . import b\nVALUE = 1\n")
        (neg / "b.py").write_text("VALUE = 2\n")
        return str(pos), str(neg), "audit"
    raise AssertionError(f"no corpus builder for decidable risk {risk!r}")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


def _findings(engine_iid, mode: str, scope: str) -> list[dict]:
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "develop", "review", mode=mode, scope=scope)
    return result["findings"]


# ── per-risk paired scenarios (Scenario Outline over R1/R4/R5) ───────────────

@when(parsers.parse('the "{risk}" decidable corpus is reviewed'),
      target_fixture="corpus")
def _review_corpus(risk, tmp_path, engine_iid):
    pos, neg, mode = _build(risk, tmp_path)
    return {
        "risk": risk,
        "positive": _findings(engine_iid, mode, pos),
        "negative": _findings(engine_iid, mode, neg),
    }


@then(parsers.parse('the positive fixture raises an "{risk}" Finding with '
                    "Source, Consequence, and Remedy"))
def _positive_flagged(corpus, risk):
    hits = [f for f in corpus["positive"] if f.get("risk_code") == risk]
    assert hits, (f"{risk}: positive fixture raised no {risk} finding; got "
                  f"{[f.get('risk_code') for f in corpus['positive']]}")
    f = hits[0]
    assert f.get("source") and f.get("consequence") and f.get("remedy"), \
        f"{risk}: Iron Law incomplete on positive finding: {f}"


@then(parsers.parse('the negative fixture raises no "{risk}" Finding'))
def _negative_clean(corpus, risk):
    hits = [f for f in corpus["negative"] if f.get("risk_code") == risk]
    assert not hits, \
        f"{risk}: the What-Not-to-Flag negative fixture was wrongly flagged: {hits}"


# ── coverage matrix (derived invariants) ─────────────────────────────────────

@then("every decidable risk is covered by a positive and a negative fixture")
def _risk_coverage(tmp_path):
    decidable = _decidable_risks()
    uncovered = decidable - _CORPUS
    assert not uncovered, \
        f"decidable risks lacking paired corpus coverage: {sorted(uncovered)}"
    # the manifest cannot lie — every declared risk must actually build both halves
    for risk in sorted(_CORPUS & decidable):
        pos, neg, _mode = _build(risk, tmp_path / risk)
        assert pos and neg


@then("each of the six modes flags the long-function symptom")
def _mode_coverage(engine_iid, tmp_path):
    over = _FUNC_LOC_LIMIT + 10
    src = tmp_path / "modes"
    src.mkdir()
    (src / "m.py").write_text(
        "def big():\n    total = 0\n" + "    total += 1\n" * over + "    return total\n")
    for mode in _MODES:
        hits = [f for f in _findings(engine_iid, mode, str(src))
                if f.get("risk_code") == "R1"]
        assert hits, f"mode {mode!r} did not run a decidable scan (no R1 finding)"
