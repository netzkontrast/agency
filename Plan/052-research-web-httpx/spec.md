---
spec_id: "052"
slug: research-web-httpx
status: draft
last_updated: 2026-06-03
owner: "@agency"
depends_on: [044]
informs: [045, 049]
affects:
  - pyproject.toml                              # add httpx already there; just add user-agent default
  - agency/capabilities/research/_web.py        # implement default WebSearchClient
  - agency/capabilities/research/_verify.py     # web-reachability check
  - agency/capabilities/research/_main.py       # walker may invoke web w/o injector
  - tests/test_research_web.py                  # NEW
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 052 — research.web default driver + web-reachability check

## Why

Spec 044 v1 ships the WebSearchClient Protocol but defers the
default driver to v2 — the `web` specialist returns "no driver"
when called without injection. This means the deepest research
depth (`deep` → 4 specialists incl. web) currently runs only 3
specialists.

httpx is already a runtime dep (used by Jules client). The same
httpx can drive a **simple** web specialist: hit a public search
endpoint, parse JSON. v1 candidates:

- **DuckDuckGo Instant Answer API** (no key, JSON, instant-zero-
  click answers). Limited recall but ZERO config.
- **SerpAPI free tier** (rate-limited, key-required). Better recall
  but key surface.
- **Tavily AI Research API** (designed for AI agents, JSON).

Recommendation: ship DuckDuckGo as the default zero-config baseline.
Other backends activate via `AGENCY_WEB_BACKEND=serpapi` +
`SERPAPI_KEY=…` env vars (same pattern as Spec 045's
`AGENCY_EMBEDDER`).

Plus: Spec 044's verifier ships 2 of 3 checks. The third —
**web-reachability** (HEAD URLs, verify 2xx) — also wants httpx.
Ship it here.

## Done When

### Default WebSearchClient implementations

- [ ] `agency/capabilities/research/_web.py::DuckDuckGoClient`:
  - Subclasses the WebSearchClient Protocol.
  - `name = "duckduckgo"`.
  - `search(query, k)` POSTs to `https://api.duckduckgo.com/?
    q=<query>&format=json&no_html=1`; parses RelatedTopics +
    AbstractText; returns up to k `{url, title, text}` dicts.
  - Timeout 10s; failure → empty list.
- [ ] `agency/capabilities/research/_web.py::resolve_web_search()`:
  - Reads `AGENCY_WEB_BACKEND` env var (default `"duckduckgo"`).
  - Returns the configured backend; unknown name → DuckDuckGo
    fallback (same pattern as Spec 045 resolve_embedder).
- [ ] Engine wiring: `Engine.__init__` defaults `web_search=
  resolve_web_search()` when not explicitly passed.

### Web-reachability check on verify

- [ ] `_verify.py::check_web_reachability(memory, research_id) ->
  dict`:
  - For each `source_kind="web"` Citation, HEAD the URL with 3s
    timeout.
  - Pass = 2xx OR 3xx response.
  - Fail = 4xx, 5xx, timeout, OR network error.
  - Cached per-call (so multiple verify runs in one session don't
    re-hit each URL).
- [ ] `run_all()` now reports 3 checks: evidence-supports-claim +
  contradiction-cluster + web-reachability.
- [ ] When NO `web` citations exist, reachability vacuously passes
  (status="pass", items=[]).

### Confidence adjustment

- [ ] When the web specialist records a Citation, the v1 hardcoded
  confidence 0.9 stays. But the verifier's reachability check now
  DEMOTES citations to confidence 0.2 (in place via supersede) when
  their URL is unreachable AT VERIFY TIME. Spec 044 §"confidence"
  line 113-117 already foresees this case.

### agency_doctor reporting

- [ ] `agency_doctor` payload's `web_backend` field reports the
  resolved backend name (matches Spec 045 `embedder` field pattern).

### Tests

- [ ] `tests/test_research_web.py`:
  - DuckDuckGoClient: mock httpx.Client.get to return canned JSON;
    assert search returns the parsed RelatedTopics.
  - resolve_web_search: env var honored; unknown backend falls back.
  - Reachability check: mock HEAD requests; pass on 2xx, fail on
    4xx/5xx/timeout.
  - Engine default: when no web_search injected, default is
    DuckDuckGoClient.

## Design

### Why DuckDuckGo as default

Zero-config wins. Users `pip install -e .` and `research.specialist
(role='web')` works immediately. Real-world recall is limited
(DuckDuckGo's Instant Answers cover only ~30% of queries), but
the test infrastructure runs without any external state.

For real research, users `export AGENCY_WEB_BACKEND=tavily &&
export TAVILY_API_KEY=…` and get production-grade recall.

### Why DEMOTE not REJECT unreachable citations

A citation might be unreachable at verify-time for transient reasons
(temporary 503, network glitch). Demoting to confidence 0.2 keeps
it in the report but flags the uncertainty. Spec 044 §"confidence"
already pinned 0.2 as the "URL unreachable" tier.

### Open Questions

1. **Should reachability re-check at publish time?** Verify might
   run 10 minutes before publish. v2 may add a recheck. v1 trusts
   verify.
2. **httpx async vs sync.** Verify is a transform; sync simpler.
   Use sync httpx.

## Files

- **Modify:**
  - `pyproject.toml` — confirm httpx already required (it is).
  - `agency/capabilities/research/_web.py` — add DuckDuckGoClient
    + resolve_web_search.
  - `agency/capabilities/research/_verify.py` — add check_web_
    reachability + extend run_all to include it.
  - `agency/engine.py` — default web_search via resolve_web_search.
  - `agency/engine.py::agency_doctor` — `web_backend` field.
- **Add:**
  - `tests/test_research_web.py`

## Cluster-coherence (Spec 047)

- C10 Research (it IS — closes the v1 scope-cut on web specialist).
- C04 Quality (verifier adds the third decidable check).

## Followup — Implementation Status (2026-06-03)

**Verdict:** Not started — drafted from deps-extension push +
Spec 044 v1 scope-cut.
