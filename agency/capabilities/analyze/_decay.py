"""Spec 354 — decay-risk knowledge loader + decidable→risk tagger (the bridge).

The twelve decay risks (R1-R6 code, T1-T6 test) are vendored as cited data in
``data/decay-risks.json`` (from brooks-lint ``_shared/decay-risks.md`` +
``test-decay-risks.md``). This module is the single reader of that data and the
bridge from agency's *mechanical* analyze engine to brooks' *judgment* framework
(Spec 353 §3): it tags the decidable findings analyze already produces with the
risk code + Iron Law fields (Source · Consequence · Remedy) they evidence.

No risk definition is duplicated in prose-in-code (CLAUDE.md rule 2) — everything
reads from the JSON. A non-empty ``risk_code`` marks a brooks decay finding; the
empty default leaves a plain decidable finding untouched.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ._findings import Finding

DECAY_RISKS_PATH = Path(__file__).parent / "data" / "decay-risks.json"


def load_risks() -> dict[str, dict]:
    """The decay-risk registry: ``{risk_code: entry}``.

    Excludes metadata keys (those starting with ``_``, e.g. the ``_source``
    provenance marker). This is the single source for every risk definition the
    scanners + skills read (rule 2); the risk count is whatever the data
    defines, never a pinned literal (rule 8).
    """
    raw = json.loads(DECAY_RISKS_PATH.read_text(encoding="utf-8"))
    return {code: entry for code, entry in raw.items() if not code.startswith("_")}


def _decidable_index(risks: dict[str, dict]) -> dict[str, str]:
    """Reverse index ``analyze rule-id → risk_code`` built from each risk's
    ``decidable`` array. The arrays are the single source (rule 2); a rule-id
    listed under no risk is judgment-only."""
    index: dict[str, str] = {}
    for code, entry in risks.items():
        for rule_id in entry.get("decidable", ()):
            index[rule_id] = code
    return index


def tag(findings: list[Finding],
        risks: dict[str, dict] | None = None) -> list[Finding]:
    """Enrich the decidable findings analyze already produced with the risk code
    + Iron Law fields (Source · Consequence · Remedy) they evidence — the bridge
    from the mechanical engine to the judgment framework (Spec 353 §3).

    A finding whose ``rule`` appears in some risk's ``decidable`` array gets an
    enriched copy filled from the registry; every other finding passes through
    unchanged (``risk_code`` stays ``""`` — a plain decidable finding).

    ``risks`` defaults to the vendored registry (``load_risks()``). The registry
    is an OPEN set (§4): pass a merged registry (built-ins + a project's custom
    ``Cx`` entries) to tag against it without a code edit — the seam Spec 356's
    config-driven ``custom_risks`` merge plugs into.

    This is the WRITE side of the 355 §3b merge contract: the enriched finding
    carries the join key ``(risk_code, file, line)`` so the later judgment pass
    enriches it in place rather than emitting a duplicate — one Finding per
    ``(risk_code, span)``, no double-count downstream.
    """
    if risks is None:
        risks = load_risks()
    rule_to_risk = _decidable_index(risks)
    out: list[Finding] = []
    for f in findings:
        code = rule_to_risk.get(f.rule)
        if code is None:
            out.append(f)
            continue
        entry = risks[code]
        first = entry["sources"][0]
        out.append(replace(
            f,
            risk_code=code,
            source=f"{first['book']} — {first['principle']}",
            consequence=entry["consequence"],
            remedy=entry["remedy"],
        ))
    return out
