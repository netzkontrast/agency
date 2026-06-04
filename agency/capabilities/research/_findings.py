"""Helper utilities reused across research lead / specialist / verify.

Includes the deterministic substring-similarity helper for the verify
verb's evidence-supports-claim check (no LLM; same Spec 045 TF-IDF
machinery used for semantic matching when substring fails).
"""
from __future__ import annotations


def substring_supports(claim: str, evidence: str) -> bool:
    """True if claim is reasonably contained in evidence.

    Heuristic: take 50%+ of claim's content tokens, check they appear
    in evidence (lowercased). Generous enough that paraphrases pass;
    strict enough that unrelated text fails.
    """
    import re
    tokenize = lambda s: [t for t in re.findall(
        r"[a-zA-Z][a-zA-Z0-9]+", (s or "").lower()) if len(t) > 2]
    claim_toks = set(tokenize(claim))
    ev_toks = set(tokenize(evidence))
    if not claim_toks:
        return True   # empty claim is vacuously supported
    overlap = claim_toks & ev_toks
    # Ceiling division so a 3-token claim requires 2 shared (≥ 67%),
    # not 1 (≈ 33%). Floor would let weakly related evidence pass and
    # the semantic-score fallback never gets a chance to reject it.
    required = max(1, -(-len(claim_toks) // 2))
    return len(overlap) >= required


def semantic_score(query: str, text: str, embedder) -> float:
    """Cosine score between query and text via the engine's embedder.

    Used by prior-reflections + doc-corpus specialists for confidence
    AND by verify's evidence-supports-claim fallback.
    """
    if not query or not text or embedder is None:
        return 0.0
    indexed = embedder.index([text])
    scores = embedder.score(query, indexed)
    return float(scores[0]) if scores else 0.0
