"""Spec 011 — decidable gate predicates (pure module helpers, not verbs).

A predicate that blocks a phase IS a `gate` (CLUSTERS:18). These helpers classify
spec/confidence inputs into a pass/fail verdict; the CALLER records the verdict
through the existing `gate.check` verb (which writes a `Gate` and pauses the
Lifecycle on failure). No LLM, no new node label, no new capability.
"""
from __future__ import annotations

import re

# RFC-2119 normative keywords (whole-word, uppercase — the convention in specs).
_RFC2119 = (
    "MUST NOT", "MUST", "SHALL NOT", "SHALL", "SHOULD NOT", "SHOULD",
    "REQUIRED", "RECOMMENDED", "MAY", "OPTIONAL",
)
_GHERKIN_STEP = re.compile(r"^\s*(Given|When|Then|And|But)\b", re.MULTILINE)
_GHERKIN_SCENARIO = re.compile(r"^\s*Scenario\b", re.MULTILINE | re.IGNORECASE)
# Split the text at each Scenario header; a well-formed spec has at least one
# step (Given/When/Then) in the block FOLLOWING a header (not merely a stray
# step anywhere in the document, e.g. in the preamble).
_SCENARIO_SPLIT = re.compile(r"(?im)^\s*Scenario\b.*$")


def _has_scenario_with_step(text: str) -> bool:
    blocks = _SCENARIO_SPLIT.split(text)
    if len(blocks) < 2:        # no Scenario header at all
        return False
    return any(_GHERKIN_STEP.search(block) for block in blocks[1:])


def spec_validate(text: str) -> dict:
    """Classify a spec's normative + Gherkin coverage.

    Inputs: text (str — the spec body).
    Returns: ``{ok: bool, findings: [{rule, locator, msg}]}``. ``ok`` is True
             iff the text carries at least one RFC-2119 keyword AND at least one
             Gherkin scenario (Scenario: + a Given/When/Then step). Each gap is a
             finding; decidable, no LLM.
    chain_next: caller records the verdict via
                ``gate.check(name="spec-valid", passed=ok, evidence=...)`` to feed
                `develop`'s spec-panel/plan disciplines.
    """
    findings: list[dict] = []
    has_normative = any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in _RFC2119)
    if not has_normative:
        findings.append({"rule": "rfc2119", "locator": "",
                         "msg": "no RFC-2119 normative keyword (MUST/SHALL/SHOULD/MAY/…) found"})
    if not _has_scenario_with_step(text):
        findings.append({"rule": "gherkin", "locator": "",
                         "msg": "no Gherkin scenario with a step under it (Scenario: + a "
                                "Given/When/Then beneath the header) found"})
    return {"ok": not findings, "findings": findings}


def confidence_check(checklist: list[dict]) -> dict:
    """Score a pre-action confidence gate from a checklist of decidable claims.

    Inputs: checklist (list of ``{claim: str, ok: bool}``).
    Returns: ``{score: float, blocking: [claim, …]}`` — ``score`` is the fraction
             of claims marked ``ok`` (0.0 for an empty checklist: nothing
             verified ⇒ not confident); ``blocking`` lists the unmet claims.
    chain_next: ``score >= 0.9`` is the documented go-threshold (mirrors
                JULES_PROTOCOL Gate 1); caller records via
                ``gate.check(name="confidence", passed=score>=0.9, evidence=...)``.
    """
    if not checklist:
        return {"score": 0.0, "blocking": []}
    met = sum(1 for item in checklist if item.get("ok"))
    blocking = [item.get("claim", "") for item in checklist if not item.get("ok")]
    return {"score": met / len(checklist), "blocking": blocking}
