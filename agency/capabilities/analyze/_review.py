"""Shared review core (Spec 380): scope-detect · merge · Iron Law gate · classify.

This module is the single engine both develop.review (interactive) and
analyze.review (headless/CI) drive. The actors differ in pause behaviour, not
logic — pure functions here, no graph writes.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._findings import Finding

REVIEW_CHAIN_PATH = Path(__file__).parent / "data" / "review-chain.json"


def scope_detect(scope: str = "") -> str:
    """Return the effective scope description (auto-detect from git state if empty)."""
    if scope:
        return scope
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=2, check=False)
        if r.stdout.strip():
            return "staged changes"
        r2 = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, timeout=2, check=False)
        if r2.stdout.strip():
            return "working tree changes"
        r3 = subprocess.run(
            ["git", "diff", "main...HEAD", "--name-only"],
            capture_output=True, text=True, timeout=2, check=False)
        if r3.stdout.strip():
            return "branch changes vs main"
    except Exception:
        pass
    return "whole repo"


def merge_findings(
    decidable: list["Finding"],
    judgment: list["Finding"],
) -> list["Finding"]:
    """Merge decidable + judgment — one Finding per (risk_code, file, line).

    Judgment enriches an existing decidable finding in place (consequence/remedy/
    sharper source); it creates a new Finding only where no decidable finding
    covers that (risk_code, span). Pure function; no graph writes (Hohpe fix).
    """
    out = list(decidable)
    index: dict[tuple, int] = {}
    for i, f in enumerate(out):
        if f.risk_code:
            index[(f.risk_code, f.file, f.line)] = i

    for jf in judgment:
        if jf.risk_code:
            key = (jf.risk_code, jf.file, jf.line)
            if key in index:
                i = index[key]
                existing = out[i]
                out[i] = replace(
                    existing,
                    consequence=jf.consequence or existing.consequence,
                    remedy=jf.remedy or existing.remedy,
                    source=jf.source or existing.source,
                )
            else:
                out.append(jf)
                index[key] = len(out) - 1
        else:
            out.append(jf)
    return out


def iron_law_passed(findings: list["Finding"]) -> bool:
    """Pure predicate: every brooks finding (non-empty risk_code) must carry
    both consequence AND remedy. This is the Iron Law gate — a decidable check
    over Finding fields, not agent self-assertion (Wiegers fix, Spec 380 §2).
    """
    return all(f.consequence and f.remedy for f in findings if f.risk_code)


def classify_remedy(finding: "Finding") -> str:
    """Classify a Finding's remedy as 'safe' (mechanical+local) or 'risky' (structural).

    Safe = can auto-apply; risky = structural change that needs human confirmation.
    """
    risky_keywords = [
        "invert", "move class", "move module", "restructure",
        "reorder", "split module", "decompose", "dependency direction",
        "invert dependency",
    ]
    remedy_lower = (getattr(finding, "remedy", "") or "").lower()
    for kw in risky_keywords:
        if kw in remedy_lower:
            return "risky"
    return "safe"


def quality_gate(score: int, critical: int,
                 min_score: int = 70, max_critical: int = 0) -> tuple[bool, str]:
    """The quality-gate decision (Spec 382 §2): PASSED iff ``score >= min_score``
    AND ``critical <= max_critical``. ``min_score`` / ``max_critical`` are
    documented tunable budgets (CLAUDE.md #8 — brooks-lint defaults), not magic
    snapshots. Returns ``(passed, evidence)`` — the evidence string is the
    auditable rationale recorded on the Gate node."""
    passed = score >= min_score and critical <= max_critical
    evidence = (f"score {score} (min {min_score}); "
                f"{critical} critical (max {max_critical})")
    return passed, evidence


# ── the judgment pass (Spec 380 §judgment — the reasoning half) ───────────────
# The decidable scanners catch the mechanical risks; the JUDGMENT pass produces
# the reasoning-heavy ones (R2/R3/R6/T1–T6) by asking an LLM to reason over the
# code against each risk's principle + its "what NOT to flag" guard. It routes
# through the Spec 352/279 `complete_or_delegate` seam (OpenRouter free-first →
# driver → MCP host-sampling → host-delegate), so no API key is required — inside
# Claude Code the host runs inference and resumes via `host_completion`. Plain
# text (`output_schema=None`) keeps a free OpenRouter model eligible.

_JUDGMENT_SYSTEM = (
    "You are a senior software reviewer applying the brooks-lint Iron Law: every "
    "finding is Symptom -> Source -> Consequence -> Remedy. Judge ONLY the "
    "reasoning-heavy risks listed (the mechanical ones are already caught). Cite a "
    "book ONLY when the symptom matches its principle; a threshold crossing is a "
    "hint, not a verdict; honor each risk's 'do NOT flag' guard. Reply with ONLY a "
    "JSON array of objects {risk_code,file,line,message,source,consequence,remedy}; "
    "reply [] when nothing genuinely applies."
)


def judgment_risks(risks: dict) -> dict:
    """The judgment-only subset of the registry — risks with NO ``decidable``
    rule-id mapping (the reasoning-heavy ones a scanner cannot decide). DERIVED
    from the data (rule 8), the complement of ``_decay._decidable_index``."""
    return {c: e for c, e in risks.items() if not e.get("decidable")}


# AGENCY-DRIFT: review-chain — the vendored, mode-aware Brooks review chain (the
# ordered review methodology the judgment subagent walks). Its step risk-codes MUST
# stay a subset of decay-risks.json and its _source MUST track the pinned upstream
# rev — both enforced by the "review-chain grounding" gate in scripts/check-drift.
def load_review_chain() -> dict:
    """The vendored, mode-aware Brooks review chain ``{mode: {title, purpose,
    steps:[…]}}`` PLUS the shared ``_methodology`` block. Returns the FULL dict
    (the ``_``-prefixed metadata stays — ``_methodology`` is read by the prompt
    builder; mode entries are the non-``_`` keys). Single source (rule 2); the per-
    risk prose is NOT here — it derives from decay-risks.json at build time."""
    return json.loads(REVIEW_CHAIN_PATH.read_text(encoding="utf-8"))


def _risk_detail(code: str, j_risks: dict) -> str:
    """One judgment-risk's diagnostic + symptoms + 'do NOT flag' guard + cites,
    DERIVED from decay-risks.json (rule 2). A code NOT in ``j_risks`` is decidable —
    already caught mechanically — so it's marked context-only (don't re-flag)."""
    e = j_risks.get(code)
    if e is None:
        return (f"    [{code}] already caught mechanically — context only, "
                f"do NOT emit a finding for it")
    cites = "; ".join(f"{s.get('book', '')} — {s.get('principle', '')}"
                      for s in e.get("sources", []))
    return (f"    [{code}] {e.get('name', '')}: {e.get('diagnostic', '')}\n"
            f"        symptoms: {', '.join(e.get('symptoms', []))}\n"
            f"        do NOT flag: {'; '.join(e.get('what_not_to_flag', []))}\n"
            f"        cite: {cites}")


def build_judgment_prompt(code_units: list[tuple[str, str]], j_risks: dict, *,
                          mode: str = "review",
                          chain: dict | None = None) -> tuple[list[dict], str]:
    """Pure — build ``(messages, system)`` for the judgment pass, driving the
    subagent with the mode's BROOKS REVIEW CHAIN (Spec 380 §judgment) rather than a
    flat risk-dump. ``code_units`` is a list of ``(path, source)``; ``j_risks`` the
    judgment-only registry subset; ``mode`` selects the chain. The prompt carries
    the shared methodology (Iron Law, severity, scope calibration, fix order,
    restraint) + the mode's ORDERED steps, each step naming its risks; per-risk
    detail derives from ``j_risks`` (decay-risks.json). Decidable risks are shown as
    CONTEXT-ONLY — the subagent emits findings only for the judgment-only codes."""
    if chain is None:
        chain = load_review_chain()
    methodology = chain.get("_methodology", {})
    mode_chain = chain.get(mode) or chain.get("review") or {}

    meth_lines = [f"- {methodology[k]}" for k in
                  ("iron_law", "severity", "scope_calibration", "fix_order", "restraint")
                  if methodology.get(k)]

    step_blocks = []
    for i, step in enumerate(mode_chain.get("steps", []), start=1):
        head = f"{i}. {step.get('name', '')} — {step.get('intent', '')}"
        detail = [_risk_detail(code, j_risks) for code in step.get("risks", [])]
        step_blocks.append(head + ("\n" + "\n".join(detail) if detail else ""))

    code_blocks = "\n\n".join(f"### {p}\n```\n{src}\n```" for p, src in code_units)
    judgment_only = ", ".join(sorted(j_risks))
    user = (
        f"# {mode_chain.get('title', mode)} — Brooks review chain\n"
        f"{mode_chain.get('purpose', '')}\n\n"
        f"## Methodology\n" + "\n".join(meth_lines) + "\n\n"
        f"## Review chain — walk these steps in order\n" + "\n".join(step_blocks) + "\n\n"
        f"## Your task\n"
        f"Walk the chain over the code below. EMIT findings ONLY for the "
        f"judgment-only risks ({judgment_only}); the decidable risks are already "
        f"caught mechanically and are shown for context. Emit one JSON object per "
        f"genuine issue {{risk_code,file,line,message,source,consequence,remedy}}; "
        f"reply [] when nothing genuinely applies.\n\n"
        f"## Code\n" + code_blocks)
    return [{"role": "user", "content": user}], _JUDGMENT_SYSTEM


def _extract_json_array(text: str) -> list:
    """Tolerant JSON-array extraction (fence-strip + bracket-extract), mirroring
    ``_llm._parse`` — a model that wraps the array in prose or ```json fences
    still parses. Returns ``[]`` on anything unparseable."""
    if not text:
        return []
    s = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(s)
    except Exception:
        m = re.search(r"\[.*\]", s, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
        except Exception:
            return []
    return data if isinstance(data, list) else []


def parse_judgment(text: str, valid_codes: set) -> list["Finding"]:
    """Pure — parse the LLM's JSON-array reply into ``Finding``s. Two guards
    applied at the source: a finding whose ``risk_code`` is not a REAL registry
    code is dropped (hallucination guard), and one missing ``consequence`` or
    ``remedy`` is dropped (the Iron Law gate — Wiegers, Spec 380 §2 — enforced
    where the judgment enters, not after)."""
    from ._findings import make_finding
    out: list["Finding"] = []
    for item in _extract_json_array(text):
        if not isinstance(item, dict):
            continue
        code = str(item.get("risk_code", "")).strip()
        if code not in valid_codes:
            continue
        consequence = str(item.get("consequence", "")).strip()
        remedy = str(item.get("remedy", "")).strip()
        if not (consequence and remedy):
            continue
        message = str(item.get("message", ""))
        try:
            line = int(item.get("line", 1) or 1)
        except (TypeError, ValueError):
            line = 1
        out.append(make_finding(
            rule=code, severity="warn", file=str(item.get("file", "")),
            line=line, message=message, evidence=message,
            risk_code=code, source=str(item.get("source", "")),
            consequence=consequence, remedy=remedy))
    return out


def judgment(code_units: list[tuple[str, str]], risks: dict, *,
             mode: str = "review",
             driver=None, host=None, llm=None, host_completion: dict | None = None,
             require: str | None = None,
             model_hint: str | None = None) -> tuple[list["Finding"], dict | None]:
    """Run the LLM judgment pass over ``code_units``. Returns
    ``(findings, delegate)`` — ``delegate`` is ``None`` when findings were
    produced (or none applied), or the ``llm_delegate`` envelope dict when the
    host must run inference (Spec 279). The decidable pass has already run, so
    judgment is purely ADDITIVE: any failure degrades to ``([], None)`` and the
    decidable findings still stand (Hightower CI-degradation path).

    ``model_hint`` tags the delegate envelope with how the host should fulfil it
    (e.g. ``"subagent"`` — dispatch a Claude subagent, no external LLM; ``"jules"``
    — a remote agent). The host reads the hint off the returned envelope."""
    from agency._host_llm import complete_or_delegate, HostLLMRequest
    j_risks = judgment_risks(risks)
    if not j_risks or not code_units:
        return [], None
    messages, system = build_judgment_prompt(code_units, j_risks, mode=mode)
    if driver is None:                                   # resume/host paths ignore it
        class _NoDriver:
            def backend(self) -> str:
                return "none"
        driver = _NoDriver()
    try:
        result = complete_or_delegate(
            driver, messages=messages, system=system, output_schema=None,
            host_completion=host_completion, host=host, llm=llm,
            use_case="code", require=require, model_hint=model_hint)
    except Exception:
        return [], None
    if isinstance(result, HostLLMRequest):
        return [], result.to_dict()
    return parse_judgment(result.text, set(risks)), None
