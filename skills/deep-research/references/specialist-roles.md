# Specialist roles — Spec 044 v1

Four roles ship. Each is a single bounded sub-search that records
Citation nodes with `(source_kind, source_url_or_path, evidence_text,
confidence, claim_supported)`. Confidence rules per Spec 044 §"confidence
computation rule" — every floating-point field has a defined origin.

## `codebase`

**What it does.** `os.walk` over `search_root` (default `agency/`),
read every `.py` file, grep for `query` substring. Record one
Citation per hit (cap default 5).

**Confidence: 1.0.** Codebase citations are deterministic — file path
+ line number + literal source line. No interpretation.

**When it wins.** "How is X implemented?" "Where is Y referenced?"

## `prior-reflections`

**What it does.** Calls `reflect.recall_semantic(query, k)` via the
registry (so the embedder injector is honoured); records the top-k
Reflection hits as Citation nodes.

**Confidence: ranker score.** TF-IDF cosine or BGE cosine, whichever
backend is live. The embedder name is reported in `agency_doctor`.

**When it wins.** "What have we learned about X?" "Any past
observations on Y?"

## `doc-corpus`

**What it does.** Walks `docs_root` (default `docs/`) for `.md`,
`.txt`, `.rst`. Substring match first; semantic backup via embedder
when substring fails (≥ 0.3 cosine).

**Confidence.** Substring match = 1.0. Semantic match = the cosine
score. v1 doesn't double-count — first hit per file wins.

**When it wins.** "Is X documented?" "What does the vision doc say
about Y?"

## `web` (v1: error if no driver injected)

**What it does (when wired).** `engine.web_search.search(query, k)`;
records returned `{url, text|snippet}` as Citation nodes.

**Confidence: 0.9.** Web baseline — URL resolves AND text is the page
content. v2's reachability check re-verifies at publish time; v1
trusts the search result.

**When it would win (after a driver lands).** "What's the SOTA on
X?" "Is there a public spec for Y?"

**v1 fallback.** Without a driver injected, the verb returns
`{citations: 0, summary: "web specialist requires
Engine(web_search=…) — v1 has no default driver"}`. NOT an
exception; the orchestrator can fan out to the other specialists
and treat the web result as missing.

## How the orchestrator picks roles

`research.lead`'s `_lead.plan()` defaults:

```
brief    → [codebase]
standard → [codebase, prior-reflections]
deep     → [codebase, prior-reflections, doc-corpus, web]
```

If the question contains `http` or `https`, web is added regardless
of depth.

The orchestrator MAY override the plan by calling `research.specialist`
with any role; the plan is a recommendation, not a contract.
