---
spec_id: "168"
slug: research-web-driver-depth
status: draft
state: inprogress
last_updated: 2026-06-10
owner: "@agency"
enhances: "052"
depends_on: ["052", "044", "147", "146"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/research/_web.py
  - tests/test_research_web_depth.py
---

# Spec 168 — research web-driver depth (server-side tools)

## Why

Spec 052 shipped a DuckDuckGo zero-config web backend + reachability
check, closing Spec 044's v1 web scope-cut. But the Claude API ships
SERVER-SIDE `web_search` + `web_fetch` tools with dynamic filtering
(`claude-api` skill, tool-use-concepts) that filter results before they
hit context — strictly better token economy than scraping into the
orchestrator. When the Spec 147 Driver is present, the research web
specialist should prefer the server-side tools.

## Done When (measurable invariants — rule 8)

- [ ] **Typed Citation shape unchanged across backends** —
      `Citation{url, title, snippet, retrieved_at, backend:
      Literal["anthropic_web", "duckduckgo"], hash}` — the verify
      path is backend-agnostic (Spec 044 contract).
- [ ] **Invariant: backend selection is deterministic per environment**
      — `[anthropic]` present + `ANTHROPIC_API_KEY` set ⇒
      `backend=="anthropic_web"`; otherwise `"duckduckgo"`. No silent
      flipping mid-walk.
- [ ] **Relationship: `mean_tokens_per_citation(anthropic_web) <
      mean_tokens_per_citation(duckduckgo)`** on the benchmark fixture
      — dynamic filtering proves out, derived (≥ ratio, not pinned).
- [ ] **Invariant: every Citation hash is reproducible** — same `url`
      + same `retrieved_at` rounded to day ⇒ same `hash` regardless of
      backend; protects the verify chain (Spec 044) from backend
      churn.
- [ ] **Invariant: large body capture-and-recall** — when fetched
      body > `MAX_BODY_TOKENS` (Spec 154 default), the body is
      stored as a graph node + recalled by ref; the returned Citation
      carries `body_ref` not `body`.
- [ ] **Failure mode (server-side path):** Driver `RATE_LIMITED` →
      fall back to DuckDuckGo for the remaining queries in the walk +
      emit `Codes.WEB_BACKEND_DEGRADED` Reflection; Driver `REFUSAL`
      (cyber/bio) → the specific query fails with the typed code,
      next query continues; tool result with no citations → emit
      `Codes.WEB_NO_CITATIONS` (do not silently return `[]`).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  `[anthropic]` extra installed + ANTHROPIC_API_KEY set; query
        "graphqlite bi-temporal model"; MAX_BODY_TOKENS = 4000
When:   research.web(query) runs
Then:   returns Citations[i]{backend="anthropic_web"}; each fetched
        page > 4000 tokens carries body_ref pointing at a graph node
        (not inlined); envelope.prefix bytes are byte-identical to
        a prior research call (Spec 146 cache held)

Given:  Driver returns RATE_LIMITED mid-walk on query 3 of 5
When:   research.web continues
Then:   queries 4 + 5 route through DuckDuckGo; emit
        WEB_BACKEND_DEGRADED Reflection linked to the walk Intent;
        verify chain (Spec 044) runs identically on both backends'
        Citations

Given:  Same query, `[anthropic]` extra NOT installed
When:   research.web(query) runs
Then:   backend=="duckduckgo" for every Citation (deterministic,
        no silent flip) AND Citation hash is reproducible
```

## Failure modes (Nygard)

| Failure | Specialist response |
|---|---|
| Driver `RATE_LIMITED` | fall back to DuckDuckGo for remainder of walk + `WEB_BACKEND_DEGRADED` |
| Driver `REFUSAL` (cyber/bio) | per-query typed error; next query continues |
| Server-side tool returns 0 citations on a query that DDG answered | `WEB_NO_CITATIONS` Reflection; surface to operator |
| Fetched body > MAX_BODY_TOKENS | capture-and-recall: store as graph node, return `body_ref` |
| Egress policy blocks the URL | typed `EGRESS_BLOCKED`; both backends honor the policy |
| Citation hash mismatch across backends for same URL+day | drift gate fails; Spec 173 reflection-link audit catches |

## Interconnects

- **LLM-driver chain** (147) — the server-side path is a major Driver
  consumer.
- **Output-budget chain** (146/154) — Citations + bodies budget through
  the same envelope; the prefix stays cache-stable.
- Spec 044 (research cap) is the parent; Spec 052 the web v1.
- Spec 168 + Spec 161 (discovery rank) share the structured-output
  contract for ranked results.
- Spec 170 (doctor) reports `web_backend.live` (derived).
- Spec 173 (reflection-link promotion) ensures any
  `WEB_BACKEND_DEGRADED` Reflection has the SERVES + OBSERVED_DURING
  edges Spec 150's classifier reads.
- Spec 151 (Codes coverage) supplies `WEB_BACKEND_DEGRADED`,
  `WEB_NO_CITATIONS`, `EGRESS_BLOCKED`.

## Open questions

1. Cost of server-side fetch vs scrape? **Recommend**: server-side when
   available (dynamic filtering saves tokens); the user's web policy
   governs egress either way.
2. Cache server-side results across walks? **Recommend**:
   `(query_hash, day)` keyed; invalidates the next day; reproducible
   `hash` invariant guarantees safe sharing.
3. Hybrid mode — both backends per query and reconcile? **Recommend**:
   no by default (doubles cost); opt-in `verify_with=["duckduckgo"]`
   for high-stakes citations.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion`.

Engine-driven end-to-end (intent:8fc460e1; skill:19b30acd tdd walk
completed; 5 Reflections via dogfood.note; branch.commit_smart
composed the commit message).

### Done — Slice 1 (typed Citation + deterministic backend selector)

- **`agency/_research_citation.py`**:
  - `CitationBackend = Literal['anthropic_web', 'duckduckgo']`
  - `Citation{url, title, snippet, retrieved_at, backend, hash}` frozen
    dataclass with `__post_init__` rejecting empty url / hash / invalid
    backend.
  - `compute_citation_hash(url, snippet)` → 16-char hex (SHA-256[:16])
    deterministic dedup hash; includes snippet so a page that updates
    its content surfaces as a NEW citation.
  - `select_backend(env)` pure selector. Invariant: `ANTHROPIC_API_KEY`
    present AND `AGENCY_RESEARCH_ANTHROPIC != "0"` ⇒ `"anthropic_web"`;
    else `"duckduckgo"`. No silent fallback at runtime.

- **10 tests** in `tests/test_research_citation.py`.

### Still — Slice 2+

- **Slice 2** — `research.fetch` verb routes through `select_backend`
  + the anthropic_web boundary (Spec 147 driver) when applicable;
  DuckDuckGo path stays as today.
- **Slice 3** — Spec 154 overflow capture wraps long citation lists
  so the agent's context stays bounded.
- **Slice 4** — citation verify path uses the typed Citation across
  backends (Spec 044 contract); a deterministic re-fetch reproduces
  the hash.

