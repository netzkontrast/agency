"""Spec 373 — Health Score (computed, preset-weighted) + leverage ranking.

Pure functions over the recorded Findings. The score is COMPUTED every run,
never a stored magic number (CLAUDE.md rule 8):

    score = max(0, 100 - Σ deduction(tier, preset))

The per-tier deductions are a documented tunable budget vendored from brooks-lint
``common.md``, kept in ``data/score-presets.json`` (a definable registry — a team
adds a preset without a code edit). "Leverage" is a defined computed quantity
(Wiegers fix, Spec 373 §1): ``deduction_weight(tier) × occurrence_count(risk_code)``
— the score points recovered by fixing it × how often that risk recurs.

Accepts either wire-shape finding dicts or ``Finding`` objects; ``tier`` is read
(Finding.tier) or derived from severity, so there is one severity source.
"""
from __future__ import annotations

import json
from pathlib import Path

SCORE_PRESETS_PATH = Path(__file__).parent / "data" / "score-presets.json"
DEFAULT_PRESET = "balanced"
BASE_SCORE = 100

# fail/warn/info → the brooks tier vocabulary (mirrors Finding.tier, Spec 354 §1).
_SEVERITY_TIER = {"fail": "critical", "warn": "warning", "info": "suggestion"}


def load_presets() -> dict[str, dict]:
    """The score-preset registry ``{preset: {tier: deduction}}`` — excludes the
    ``_``-prefixed metadata keys (``_source``/``_note``)."""
    raw = json.loads(SCORE_PRESETS_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _tier_of(finding) -> str:
    """The brooks tier of a finding — accepts a wire dict or a ``Finding``."""
    if isinstance(finding, dict):
        return finding.get("tier") or _SEVERITY_TIER.get(
            str(finding.get("severity", "")), "suggestion")
    return getattr(finding, "tier", "suggestion")


def _risk_of(finding) -> str:
    return (finding.get("risk_code", "") if isinstance(finding, dict)
            else getattr(finding, "risk_code", ""))


def weights(preset: str = DEFAULT_PRESET, presets: dict | None = None) -> dict:
    """The per-tier deduction weights for ``preset`` — falls back to balanced for
    an unknown preset (Spec 373 §2 config-validation default)."""
    presets = presets or load_presets()
    return presets.get(preset) or presets[DEFAULT_PRESET]


def score(findings, preset: str = DEFAULT_PRESET, presets: dict | None = None) -> int:
    """``max(0, 100 - Σ deduction(tier, preset))`` — floored at 0, computed live."""
    w = weights(preset, presets)
    total = sum(w.get(_tier_of(f), 0) for f in findings)
    return max(0, BASE_SCORE - total)


def leverage(finding, findings, preset: str = DEFAULT_PRESET,
             presets: dict | None = None) -> int:
    """``deduction_weight(tier) × occurrence_count(risk_code)`` — a finding with
    no risk_code counts as a single occurrence (Wiegers fix, Spec 373 §1)."""
    w = weights(preset, presets)
    weight = w.get(_tier_of(finding), 0)
    rc = _risk_of(finding)
    if not rc:
        return weight
    count = sum(1 for f in findings if _risk_of(f) == rc)
    return weight * count


def top_leverage(findings, preset: str = DEFAULT_PRESET, n: int = 3,
                 presets: dict | None = None) -> list:
    """The ``n`` highest-leverage findings, one representative per recurring
    risk_code (its leverage already folds the occurrence count), desc."""
    presets = presets or load_presets()
    seen: set = set()
    ranked: list[tuple[int, object]] = []
    for f in findings:
        rc = _risk_of(f)
        key = rc or id(f)
        if key in seen:
            continue
        seen.add(key)
        ranked.append((leverage(f, findings, preset, presets), f))
    ranked.sort(key=lambda t: t[0], reverse=True)
    return [f for _, f in ranked[:n]]
