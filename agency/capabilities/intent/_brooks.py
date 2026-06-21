"""Brooks-lint — decidable conceptual-integrity heuristics (Spec 359).

The 9th `intent` critical-thinking pass, grounded in Fred Brooks (*The Mythical
Man-Month*, *No Silver Bullet*). Pure + evidence-anchored: every finding cites
the span/section that triggered it (a finding with no evidence is never emitted,
so the lint advises on signal, not vibes — Nygard failure-mode row). Decidable
with NO API key; an LLM may sharpen wording later (barbell, like Spec 356).
"""
from __future__ import annotations

import re

# Tunable budgets (rule 8 — documented, overridable; not frozen snapshots).
_DESIGN_WHY_RATIO = 3.0      # Design >> Why ⇒ accidental-complexity smell
_SECOND_SYSTEM_MIN = 2       # ≥ this many gold-plating markers ⇒ second-system
_THIN_FAILURE = 40           # a Failure-modes section shorter than this reads as thin

# Conceptual-integrity violations — a parallel/second system or a substrate bypass
# (agency's canon: "no parallel store", one substrate).
_PARALLEL = re.compile(
    r"\b(parallel|second|separate|duplicate|another)\s+"
    r"(store|system|graph|database|db|tracking|index|registry|pipeline)\b", re.I)
_BYPASS = re.compile(r"\bbypass(?:es|ing)?\s+the\s+(substrate|graph|engine|contract)\b", re.I)
# Gold-plating / second-system markers.
_GOLDPLATE = ("nice-to-have", "nice to have", "gold-plat", "future enhancement",
              "also support", "would be nice", "for completeness", "optional extra",
              "while we're at it", "wish-list", "wishlist")
# Silver-bullet claim markers.
_SILVER = ("10x", "10×", "100x", "dramatically", "eliminates all", "solves all",
           "just works", "trivially", "zero cost", "no trade-off", "no tradeoff",
           "silver bullet")
# Irreversible-surface markers + the additive-migration escape that clears them.
_IRREVERSIBLE = re.compile(
    r"\b(wire contract|breaking change|rewrite the|remove[sd]? the [a-z_]+ edge|"
    r"drop the [a-z_]+ (enum|edge|node))\b", re.I)
_ADDITIVE = ("additive", "backward-compat", "backward compat", "backwards-compat",
             "migration", "keep-both", "keep both", "grandfather", "deprecat")

PRINCIPLES = ("conceptual-integrity", "essential-vs-accidental", "second-system",
              "no-silver-bullet", "plan-to-throw-one-away")


def _section(body: str, header: str) -> str:
    low = body.lower()
    key = "## " + header.lower()
    i = low.find(key)
    if i == -1:
        return ""
    start = i + len(key)
    nxt = low.find("## ", start)
    return body[start: nxt if nxt != -1 else len(body)].strip()


def _f(principle: str, severity: str, msg: str, evidence: str) -> dict:
    return {"principle": principle, "severity": severity, "msg": msg,
            "evidence": evidence}


def brooks_findings(body: str) -> list[dict]:
    """Score ``body`` against the five Brooks principles; return evidence-anchored
    findings (``block`` reserved for conceptual-integrity / irreversible-surface)."""
    findings: list[dict] = []
    low = body.lower()
    why, design = _section(body, "why"), _section(body, "design")
    failure = _section(body, "failure modes") or _section(body, "failure")

    m = _PARALLEL.search(body) or _BYPASS.search(body)              # 1. conceptual integrity
    if m:
        findings.append(_f("conceptual-integrity", "block",
                           "introduces a parallel/second system — fold it into the "
                           "existing core concepts instead", m.group(0)))

    if design and why and len(design) > _DESIGN_WHY_RATIO * len(why):  # 2. essential vs accidental
        findings.append(_f("essential-vs-accidental", "warn",
                           "Design dwarfs Why — check the complexity is essential to "
                           "the problem, not accidental to the mechanism",
                           f"len(Design)={len(design)} > {_DESIGN_WHY_RATIO}×len(Why)={len(why)}"))

    hits = [g for g in _GOLDPLATE if g in low]                       # 3. second-system
    if len(hits) >= _SECOND_SYSTEM_MIN:
        findings.append(_f("second-system", "warn",
                           "gold-plating smell — is every feature needed now, or the "
                           "second-system wish-list?", ", ".join(hits)))

    claims = [s for s in _SILVER if s in low]                        # 4. no silver bullet
    if claims and len(failure) < _THIN_FAILURE:
        findings.append(_f("no-silver-bullet", "warn",
                           "a large benefit claim with thin/empty Failure modes — "
                           "state the trade-off", ", ".join(claims)))

    mi = _IRREVERSIBLE.search(body)                                 # 5. plan to throw one away
    if mi and not any(a in low for a in _ADDITIVE):
        findings.append(_f("plan-to-throw-one-away", "block",
                           "touches an irreversible surface without an "
                           "additive-migration note", mi.group(0)))
    return findings
