---
spec_id: "045"
slug: reflect-semantic-recall
status: draft
last_updated: 2026-06-02
owner: "@agency"
depends_on: [020, 023]
affects:
  - agency/capabilities/reflect.py             # add recall_semantic transform + helper
  - agency/capabilities/_embed.py              # NEW — pluggable embedder boundary
  - pyproject.toml                              # NEW optional extra [recall]
  - tests/test_reflect_recall_semantic.py
  - docs/vision/CORE.md                         # update: reflect now carries semantic recall
estimated_jules_sessions: 1
domain: meta
wave: 2
informs: [042, 043]
---

# Spec 045 — Semantic Recall on `reflect`

## Why

The audit (PR #17) identified **cross-session SEARCH** as agency's biggest
memory gap. Today the `reflect` capability owns three verbs:

- `reflect.note` — write a Reflection node (`act`).
- `reflect.recall` — list reflections newest-first, optionally by scope
  (`transform`).
- `reflect.search` — case-insensitive substring match over text
  (`transform`).

`recall` lists; `search` substring-matches. Neither finds "the time we
fixed the same problem six weeks ago" without the user remembering the
exact phrasing. The Superpowers `episodic-memory:remembering-conversations`
skill plugs exactly this gap — but does so by carrying its own MCP server
plus a vector-DB. Agency already has the bi-temporal graph (Spec 020); a
**graph-native semantic recall** is the smaller, more honest fit.

This spec adds **one transform verb** — `reflect.recall_semantic` — backed
by a pluggable embedder boundary (`agency/capabilities/_embed.py`,
following the `JulesClient`/`GitClient` driver pattern). The embedder is
an `optional-dependencies` extra so core stays light. Default embedder is
TF-IDF over the reflection corpus — no external deps, decidable, good
enough for ranking < 10K Reflections. A real-vector embedder (BGE,
sentence-transformers) is available via the `[recall]` extra for users
with serious corpora.

This unblocks two downstream specs (034 `document.render` and 035
`research.lead_research`) that need to surface "what we previously
learned about X" inside a walker phase.

## Done When

- [ ] `reflect.recall_semantic(query: str, k: int = 5, scope: str = "")`
  verb added (role `transform`, pure).
- [ ] Returns `{"results": [{"id": str, "score": float, "scope": str,
  "text": str, "vfrom": int}], "embedder": str}`. Results are sorted by
  score descending. `embedder` names the backend that ran (default
  `"tfidf"`).
- [ ] Default backend is **TF-IDF** (pure Python, scikit-free
  implementation in `_embed.py`) — works on the corpus + the query, no
  external deps. Indexes per-call (no persistence in v1); corpus < 10K
  Reflections completes in < 50ms.
- [ ] **TF-IDF backend parameters** (Wiegers — every default is named,
  not implicit):
  - Tokeniser: `re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())` —
    lowercase, alphanumeric runs starting with a letter, ≥ 2 chars.
  - Stop words: a fixed ~50-word English list (`the`, `a`, `is`, `of`,
    `to`, `and`, `in`, `that`, `it`, `for`, `on`, `with`, `as`, `at`,
    `by`, `this`, `but`, `be`, `are`, `or`, `from`, `was`, `if`,
    `not`, `you`, `we`, `they`, `i`, `an`, `have`, `has`, `had`,
    `do`, `does`, `did`, `can`, `will`, `would`, `should`, `could`,
    `there`, `here`, `their`, `our`, `its`, `his`, `her`, `my`,
    `your`) — defined in `_embed.py` as a module-level frozenset.
  - N-grams: unigrams only (v1). Bigrams considered for v2 if the
    unigram ranking proves too noisy.
  - IDF formula: `idf(t) = log((1 + N) / (1 + df(t))) + 1`
    (smoothed; matches scikit-learn default).
  - Norm: L2 normalisation of the TF-IDF vectors.
  - Similarity: cosine.
  - Min document frequency: 1 (no rare-term filtering — agency
    Reflections are short; rare terms matter).
  All params are constants in `_embed.py`; changing them is a Spec
  amendment, not a runtime configuration.
- [ ] Optional **vector backend** behind `pip install -e ".[recall]"`
  (adds `sentence-transformers` + a small model). Activated by
  `AGENCY_EMBEDDER=bge-small-en` env var; falls back to TF-IDF silently
  if the dep is missing.
- [ ] The boundary is INJECTABLE via the `Engine(..., embedder=…)` kwarg,
  same pattern as `jules_client` and `vcs_backend`. Tests inject a
  fixture embedder; production gets the resolved one (env-selected).
- [ ] `agency_doctor` reports `embedder: tfidf|bge-small-en|...` in its
  payload so users can confirm which backend is live.
- [ ] First-sentence brief slice on `recall_semantic` docstring is
  ≤ 120 chars (Spec 023 gate).
- [ ] No regression to existing `recall` or `search`. The four-verb shape
  (note · batch_note · recall · search · recall_semantic) ships as five.
- [ ] `tests/test_reflect_recall_semantic.py`:
  - Default TF-IDF returns sensible ranking for "fix MCP startup" against
    a fixture corpus that contains a paraphrase ("I solved the FastMCP
    bind issue").
  - Empty corpus returns `{results: [], embedder: "tfidf"}`.
  - Scope filter applies AFTER ranking (a query that semantically matches
    a `world` reflection AND a `technical` reflection, with
    `scope="technical"`, returns only the technical hit).
  - Injected stub embedder is used — proving the boundary works.
- [ ] `docs/vision/CORE.md` updated: the four verbs become five.

## Design

### Why TF-IDF as the default, not "no semantic recall"

The point of v1 isn't to ship state-of-the-art ranking — it's to **make
the surface available** so downstream specs can call it. TF-IDF over the
corpus + query is:

- decidable (same input → same output, no model versioning),
- zero-dep (pure Python in < 80 LOC),
- accurate enough for < 10K Reflections (the typical agency-session
  corpus),
- token-efficient on the wire (the result list is the top-k IDs +
  scores + truncated text, not the full corpus).

The vector backend is for users with larger corpora or harder queries.

### The embedder boundary

```python
# agency/capabilities/_embed.py
class Embedder(Protocol):
    name: str
    def index(self, corpus: list[str]) -> object: ...
    def score(self, query: str, indexed: object) -> list[float]: ...

class TfidfEmbedder:
    name = "tfidf"
    def index(self, corpus): ...     # pure-Python TF-IDF
    def score(self, query, indexed): ...

class BgeEmbedder:
    name = "bge-small-en"
    def __init__(self): ...           # lazy-loads sentence-transformers
    def index(self, corpus): ...
    def score(self, query, indexed): ...

def resolve_embedder() -> Embedder:
    """Spec 045 §"Embedder resolution": env > optional-dep > tfidf."""
    target = os.environ.get("AGENCY_EMBEDDER", "tfidf").strip()
    if target == "tfidf":
        return TfidfEmbedder()
    try:
        if target == "bge-small-en":
            return BgeEmbedder()
    except ImportError:
        # fall back silently — agency_doctor reports the fallback
        pass
    return TfidfEmbedder()
```

The engine wires `self.embedder = embedder or resolve_embedder()` and
exposes it on `ctx.embedder` (new injector slot). `recall_semantic` reads
`self.ctx.embedder`.

### The verb (sketch)

```python
@verb(role="transform")
def recall_semantic(self, query: str, k: int = 5, scope: str = "") -> dict:
    """Semantic top-k recall over Reflection nodes; backend-injectable."""
    rows = list(self.ctx.find("Reflection"))
    corpus = [r["text"] for r in rows]
    embedder = self.ctx.embedder
    indexed = embedder.index(corpus)
    scores = embedder.score(query, indexed)
    hits = sorted(
        ({**r, "score": s} for r, s in zip(rows, scores)),
        key=lambda h: h["score"],
        reverse=True,
    )
    if scope:
        hits = [h for h in hits if h.get("scope") == scope]
    out = [{"id": h["id"], "score": round(h["score"], 4),
            "scope": h["scope"], "text": h["text"][:200],
            "vfrom": h["vfrom"]} for h in hits[:k]]
    return {"results": out, "embedder": embedder.name}
```

Truncating `text` to 200 chars in the result is a Spec-023 token-budget
discipline — the caller can `recall_semantic` for the IDs then `recall`
or `search` for full text.

### What this is NOT (and the complementary `episodic-memory` adoption)

This spec is **not** a replacement for the Superpowers `episodic-memory`
plugin's `remembering-conversations` discipline. The two cover different
corpora and ship as complements:

| Surface | Corpus | Shape | Owner |
|---|---|---|---|
| `reflect.recall_semantic` (this spec) | agency `Reflection` nodes | transform verb in agency | THIS spec |
| `episodic-memory:search` / `read` | Claude Code conversation transcripts | external MCP server (TypeScript) | Superpowers ecosystem |

The right integration is **adopt episodic-memory via the future MCP-
client driver** (Spec 040 §"Open Question 3"). Reimplementing the
transcript-search corpus inside agency would duplicate well-tested
upstream work; reimplementing the Reflection-node corpus inside
episodic-memory would lose the bi-temporal graph semantics. Two corpora,
two surfaces — both available, the agent picks per question.

This spec is also:

- Not RAG — agency doesn't ship a retrieval-augmented-generation loop;
  this is plain top-k semantic ranking.
- Not persistent — the index is built per-call. Persistence is a v2
  question (Open Question 2).

## Files

- **Modify:**
  - `agency/capabilities/reflect.py` — add `recall_semantic` verb;
    declare the embedder injector slot in the OntologyExtension docs.
  - `agency/engine.py` — accept `embedder=…` kwarg; resolve default; set
    `self.registry.injectors["embedder"] = lambda: self.embedder`.
  - `pyproject.toml` — add `[project.optional-dependencies.recall] =
    ["sentence-transformers>=2.0"]`.
  - `docs/vision/CORE.md` — five-verb reflect surface.
- **Add:**
  - `agency/capabilities/_embed.py` — embedder boundary + TF-IDF +
    BGE backends + `resolve_embedder()`.
  - `tests/test_reflect_recall_semantic.py`.

## Open Questions

1. **TF-IDF over the whole Reflection corpus on every call** is fine at
   < 10K. At 100K it isn't. Should the engine maintain an incremental
   index in the bi-temporal graph (a Reflection-vector node type)?
   v2 question.
2. **Persistent embeddings** — for vector backends, re-embedding the
   corpus every call is wasted compute. A cache keyed by Reflection ID +
   embedder name solves it; the cache invalidates when a Reflection's
   vfrom changes. Defer to v2 unless real users hit it.
3. **Cross-Intent search.** Today every Reflection SERVES one Intent
   (provenance); `recall_semantic` ignores Intent boundaries. Should it
   default to "this Intent's reflections" with an `all_intents=True`
   override? v1 says no — recall is global; the caller filters via
   `scope`.
4. **Embedder name as an enum?** The `embedder` field in the return
   payload is a string today. If we ever ship 4+ backends, an enum on
   the result makes typo-resistant agent-side branching easier. Trivial
   to add; lean no for v1.

## Evidence

- Existing `reflect.py` surface (`note`, `batch_note`, `recall`,
  `search`) — the four verbs that ship today.
- `episodic-memory:remembering-conversations` skill — the cross-session
  recovery surface this spec graph-natively reimplements.
- `EXTENSION-PLAN.md` line "reflect+ (semantic recall) — vector-ranked
  recall over Reflection" — pre-existing pointer.
- Spec 020 (central graph DB) — the substrate that makes the corpus
  durable cross-session.
- Spec 023 (adaptive disclosure) — the 200-char text-truncation rule.
- The "Sieben Findings" audit in PR #17 — F-cluster on memory.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Not started — spec drafted; existing `recall`/`search`
remain the only retrieval surface.

### Done
- The substrate (`Reflection` node, scope enum, OBSERVED_DURING edge,
  bi-temporal graph) ships today; this spec only adds a transform verb
  + a boundary client.

### Still to implement
- `_embed.py` module + the two backends.
- Engine kwarg + injector slot.
- The verb itself + tests.
- pyproject `[recall]` extra.
- `agency_doctor` payload field.
- CORE.md update.

### Refinement needed
- Open Question 1 (incremental index) blocks scaling but not v1
  shipping. Mark as v2.
- Open Question 3 (cross-Intent default) is small but needs a one-line
  policy call before v1.
