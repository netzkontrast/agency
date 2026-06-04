"""Embedder boundary — pluggable semantic-ranking backend.

Spec 045 §"The embedder boundary": a Protocol-typed boundary with TWO
shipped backends:

  - ``TfidfEmbedder`` — pure-Python TF-IDF (default, zero-dep).
  - ``BgeEmbedder`` — sentence-transformers BGE small (optional, via
    ``[recall]`` extra).

``resolve_embedder()`` picks per the ``AGENCY_EMBEDDER`` env var;
unknown targets and missing optional deps fall back to TF-IDF silently
(``agency_doctor`` reports the running backend so the fallback is
visible).
"""
from __future__ import annotations

import math
import os
import re
from typing import Protocol


# --------------------------------------------------------------------------
# Protocol — the boundary every backend implements.
# --------------------------------------------------------------------------


class Embedder(Protocol):
    """Pluggable semantic-ranker boundary.

    ``index(corpus)`` returns a backend-opaque object that ``score(query,
    indexed)`` consumes; the orchestrator never inspects ``indexed``.
    Backends are STATELESS between calls — index per request (Spec 045
    Open Question 2 defers caching to v2).
    """

    name: str

    def index(self, corpus: list[str]) -> object: ...
    def score(self, query: str, indexed: object) -> list[float]: ...


# --------------------------------------------------------------------------
# TF-IDF (default).
#
# All constants here are SPEC 045 §"TF-IDF backend parameters" pinned —
# changing them is a spec amendment, not a runtime configuration.
# --------------------------------------------------------------------------


_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]+")


# Fixed ~50-word English stoplist (Spec 045 line 69–75).
_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "is", "of", "to", "and", "in", "that", "it", "for",
    "on", "with", "as", "at", "by", "this", "but", "be", "are", "or",
    "from", "was", "if", "not", "you", "we", "they", "i", "an", "have",
    "has", "had", "do", "does", "did", "can", "will", "would", "should",
    "could", "there", "here", "their", "our", "its", "his", "her", "my",
    "your",
})


def _tokenise(text: str) -> list[str]:
    """Lowercase alphanumeric runs ≥ 2 chars, stop-words removed."""
    return [t for t in (m.group(0).lower() for m in _TOKEN_RE.finditer(text))
            if t not in _STOPWORDS]


class TfidfEmbedder:
    """Pure-Python TF-IDF cosine ranker.

    Smoothed IDF (matches scikit-learn): ``idf(t) = ln((1+N) / (1+df(t))) + 1``.
    L2-normalised vectors; cosine similarity; min_df = 1 (rare terms matter
    on short Reflections).
    """

    name = "tfidf"

    def index(self, corpus: list[str]) -> dict:
        """Build per-document term vectors + the IDF map."""
        docs = [_tokenise(text or "") for text in corpus]
        n_docs = len(docs)
        # Document frequency per term.
        df: dict[str, int] = {}
        for tokens in docs:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        # Smoothed IDF (scikit-learn default).
        idf = {
            term: math.log((1 + n_docs) / (1 + dfreq)) + 1.0
            for term, dfreq in df.items()
        }
        # Per-doc TF-IDF vectors, L2-normalised.
        vectors: list[dict[str, float]] = []
        for tokens in docs:
            if not tokens:
                vectors.append({})
                continue
            tf: dict[str, float] = {}
            for term in tokens:
                tf[term] = tf.get(term, 0.0) + 1.0
            vec = {term: tf[term] * idf[term] for term in tf}
            norm = math.sqrt(sum(v * v for v in vec.values()))
            if norm > 0:
                vec = {term: val / norm for term, val in vec.items()}
            vectors.append(vec)
        return {"vectors": vectors, "idf": idf, "n_docs": n_docs}

    def score(self, query: str, indexed: dict) -> list[float]:
        """Cosine similarity of the L2-normalised query vector against each
        document vector. Returns a score per document; empty query → all
        zeros."""
        idf = indexed["idf"]
        vectors = indexed["vectors"]
        q_tokens = _tokenise(query or "")
        if not q_tokens:
            return [0.0] * len(vectors)
        # TF-IDF for the query — only terms present in the corpus IDF
        # contribute (out-of-vocabulary terms get 0 weight).
        q_tf: dict[str, float] = {}
        for term in q_tokens:
            if term in idf:
                q_tf[term] = q_tf.get(term, 0.0) + 1.0
        if not q_tf:
            return [0.0] * len(vectors)
        q_vec = {term: q_tf[term] * idf[term] for term in q_tf}
        norm = math.sqrt(sum(v * v for v in q_vec.values()))
        if norm > 0:
            q_vec = {term: val / norm for term, val in q_vec.items()}
        # Cosine = dot product (both are L2-normalised already).
        scores: list[float] = []
        for vec in vectors:
            if not vec:
                scores.append(0.0)
                continue
            scores.append(sum(q_vec[t] * vec.get(t, 0.0)
                              for t in q_vec if t in vec))
        return scores


# --------------------------------------------------------------------------
# BGE (optional, behind [recall] extra).
# --------------------------------------------------------------------------


class BgeEmbedder:
    """sentence-transformers BGE-small-en backend (optional).

    Loaded lazily so the import cost is only paid when the user opts in
    via ``AGENCY_EMBEDDER=bge-small-en`` + ``pip install -e .[recall]``.
    """

    name = "bge-small-en"

    def __init__(self) -> None:
        # Lazy import — raises ImportError if [recall] extra missing.
        # resolve_embedder() catches the ImportError and falls back to
        # TF-IDF silently.
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    def index(self, corpus: list[str]) -> object:
        # Returns a tensor; downstream `score` runs cosine over it.
        return self._model.encode(corpus or [""], normalize_embeddings=True)

    def score(self, query: str, indexed) -> list[float]:
        if query is None or not query.strip():
            return [0.0] * len(indexed)
        q_vec = self._model.encode([query], normalize_embeddings=True)[0]
        # Both already L2-normalised → cosine = dot product.
        return [float(sum(a * b for a, b in zip(q_vec, row))) for row in indexed]


# --------------------------------------------------------------------------
# Resolution (env > optional-dep > tfidf default).
# --------------------------------------------------------------------------


# Single source of truth for "what backends does this version know?".
# agency_doctor consults this when deciding whether AGENCY_EMBEDDER's
# request was a typo (suggest valid names) vs. a known target with a
# missing optional dep (suggest pip install -e .[recall]).
KNOWN_EMBEDDERS: frozenset[str] = frozenset({"tfidf", "bge-small-en"})


def resolve_embedder() -> Embedder:
    """Spec 045 §"Embedder resolution": env > optional-dep > tfidf.

    Unknown ``AGENCY_EMBEDDER`` targets fall back to TF-IDF silently;
    ``agency_doctor`` reports the running backend so the fallback is
    visible to the user.
    """
    target = (os.environ.get("AGENCY_EMBEDDER", "tfidf") or "tfidf").strip()
    if target == "tfidf":
        return TfidfEmbedder()
    if target == "bge-small-en":
        try:
            return BgeEmbedder()
        except Exception:    # noqa: BLE001 — any model-load failure
            # ImportError covers missing sentence-transformers; broader
            # Exception catches model-not-cached / network errors /
            # HuggingFace 4xx in offline or restricted environments so
            # opt-in to the optional backend never crashes engine
            # startup or agency-doctor. The TF-IDF fallback is the
            # documented degradation path.
            return TfidfEmbedder()
    # Unknown target → safe default.
    return TfidfEmbedder()
