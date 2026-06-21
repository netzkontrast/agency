"""Spec 381 — Health Score (computed, preset-weighted) + leverage ranking.

Pure functions over the recorded Findings. The score is COMPUTED every run,
never a stored magic number (CLAUDE.md rule 8):

    score = max(0, 100 - Σ deduction(tier, preset))

The per-tier deductions are a documented tunable budget vendored from brooks-lint
``common.md``, kept in ``data/score-presets.json`` (a definable registry — a team
adds a preset without a code edit). "Leverage" is a defined computed quantity
(Wiegers fix, Spec 381 §1): ``deduction_weight(tier) × occurrence_count(risk_code)``
— the score points recovered by fixing it × how often that risk recurs.

Accepts either wire-shape finding dicts or ``Finding`` objects; ``tier`` is read
(Finding.tier) or derived from severity, so there is one severity source.
"""
from __future__ import annotations

import fnmatch
import json
import time
from pathlib import Path

SCORE_PRESETS_PATH = Path(__file__).parent / "data" / "score-presets.json"
DEFAULT_PRESET = "balanced"
BASE_SCORE = 100

# fail/warn/info → the brooks tier vocabulary (mirrors Finding.tier, Spec 360 §1).
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
    an unknown preset (Spec 381 §2 config-validation default)."""
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
    no risk_code counts as a single occurrence (Wiegers fix, Spec 381 §1)."""
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


# ── Spec 381 §2 — the quality: config block (tunability + validation) ──────────

_TIER_SEVERITY = {"critical": "fail", "warning": "warn", "suggestion": "info"}


def _with_tier(finding, tier: str):
    """A copy of the finding with its tier overridden — wire dict sets ``tier``;
    a ``Finding`` maps the tier back to its canonical severity."""
    if isinstance(finding, dict):
        f = dict(finding)
        f["tier"] = tier
        return f
    from dataclasses import replace
    try:
        from ._findings import FindingSeverity
        return replace(finding, severity=FindingSeverity(_TIER_SEVERITY.get(tier, "info")))
    except Exception:
        return finding


def parse_quality_config(raw: dict | None,
                         preset_names: set | None = None) -> tuple[dict, list[str]]:
    """Validate + normalise the ``quality:`` config block (Spec 381 §2). NEVER
    fatal — surfaced as notes: ``focus`` AND ``disable`` both set → ignore both +
    note; unknown ``strictness`` → fall back balanced + note. Returns
    ``(effective_config, notes)``."""
    raw = raw or {}
    names = preset_names or set(load_presets())
    notes: list[str] = []
    disable = list(raw.get("disable") or [])
    focus = list(raw.get("focus") or [])
    if disable and focus:
        notes.append("config: 'focus' and 'disable' both set — both ignored")
        disable, focus = [], []
    strictness = raw.get("strictness") or DEFAULT_PRESET
    if strictness not in names:
        notes.append(f"config: invalid strictness {strictness!r} — using {DEFAULT_PRESET}")
        strictness = DEFAULT_PRESET
    return ({"disable": disable, "focus": focus,
             "severity": dict(raw.get("severity") or {}),
             "ignore": list(raw.get("ignore") or []),
             "strictness": strictness}, notes)


def apply_quality_config(findings, config: dict) -> list:
    """Filter findings per the config (Spec 381 §2), pure → new list:
    ``ignore`` glob excludes files, ``disable`` drops risks, ``focus`` keeps ONLY
    listed risks, ``severity`` overrides a risk's tier."""
    disable = set(config.get("disable") or [])
    focus = set(config.get("focus") or [])
    ignore = config.get("ignore") or []
    severity = config.get("severity") or {}
    out = []
    for f in findings:
        rc = _risk_of(f)
        path = (f.get("file", "") if isinstance(f, dict) else getattr(f, "file", ""))
        if any(fnmatch.fnmatch(path, g) for g in ignore):
            continue
        if rc and rc in disable:
            continue
        if focus and rc not in focus:
            continue
        if rc and rc in severity:
            f = _with_tier(f, severity[rc])
        out.append(f)
    return out


# ── Spec 381 §4 — scan-time suppression read (the score-side of triage) ─────────

def _as_epoch(v):
    """Parse a suppression ``expires`` to an epoch float; unparseable → None
    (treated as no-expiry, i.e. still active — never accidentally resurface)."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def apply_suppressions(findings, suppressions, now: float | None = None):
    """Drop findings matching a LIVE (non-expired) Suppression (risk + file glob);
    an expired suppression is ignored so its finding resurfaces (keep-both — the
    finding is never deleted, Spec 292). Pure. Returns
    ``(kept, suppressed, expired_count)``."""
    now = time.time() if now is None else now
    active: list = []
    expired = 0
    for s in suppressions:
        exp = s.get("expires")
        ep = _as_epoch(exp) if exp not in (None, "") else None
        if ep is not None and ep < now:
            expired += 1
        else:
            active.append(s)
    kept, suppressed = [], []
    for f in findings:
        rc = _risk_of(f)
        path = (f.get("file", "") if isinstance(f, dict) else getattr(f, "file", ""))
        if rc and any(s.get("risk") == rc
                      and fnmatch.fnmatch(path, s.get("glob", ""))
                      for s in active):
            suppressed.append(f)
        else:
            kept.append(f)
    return kept, suppressed, expired
