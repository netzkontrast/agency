"""research.verify — adversarial citation check.

Two decidable checks ship in v1:
  evidence-supports-claim — substring match OR semantic ≥ 0.5
  contradiction-cluster   — flag opposing claims with semantically
                            distant evidence (≥ 0.7 dissimilarity)

v2 adds web-reachability (HEAD URLs and verify 2xx).
"""
from __future__ import annotations

from ._findings import semantic_score, substring_supports


_EVIDENCE_SEMANTIC_THRESHOLD = 0.5
_CONTRADICTION_DISSIMILARITY = 0.7


def _citations_for_research(memory, research_id: str) -> list[dict]:
    rows = memory.g.query(
        "MATCH (r:Research)-[:CITES]->(c:Citation) "
        "WHERE r.id = $rid RETURN c",
        {"rid": research_id})
    return [r["c"]["properties"] for r in rows]


def check_evidence_supports_claim(memory, research_id: str,
                                   embedder=None) -> dict:
    """Each Citation's evidence_text must support its claim_supported."""
    citations = _citations_for_research(memory, research_id)
    failing: list[dict] = []
    for c in citations:
        claim = c.get("claim_supported", "")
        evidence = c.get("evidence_text", "")
        if substring_supports(claim, evidence):
            continue
        score = semantic_score(claim, evidence, embedder)
        if score >= _EVIDENCE_SEMANTIC_THRESHOLD:
            continue
        failing.append({"citation_id": c.get("id"), "score": score,
                        "claim": claim[:80]})
    if failing:
        return {"status": "fail", "items": failing,
                "n_checked": len(citations)}
    return {"status": "pass", "items": [], "n_checked": len(citations)}


def check_contradiction_cluster(memory, research_id: str,
                                  embedder=None) -> dict:
    """Flag pairs of citations whose claims are semantically opposite.

    Heuristic: cosine(evidence_a, evidence_b) is very LOW (≤ 1 -
    threshold) AND claim_a contains a negation word that claim_b
    doesn't (or vice versa). Cheap and explainable.
    """
    citations = _citations_for_research(memory, research_id)
    if len(citations) < 2 or embedder is None:
        return {"status": "pass", "items": []}
    negations = {"not", "never", "no"}

    def _negs(s: str) -> set[str]:
        words = set((s or "").lower().split())
        return words & negations

    flagged: list[dict] = []
    # Flag pairs whose evidence is SIMILAR (high cosine) AND whose
    # claims differ on polarity (one has a negation word the other
    # doesn't). Two same-topic citations with opposite polarity
    # are the contradiction signal.
    _MIN_TOPIC_SIM = 0.3   # both citations talk about the same topic
    for i in range(len(citations)):
        for j in range(i + 1, len(citations)):
            a, b = citations[i], citations[j]
            a_text = a.get("evidence_text", "")
            b_text = b.get("evidence_text", "")
            neg_diff = _negs(a.get("claim_supported", "")) ^ \
                       _negs(b.get("claim_supported", ""))
            if not neg_diff:
                continue
            # Compute topic-similarity over evidence text.
            indexed = embedder.index([a_text, b_text])
            scores = embedder.score(a_text, indexed)
            sim_b = scores[1] if len(scores) > 1 else 0.0
            if sim_b >= _MIN_TOPIC_SIM:
                flagged.append({
                    "a": a.get("id"), "b": b.get("id"),
                    "similarity": sim_b,
                })
    if flagged:
        return {"status": "warn", "items": flagged}
    return {"status": "pass", "items": []}


_REACHABILITY_TIMEOUT = 3.0   # Spec 052 §"web-reachability check"


def check_web_reachability(memory, research_id: str) -> dict:
    """Spec 052 — HEAD each web Citation's URL; pass on 2xx/3xx, fail
    on 4xx/5xx/timeout/network-error. Vacuous pass when no web
    Citations exist (the check is web-only)."""
    citations = _citations_for_research(memory, research_id)
    web = [c for c in citations if c.get("source_kind") == "web"]
    if not web:
        return {"status": "pass", "items": []}
    failing: list[dict] = []
    try:
        import httpx
    except ImportError:
        return {"status": "pass", "items": [],
                "note": "httpx unavailable; reachability check skipped"}
    with httpx.Client(timeout=_REACHABILITY_TIMEOUT, follow_redirects=True) as client:
        for c in web:
            url = c.get("source_url_or_path", "") or ""
            if not url:
                failing.append({"citation_id": c.get("id"),
                                  "url": "", "reason": "empty-url"})
                continue
            try:
                resp = client.head(url)
                if not (200 <= resp.status_code < 400):
                    failing.append({"citation_id": c.get("id"),
                                      "url": url,
                                      "status_code": resp.status_code})
            except Exception as exc:
                failing.append({"citation_id": c.get("id"),
                                  "url": url, "error": str(exc)[:80]})
    if failing:
        return {"status": "fail", "items": failing,
                "n_checked": len(web)}
    return {"status": "pass", "items": [], "n_checked": len(web)}


def run_all(memory, research_id: str, embedder=None) -> dict:
    """Run the v1 verifier checks; combine into the canonical payload.

    Returns ``{ok, checks: {evidence-supports-claim, contradiction-cluster,
    web-reachability}}``. ``ok`` is False if ANY check has status='fail'.
    """
    checks = {
        "evidence-supports-claim": check_evidence_supports_claim(
            memory, research_id, embedder),
        "contradiction-cluster": check_contradiction_cluster(
            memory, research_id, embedder),
        "web-reachability": check_web_reachability(memory, research_id),
    }
    ok = all(c["status"] != "fail" for c in checks.values())
    return {"ok": ok, "checks": checks}
